"""API tests for artifacts endpoints (/api/artifacts).

Tests listing, metadata retrieval with validation checklist,
and scoped downloads enforcing SEC-19 (auditor 403) and SEC-20 (unassigned reviewer 403).
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.core.config import get_settings
from backend.core.db import Artifact, Task, User, get_session_factory
from backend.core.security import SESSION_COOKIE_NAME, create_session, hash_password
from backend.main import create_app


@pytest.fixture
def api_test_data(tmp_path):
    """Set up database with admin, engineer1, engineer2, reviewer1, reviewer2, auditor, and sample artifacts."""
    settings = get_settings()
    outputs_dir = Path(settings.DATA_DIR) / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy artifact files
    art1_file = outputs_dir / "deliverable_1.docx"
    art1_file.write_text("dummy docx content")

    art2_file = outputs_dir / "deliverable_2.xlsx"
    art2_file.write_text("dummy xlsx content")

    import uuid
    suffix = uuid.uuid4().hex[:8]

    factory = get_session_factory()
    with factory() as db:
        # Create users
        admin = User(
            id=f"admin_{suffix}",
            username=f"admin_{suffix}",
            password_hash=hash_password("AdminPass123!"),
            role="admin",
            clearance=3,
            active=True,
        )
        eng1 = User(
            id=f"eng1_{suffix}",
            username=f"eng1_{suffix}",
            password_hash=hash_password("EngPass123!"),
            role="engineer",
            clearance=2,
            active=True,
        )
        eng2 = User(
            id=f"eng2_{suffix}",
            username=f"eng2_{suffix}",
            password_hash=hash_password("EngPass123!"),
            role="engineer",
            clearance=2,
            active=True,
        )
        rev1 = User(
            id=f"rev1_{suffix}",
            username=f"rev1_{suffix}",
            password_hash=hash_password("RevPass123!"),
            role="reviewer",
            clearance=2,
            active=True,
        )
        rev2 = User(
            id=f"rev2_{suffix}",
            username=f"rev2_{suffix}",
            password_hash=hash_password("RevPass123!"),
            role="reviewer",
            clearance=2,
            active=True,
        )
        auditor = User(
            id=f"aud_{suffix}",
            username=f"aud_{suffix}",
            password_hash=hash_password("AudPass123!"),
            role="auditor",
            clearance=2,
            active=True,
        )

        db.add_all([admin, eng1, eng2, rev1, rev2, auditor])
        db.commit()

        # Create tasks
        task1 = Task(
            id=f"task1_{suffix}",
            owner_id=eng1.id,
            request_text="Generate report 1",
            task_type="inspection_report",
            selected_models_json='["qwen3.5:4b"]',
            status="finished",
        )
        db.add(task1)
        db.commit()

        # Create artifacts
        # Artifact 1: owned by eng1, assigned to rev1
        art1 = Artifact(
            id=f"art1_{suffix}",
            task_id=task1.id,
            owner_id=eng1.id,
            kind="docx",
            filename="deliverable_1.docx",
            stored_path=str(art1_file),
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            status="PENDING_REVIEW",
            reviewer_id=rev1.id,
            validation_json=json.dumps([{"rule": "file_exists", "passed": True}]),
        )

        # Artifact 2: owned by eng2, unassigned
        art2 = Artifact(
            id=f"art2_{suffix}",
            task_id=task1.id,
            owner_id=eng2.id,
            kind="xlsx",
            filename="deliverable_2.xlsx",
            stored_path=str(art2_file),
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            status="PENDING_REVIEW",
            reviewer_id=None,
        )
        db.add_all([art1, art2])
        db.commit()

        # Create sessions
        _, admin_token = create_session(db, admin.id)
        _, eng1_token = create_session(db, eng1.id)
        _, eng2_token = create_session(db, eng2.id)
        _, rev1_token = create_session(db, rev1.id)
        _, rev2_token = create_session(db, rev2.id)
        _, auditor_token = create_session(db, auditor.id)

    app = create_app()
    client = TestClient(app)

    return {
        "client": client,
        "admin_token": admin_token,
        "eng1_token": eng1_token,
        "eng2_token": eng2_token,
        "rev1_token": rev1_token,
        "rev2_token": rev2_token,
        "auditor_token": auditor_token,
        "art1_id": art1.id,
        "art2_id": art2.id,
    }


def test_list_artifacts_scoped(api_test_data):
    client = api_test_data["client"]
    eng1_token = api_test_data["eng1_token"]
    admin_token = api_test_data["admin_token"]

    # Engineer 1 lists artifacts: sees only own artifact
    res = client.get("/api/artifacts", cookies={SESSION_COOKIE_NAME: eng1_token})
    assert res.status_code == 200
    data = res.json()
    ids = [a["id"] for a in data]
    assert api_test_data["art1_id"] in ids
    assert api_test_data["art2_id"] not in ids

    # Admin lists artifacts: sees all artifacts
    res_admin = client.get("/api/artifacts", cookies={SESSION_COOKIE_NAME: admin_token})
    assert res_admin.status_code == 200
    admin_ids = [a["id"] for a in res_admin.json()]
    assert api_test_data["art1_id"] in admin_ids
    assert api_test_data["art2_id"] in admin_ids


def test_get_artifact_detail_and_validation(api_test_data):
    client = api_test_data["client"]
    admin_token = api_test_data["admin_token"]
    art1_id = api_test_data["art1_id"]

    res = client.get(f"/api/artifacts/{art1_id}", cookies={SESSION_COOKIE_NAME: admin_token})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == art1_id
    assert data["kind"] == "docx"
    assert data["filename"] == "deliverable_1.docx"
    assert data["validation_results"] is not None
    assert len(data["validation_results"]) == 1
    assert data["validation_results"][0]["rule"] == "file_exists"


def test_sec_19_auditor_cannot_download_artifact(api_test_data):
    """SEC-19: Auditor role is strictly prohibited from downloading artifacts (403 Forbidden)."""
    client = api_test_data["client"]
    auditor_token = api_test_data["auditor_token"]
    art1_id = api_test_data["art1_id"]

    res = client.get(f"/api/artifacts/{art1_id}/download", cookies={SESSION_COOKIE_NAME: auditor_token})
    assert res.status_code == 403
    assert "SEC-19" in res.json()["detail"]["error"]["message"] or "Auditor" in res.json()["detail"]["error"]["message"]


def test_sec_20_reviewer_cannot_download_unassigned_artifact(api_test_data):
    """SEC-20: Reviewer cannot access/download artifact assigned to another reviewer (403 Forbidden)."""
    client = api_test_data["client"]
    rev1_token = api_test_data["rev1_token"]
    rev2_token = api_test_data["rev2_token"]
    art1_id = api_test_data["art1_id"]  # assigned to rev1

    # Rev1 is assigned -> succeeds (200 OK)
    res_rev1 = client.get(f"/api/artifacts/{art1_id}/download", cookies={SESSION_COOKIE_NAME: rev1_token})
    assert res_rev1.status_code == 200
    assert "attachment" in res_rev1.headers.get("content-disposition", "")

    # Rev2 is NOT assigned -> fails (403 Forbidden)
    res_rev2 = client.get(f"/api/artifacts/{art1_id}/download", cookies={SESSION_COOKIE_NAME: rev2_token})
    assert res_rev2.status_code == 403
    assert "SEC-20" in res_rev2.json()["detail"]["error"]["message"] or "another reviewer" in res_rev2.json()["detail"]["error"]["message"]


def test_engineer_download_permissions(api_test_data):
    client = api_test_data["client"]
    eng1_token = api_test_data["eng1_token"]
    eng2_token = api_test_data["eng2_token"]
    art1_id = api_test_data["art1_id"]  # owned by eng1

    # Eng1 (owner) downloads -> 200 OK
    res_owner = client.get(f"/api/artifacts/{art1_id}/download", cookies={SESSION_COOKIE_NAME: eng1_token})
    assert res_owner.status_code == 200

    # Eng2 (non-owner) downloads -> 403 Forbidden
    res_non_owner = client.get(f"/api/artifacts/{art1_id}/download", cookies={SESSION_COOKIE_NAME: eng2_token})
    assert res_non_owner.status_code == 403


def test_download_missing_artifact_404(api_test_data):
    client = api_test_data["client"]
    admin_token = api_test_data["admin_token"]

    res = client.get("/api/artifacts/non_existent_id/download", cookies={SESSION_COOKIE_NAME: admin_token})
    assert res.status_code == 404
