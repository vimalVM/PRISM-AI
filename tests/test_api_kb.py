"""API tests for Knowledge Base management and clearance-filtered search endpoints.

Tests /api/kb/documents CRUD, RBAC admin enforcement, and search permissions.
"""

from pathlib import Path
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.core.config import get_settings
from backend.core.db import User, get_session_factory
from backend.core.rbac import Clearance, Role
from backend.core.security import SESSION_COOKIE_NAME, create_session, hash_password
from backend.main import create_app
from rag.ingest import set_embedding_hook


def mock_embedding_fn(texts):
    import hashlib
    vectors = []
    for t in texts:
        h = hashlib.sha256(t.encode()).digest()
        vectors.append([(b / 255.0) for b in (h * 32)])
    return vectors


@pytest.fixture
def kb_api_client(tmp_path, monkeypatch):
    set_embedding_hook(mock_embedding_fn)
    app = create_app()
    client = TestClient(app)

    suffix = uuid.uuid4().hex[:8]
    factory = get_session_factory()
    with factory() as db:
        admin_user = User(
            username=f"admin_kb_{suffix}",
            password_hash=hash_password("AdminPass123!"),
            role="admin",
            clearance=Clearance.RESTRICTED.value,
            active=True,
        )
        eng_user = User(
            username=f"eng_kb_{suffix}",
            password_hash=hash_password("EngPass123!"),
            role="engineer",
            clearance=Clearance.INTERNAL.value,
            active=True,
        )
        db.add_all([admin_user, eng_user])
        db.commit()

        _, admin_cookie = create_session(db, admin_user.id)
        _, eng_cookie = create_session(db, eng_user.id)

    # Set up incoming test directory
    incoming = tmp_path / "incoming"
    incoming.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(get_settings(), "ALLOWED_INPUT_DIRS", str(incoming))

    test_file = incoming / "safety_test.txt"
    test_file.write_text("Facility safety protocols: Eye wash stations must be tested weekly.")

    yield client, admin_cookie, eng_cookie, test_file
    set_embedding_hook(None)


def test_kb_ingest_admin_only(kb_api_client):
    client, admin_cookie, eng_cookie, test_file = kb_api_client
    headers = {"X-Requested-With": "XMLHttpRequest"}

    # 1. Engineer attempt -> 403 Forbidden
    eng_resp = client.post(
        "/api/kb/documents",
        json={
            "doc_id": "SOP-TEST-INGEST",
            "file_path": str(test_file),
            "classification": 1,
            "version": 1,
        },
        headers=headers,
        cookies={SESSION_COOKIE_NAME: eng_cookie},
    )
    assert eng_resp.status_code == 403

    # 2. Admin attempt -> 201 Created
    admin_resp = client.post(
        "/api/kb/documents",
        json={
            "doc_id": "SOP-TEST-INGEST",
            "file_path": str(test_file),
            "classification": 1,
            "version": 1,
        },
        headers=headers,
        cookies={SESSION_COOKIE_NAME: admin_cookie},
    )
    assert admin_resp.status_code == 201
    assert admin_resp.json()["doc_id"] == "SOP-TEST-INGEST"


def test_kb_list_and_search(kb_api_client):
    client, admin_cookie, eng_cookie, test_file = kb_api_client
    headers = {"X-Requested-With": "XMLHttpRequest"}

    # Ingest document as admin first
    client.post(
        "/api/kb/documents",
        json={
            "doc_id": "SOP-SEARCH-TEST",
            "file_path": str(test_file),
            "classification": 1,
            "version": 1,
        },
        headers=headers,
        cookies={SESSION_COOKIE_NAME: admin_cookie},
    )

    # List documents as engineer
    list_resp = client.get(
        "/api/kb/documents",
        headers=headers,
        cookies={SESSION_COOKIE_NAME: eng_cookie},
    )
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert any(d["doc_id"] == "SOP-SEARCH-TEST" for d in docs)

    # Search as engineer (classification <= 1)
    search_resp = client.post(
        "/api/kb/search",
        json={"query": "eye wash station weekly"},
        headers=headers,
        cookies={SESSION_COOKIE_NAME: eng_cookie},
    )
    assert search_resp.status_code == 200
    res_data = search_resp.json()
    assert res_data["total"] > 0
    assert any(c["doc_id"] == "SOP-SEARCH-TEST" for c in res_data["chunks"])
