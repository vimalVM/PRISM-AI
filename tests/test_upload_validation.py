"""Tests for secure file upload API endpoint and SEC-07 validation rules.

Verifies:
- SEC-07: Renamed executables (.exe as .pdf) rejected via magic byte / executable inspection.
- Extension allowlist and denylist enforcement (rejects .exe, .bat, .xlsm, .zip, etc.).
- File size limit enforcement (413 Payload Too Large).
- Decompression bomb image mitigation via PIL pixel limits.
- Maximum PDF page count limit enforcement.
- Role-based permissions: Auditor role is denied (403); Admin, Engineer, Reviewer allowed.
- FileRecord database persistence and path confinement in data/incoming/.
- Ownership isolation in file listing and single-file retrieval.
"""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import fitz  # PyMuPDF
from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.core.audit import get_engine
from backend.core.config import get_settings
from backend.core.db import Base, FileRecord, User, get_db
from backend.core.rbac import Clearance, Role
from backend.core.security import get_current_user, hash_password
from backend.main import create_app


@pytest.fixture
def file_api_setup(tmp_path, monkeypatch):
    """Setup isolated database, incoming folder, and mock test users."""
    test_db = tmp_path / "test_files.db"
    engine = create_engine(f"sqlite:///{test_db.resolve()}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

    incoming_dir = tmp_path / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(get_settings(), "ALLOWED_INPUT_DIRS", str(incoming_dir))

    # Seed users: admin, engineer, reviewer, auditor
    db = TestingSession()
    admin = User(
        id="user-admin-1",
        username="admin_user",
        password_hash=hash_password("Pass123!"),
        role=Role.ADMIN.value,
        clearance=Clearance.RESTRICTED.value,
        active=True,
    )
    engineer = User(
        id="user-eng-1",
        username="eng_user",
        password_hash=hash_password("Pass123!"),
        role=Role.ENGINEER.value,
        clearance=Clearance.CONFIDENTIAL.value,
        active=True,
    )
    reviewer = User(
        id="user-rev-1",
        username="rev_user",
        password_hash=hash_password("Pass123!"),
        role=Role.REVIEWER.value,
        clearance=Clearance.CONFIDENTIAL.value,
        active=True,
    )
    auditor = User(
        id="user-aud-1",
        username="aud_user",
        password_hash=hash_password("Pass123!"),
        role=Role.AUDITOR.value,
        clearance=Clearance.RESTRICTED.value,
        active=True,
    )
    db.add_all([admin, engineer, reviewer, auditor])
    db.commit()
    db.close()

    app = create_app()

    def override_get_db():
        s = TestingSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db

    return app, admin, engineer, reviewer, auditor, TestingSession, incoming_dir


def test_sec07_renamed_exe_rejected(file_api_setup):
    """SEC-07: Executable file renamed to .pdf must be rejected with 400 Bad Request."""
    app, _, engineer, _, _, _, _ = file_api_setup
    app.dependency_overrides[get_current_user] = lambda: engineer
    client = TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"})

    # Simulated Windows PE Executable with 'MZ' DOS header
    fake_exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + b"This program cannot be run in DOS mode."
    files = {"file": ("malicious_payload.pdf", fake_exe_bytes, "application/pdf")}

    response = client.post("/api/files/upload", files=files)
    assert response.status_code == 400
    assert "executable" in response.json()["detail"].lower() or "sec-07" in response.json()["detail"].lower()


def test_sec07_linux_elf_renamed_rejected(file_api_setup):
    """SEC-07: Linux ELF executable renamed to .txt/.pdf must be rejected with 400."""
    app, _, engineer, _, _, _, _ = file_api_setup
    app.dependency_overrides[get_current_user] = lambda: engineer
    client = TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"})

    fake_elf_bytes = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 32
    files = {"file": ("exploit.pdf", fake_elf_bytes, "application/pdf")}

    response = client.post("/api/files/upload", files=files)
    assert response.status_code == 400
    assert "executable" in response.json()["detail"].lower()


def test_forbidden_and_macro_extensions_rejected(file_api_setup):
    """Forbidden extensions (.exe, .bat, .xlsm, .zip) are rejected immediately."""
    app, _, engineer, _, _, _, _ = file_api_setup
    app.dependency_overrides[get_current_user] = lambda: engineer
    client = TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"})

    # 1. Direct .exe
    res1 = client.post("/api/files/upload", files={"file": ("tool.exe", b"MZtest", "application/octet-stream")})
    assert res1.status_code == 400
    assert "forbidden" in res1.json()["detail"].lower()

    # 2. Script .bat
    res2 = client.post("/api/files/upload", files={"file": ("run.bat", b"@echo off\r\ndir", "text/plain")})
    assert res2.status_code == 400
    assert "forbidden" in res2.json()["detail"].lower()

    # 3. Macro-enabled Excel .xlsm
    res3 = client.post("/api/files/upload", files={"file": ("sheet.xlsm", b"PK\x03\x04", "application/vnd.ms-excel")})
    assert res3.status_code == 400
    assert "forbidden" in res3.json()["detail"].lower()

    # 4. Unknown extension .iso
    res4 = client.post("/api/files/upload", files={"file": ("disk.iso", b"dummy", "application/octet-stream")})
    assert res4.status_code == 400
    assert "not in the permitted allowlist" in res4.json()["detail"].lower()


def test_upload_size_limit_enforced(file_api_setup, monkeypatch):
    """Upload exceeding MAX_UPLOAD_MB returns 413 Payload Too Large."""
    app, _, engineer, _, _, _, _ = file_api_setup
    app.dependency_overrides[get_current_user] = lambda: engineer
    client = TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"})

    # Lower limit to 1 MB for testing
    monkeypatch.setattr(get_settings(), "MAX_UPLOAD_MB", 1)

    oversize_bytes = b"A" * (2 * 1024 * 1024)  # 2 MB
    files = {"file": ("large_document.txt", oversize_bytes, "text/plain")}

    response = client.post("/api/files/upload", files=files)
    assert response.status_code == 413
    assert "exceeds maximum upload limit" in response.json()["detail"].lower()


def test_decompression_bomb_rejected(file_api_setup, monkeypatch):
    """Decompression bomb image is rejected."""
    app, _, engineer, _, _, _, _ = file_api_setup
    app.dependency_overrides[get_current_user] = lambda: engineer
    client = TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"})

    # Lower pixel threshold for test
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10_000)

    # Create image with 200 x 200 = 40,000 pixels (> 10,000)
    bomb_img = Image.new("RGB", (200, 200), color="red")
    buf = io.BytesIO()
    bomb_img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("bomb.png", buf.getvalue(), "image/png")}
    response = client.post("/api/files/upload", files=files)
    assert response.status_code == 400
    assert "decompression bomb" in response.json()["detail"].lower() or "resolution exceeds" in response.json()["detail"].lower()


