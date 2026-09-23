"""Tests for User management API and Audit query/verify/export APIs."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.audit import log_event
from backend.core.db import Base, User, get_db
from backend.core.rbac import Clearance, Role
from backend.core.security import get_current_user, hash_password
from backend.main import create_app


@pytest.fixture
def api_test_setup(tmp_path):
    """Setup isolated test app with mock admin and engineer."""
    test_db = tmp_path / "test_api.db"
    engine = create_engine(f"sqlite:///{test_db.resolve()}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

    # Seed admin & auditor
    db = TestingSession()
    admin = User(
        id="admin-id-1",
        username="admin_user",
        password_hash=hash_password("SuperSecret123!"),
        role=Role.ADMIN.value,
        clearance=Clearance.RESTRICTED.value,
        active=True,
    )
    auditor = User(
        id="auditor-id-1",
        username="auditor_user",
        password_hash=hash_password("SuperSecret123!"),
        role=Role.AUDITOR.value,
        clearance=Clearance.RESTRICTED.value,
        active=True,
    )
    engineer = User(
        id="eng-id-1",
        username="engineer_user",
        password_hash=hash_password("SuperSecret123!"),
        role=Role.ENGINEER.value,
        clearance=Clearance.CONFIDENTIAL.value,
        active=True,
    )
    db.add_all([admin, auditor, engineer])
    db.commit()

    # Seed sample audit logs
    for i in range(5):
        log_event(
            event_type="tool_call",
            status="ok",
            user_id=engineer.id,
            role="engineer",
            db=db,
        )
    db.close()

    app = create_app()

    def override_get_db():
        s = TestingSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db

    return app, admin, auditor, engineer


def test_users_api_admin_only(api_test_setup):
    """SEC-12: Only admin can manage users; engineer is blocked with 403."""
    app, admin, auditor, engineer = api_test_setup
    client = TestClient(app)

    # 1. Engineer attempt -> 403
    app.dependency_overrides[get_current_user] = lambda: engineer
    res_eng = client.get("/api/users")
    assert res_eng.status_code == 403

    # 2. Admin attempt -> 200 list
    app.dependency_overrides[get_current_user] = lambda: admin
    res_admin = client.get("/api/users")
    assert res_admin.status_code == 200
    users = res_admin.json()
    assert len(users) >= 3

    # 3. Admin create user -> 201
    create_res = client.post(
        "/api/users",
        json={
            "username": "new_reviewer",
            "password": "ValidPassword123!",
            "role": "reviewer",
            "clearance": 3,
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert create_res.status_code == 201
    assert create_res.json()["username"] == "new_reviewer"

    # 4. Admin update user -> 200
    created_id = create_res.json()["id"]
    patch_res = client.patch(
        f"/api/users/{created_id}",
        json={"clearance": 2, "active": False},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["clearance"] == 2
    assert patch_res.json()["active"] is False


def test_audit_api_query_verify_export(api_test_setup):
    """Auditor and Admin can query audit log, verify hash chain, and export JSONL/CSV."""
    app, admin, auditor, engineer = api_test_setup
    client = TestClient(app)

    # 1. Engineer cannot query audit log -> 403
    app.dependency_overrides[get_current_user] = lambda: engineer
    res_eng = client.get("/api/audit")
    assert res_eng.status_code == 403

    # 2. Auditor can query audit log -> 200
    app.dependency_overrides[get_current_user] = lambda: auditor
    res_aud = client.get("/api/audit")
    assert res_aud.status_code == 200
    data = res_aud.json()
    assert data["total"] >= 5
    assert len(data["items"]) >= 5

    # 3. Auditor can verify chain -> 200 {valid: True}
    res_verify = client.get("/api/audit/verify")
    assert res_verify.status_code == 200
    assert res_verify.json()["valid"] is True

    # 4. Auditor can export as JSONL
    res_export_jsonl = client.get("/api/audit/export?format=jsonl")
    assert res_export_jsonl.status_code == 200
    assert "application/x-ndjson" in res_export_jsonl.headers["content-type"]
    lines = res_export_jsonl.text.strip().split("\n")
    assert len(lines) >= 5

    # 5. Auditor can export as CSV
    res_export_csv = client.get("/api/audit/export?format=csv")
    assert res_export_csv.status_code == 200
    assert "text/csv" in res_export_csv.headers["content-type"]
    assert "event_type" in res_export_csv.text
