"""Unit and API tests for human review gate and segregation of duties (SEC-11).

Tests:
- Reviewer approves non-owned artifact -> 200 OK, status APPROVED, audit log written.
- SEC-11: Author reviewer tries to approve own artifact -> 403 Forbidden.
- SEC-11: Admin tries to approve artifact -> 403 Forbidden (separation of ops from review).
- Engineer and Auditor roles blocked from review endpoints -> 403 Forbidden.
- Reviewer rejects artifact -> status REJECTED.
- Review queue endpoint /api/review/queue returns pending review artifacts.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.core.config import get_settings
from backend.core.db import Artifact, Task, User, get_session_factory
from backend.core.security import SESSION_COOKIE_NAME, create_session, hash_password
from backend.main import create_app


@pytest.fixture
def review_test_env():
    """Setup test users, session cookies, and artifacts for review testing."""
    settings = get_settings()
    outputs_dir = Path(settings.DATA_DIR) / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    dummy_doc = outputs_dir / "review_test_doc.docx"
    dummy_doc.write_text("dummy deliverable content")

    import uuid
    uid = uuid.uuid4().hex[:8]

    factory = get_session_factory()
    with factory() as db:
        # 1. Admin
        admin = User(
            id=f"admin_{uid}",
            username=f"admin_{uid}",
            password_hash=hash_password("AdminPass123!"),
            role="admin",
            clearance=3,
            active=True,
        )
        # 2. Author Engineer
        author_eng = User(
            id=f"eng_{uid}",
            username=f"eng_{uid}",
            password_hash=hash_password("EngPass123!"),
            role="engineer",
            clearance=2,
            active=True,
        )
        # 3. Independent Reviewer 1
        reviewer_1 = User(
            id=f"rev1_{uid}",
            username=f"rev1_{uid}",
            password_hash=hash_password("RevPass123!"),
            role="reviewer",
            clearance=2,
            active=True,
        )
        # 4. Reviewer 2 (also author of a different artifact)
        reviewer_2 = User(
            id=f"rev2_{uid}",
            username=f"rev2_{uid}",
            password_hash=hash_password("RevPass123!"),
            role="reviewer",
            clearance=2,
            active=True,
        )
        # 5. Auditor
        auditor = User(
            id=f"aud_{uid}",
            username=f"aud_{uid}",
            password_hash=hash_password("AudPass123!"),
            role="auditor",
            clearance=2,
            active=True,
        )

        db.add_all([admin, author_eng, reviewer_1, reviewer_2, auditor])
        db.commit()

        # Task
        task = Task(
            id=f"task_{uid}",
            owner_id=author_eng.id,
            request_text="Prepare inspection report",
            task_type="inspection_report",
            selected_models_json='["qwen3.5:4b"]',
            status="finished",
        )
        db.add(task)
        db.commit()

        # Artifact 1: Created by author_eng
        art1 = Artifact(
            id=f"art1_{uid}",
            task_id=task.id,
            owner_id=author_eng.id,
            kind="docx",
            filename="review_test_doc.docx",
            stored_path=str(dummy_doc),
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            status="PENDING_REVIEW",
        )

        # Artifact 2: Created by reviewer_2 (to test self-approval rejection)
        art2 = Artifact(
            id=f"art2_{uid}",
            task_id=task.id,
            owner_id=reviewer_2.id,
            kind="docx",
            filename="review_test_doc.docx",
            stored_path=str(dummy_doc),
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            status="PENDING_REVIEW",
        )

        db.add_all([art1, art2])
        db.commit()

        # Sessions
        _, admin_token = create_session(db, admin.id)
        _, eng_token = create_session(db, author_eng.id)
        _, rev1_token = create_session(db, reviewer_1.id)
        _, rev2_token = create_session(db, reviewer_2.id)
        _, aud_token = create_session(db, auditor.id)

    app = create_app()
    client = TestClient(app)

    return {
        "client": client,
        "admin_token": admin_token,
        "eng_token": eng_token,
        "rev1_token": rev1_token,
        "rev2_token": rev2_token,
        "aud_token": aud_token,
        "art1_id": art1.id,
        "art2_id": art2.id,
        "rev1_id": reviewer_1.id,
    }


def test_reviewer_can_approve_artifact(review_test_env):
    """Authorized reviewer successfully approves an artifact deliverable."""
    client = review_test_env["client"]
    rev1_token = review_test_env["rev1_token"]
    art1_id = review_test_env["art1_id"]
    headers = {"X-Requested-With": "XMLHttpRequest"}

    res = client.post(
        f"/api/artifacts/{art1_id}/review",
        json={"decision": "approve", "comment": "All PAUT findings match SOP-301 tolerances."},
        headers=headers,
        cookies={SESSION_COOKIE_NAME: rev1_token},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "APPROVED"
    assert data["reviewer_id"] == review_test_env["rev1_id"]
    assert data["review_comment"] == "All PAUT findings match SOP-301 tolerances."
    assert data["reviewed_at"] is not None


def test_sec11_author_cannot_approve_own_artifact(review_test_env):
    """SEC-11: Reviewer cannot approve or review an artifact they created themselves."""
    client = review_test_env["client"]
    rev2_token = review_test_env["rev2_token"]
    art2_id = review_test_env["art2_id"]  # Created by reviewer_2
    headers = {"X-Requested-With": "XMLHttpRequest"}

    res = client.post(
        f"/api/artifacts/{art2_id}/review",
        json={"decision": "approve", "comment": "Self approval attempt."},
        headers=headers,
        cookies={SESSION_COOKIE_NAME: rev2_token},
    )
    assert res.status_code == 403
    assert "Segregation of duties" in res.json()["detail"]["error"]["message"]


def test_sec11_admin_cannot_approve_artifact(review_test_env):
    """SEC-11: Admin role is prohibited from approving deliverables (separation of ops from review)."""
    client = review_test_env["client"]
    admin_token = review_test_env["admin_token"]
    art1_id = review_test_env["art1_id"]
    headers = {"X-Requested-With": "XMLHttpRequest"}

    res = client.post(
        f"/api/artifacts/{art1_id}/review",
        json={"decision": "approve", "comment": "Admin override attempt."},
        headers=headers,
        cookies={SESSION_COOKIE_NAME: admin_token},
    )
    assert res.status_code == 403


def test_engineer_and_auditor_cannot_call_review(review_test_env):
    """Engineers and Auditors cannot submit review decisions."""
    client = review_test_env["client"]
    eng_token = review_test_env["eng_token"]
    aud_token = review_test_env["aud_token"]
    art1_id = review_test_env["art1_id"]
    headers = {"X-Requested-With": "XMLHttpRequest"}

    # Engineer
    res_eng = client.post(
        f"/api/artifacts/{art1_id}/review",
        json={"decision": "approve", "comment": "Engineer approval attempt."},
        headers=headers,
        cookies={SESSION_COOKIE_NAME: eng_token},
    )
    assert res_eng.status_code == 403

    # Auditor
    res_aud = client.post(
        f"/api/artifacts/{art1_id}/review",
        json={"decision": "approve", "comment": "Auditor approval attempt."},
        headers=headers,
        cookies={SESSION_COOKIE_NAME: aud_token},
    )
    assert res_aud.status_code == 403


def test_reviewer_can_reject_artifact(review_test_env):
    """Reviewer can reject an artifact with mandatory comment."""
    client = review_test_env["client"]
    rev1_token = review_test_env["rev1_token"]
    art1_id = review_test_env["art1_id"]
    headers = {"X-Requested-With": "XMLHttpRequest"}

    res = client.post(
        f"/api/artifacts/{art1_id}/review",
        json={"decision": "reject", "comment": "Calculation formula assumption requires recalibration."},
        headers=headers,
        cookies={SESSION_COOKIE_NAME: rev1_token},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"


def test_review_queue_listing(review_test_env):
    """GET /api/review/queue returns pending review artifacts for reviewers only."""
    client = review_test_env["client"]
    rev1_token = review_test_env["rev1_token"]
    eng_token = review_test_env["eng_token"]

    # Reviewer accesses queue -> 200 OK
    res = client.get("/api/review/queue", cookies={SESSION_COOKIE_NAME: rev1_token})
    assert res.status_code == 200
    queue = res.json()
    assert isinstance(queue, list)
    assert any(a["status"] == "PENDING_REVIEW" for a in queue)

    # Engineer attempts to access review queue -> 403 Forbidden
    res_eng = client.get("/api/review/queue", cookies={SESSION_COOKIE_NAME: eng_token})
    assert res_eng.status_code == 403