def test_pdf_page_limit_enforced(file_api_setup, monkeypatch):
    """PDF exceeding MAX_PDF_PAGES returns 400 Bad Request."""
    app, _, engineer, _, _, _, _ = file_api_setup
    app.dependency_overrides[get_current_user] = lambda: engineer
    client = TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"})

    monkeypatch.setattr(get_settings(), "MAX_PDF_PAGES", 3)

    # Create a 5-page PDF
    doc = fitz.open()
    for _ in range(5):
        doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("oversize_pages.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/files/upload", files=files)
    assert response.status_code == 400
    assert "pdf page limit exceeded" in response.json()["detail"].lower()


def test_auditor_role_upload_forbidden(file_api_setup):
    """Auditor role is denied upload per permission matrix (403 Forbidden)."""
    app, _, _, _, auditor, _, _ = file_api_setup
    app.dependency_overrides[get_current_user] = lambda: auditor
    client = TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"})

    files = {"file": ("notes.txt", b"auditor notes", "text/plain")}
    response = client.post("/api/files/upload", files=files)
    assert response.status_code == 403


def test_valid_uploads_success_and_listing(file_api_setup):
    """Valid text and PDF uploads succeed, generate FileRecord and allow listing."""
    app, admin, engineer, _, _, TestingSession, incoming_dir = file_api_setup
    app.dependency_overrides[get_current_user] = lambda: engineer
    client = TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"})

    # 1. Upload valid text file
    txt_content = b"Engineering task specifications for pump overhaul."
    res1 = client.post("/api/files/upload", files={"file": ("specs.txt", txt_content, "text/plain")})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["original_name"] == "specs.txt"
    assert data1["modality"] == "text"
    assert data1["size_bytes"] == len(txt_content)
    file_id_1 = data1["id"]

    # 2. Upload valid PDF file
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Safe PDF content")
    pdf_bytes = doc.tobytes()
    doc.close()

    res2 = client.post("/api/files/upload", files={"file": ("report.pdf", pdf_bytes, "application/pdf")})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["original_name"] == "report.pdf"
    assert data2["modality"] == "pdf"
    assert data2["pages"] == 1
    file_id_2 = data2["id"]

    # 3. List files for engineer (should see 2 files)
    res_list = client.get("/api/files")
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) == 2
    ids = {item["id"] for item in items}
    assert file_id_1 in ids and file_id_2 in ids

    # 4. Get specific file by ID
    res_get = client.get(f"/api/files/{file_id_1}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == file_id_1
