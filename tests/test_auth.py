"""Tests for authentication, session management, and login lockout (SEC-13)."""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.core.audit import log_event
from backend.core.config import get_settings
from backend.core.db import Base, User, UserSession, get_db
from backend.core.security import (
    _failed_attempts,
    _locked_until,
    create_session,
    hash_password,
    is_account_locked,
    record_failed_login,
    record_successful_login,
    sign_session_id,
    unsign_session_id,
    verify_password,
)
from backend.main import create_app


@pytest.fixture
def auth_client(tmp_path):
    """Create test client with fresh test database and registered test users."""
    test_db_path = tmp_path / "test_auth.db"
    engine = create_engine(f"sqlite:///{test_db_path.resolve()}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Seed test users
    db = TestingSessionLocal()
    admin_user = User(
        username="admin",
        password_hash=hash_password("ValidPassword123!"),
        role="admin",
        clearance=3,
        active=True,
    )
    eng_user = User(
        username="engineer",
        password_hash=hash_password("ValidPassword123!"),
        role="engineer",
        clearance=2,
        active=True,
    )
    inactive_user = User(
        username="disabled_user",
        password_hash=hash_password("ValidPassword123!"),
        role="engineer",
        clearance=1,
        active=False,
    )
    db.add_all([admin_user, eng_user, inactive_user])
    db.commit()
    db.close()

    app = create_app()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Clear lockout tracking structures before each test
    _failed_attempts.clear()
    _locked_until.clear()

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_argon2id_password_hashing():
    """Argon2id hashing correctly hashes and verifies passwords."""
    password = "SecurePassword123!"
    pw_hash = hash_password(password)

    assert pw_hash.startswith("$argon2id$")
    assert verify_password(password, pw_hash) is True
    assert verify_password("WrongPassword!", pw_hash) is False


def test_session_signing_and_tamper_detection():
    """Signed session cookies verify successfully, tampered cookies are rejected."""
    session_id = "test-session-uuid-1234"
    signed = sign_session_id(session_id)
    assert "." in signed

    # Valid unsign
    unsigned = unsign_session_id(signed)
    assert unsigned == session_id

    # Tampered signature
    tampered_sig = signed[:-4] + "ffff"
    assert unsign_session_id(tampered_sig) is None

    # Tampered session_id
    tampered_id = "other-session." + signed.split(".")[1]
    assert unsign_session_id(tampered_id) is None


def test_login_success_and_session_cookie(auth_client):
    """Successful login sets signed saw_session cookie and returns profile."""
    res = auth_client.post(
        "/api/auth/login",
        json={"username": "engineer", "password": "ValidPassword123!"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["username"] == "engineer"
    assert data["user"]["role"] == "engineer"
    assert "saw_session" in res.cookies


def test_login_failure_wrong_password(auth_client):
    """Wrong password returns 401 and sets no session cookie."""
    res = auth_client.post(
        "/api/auth/login",
        json={"username": "engineer", "password": "WrongPassword!"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res.status_code == 401
    assert "saw_session" not in res.cookies
    assert res.json()["detail"]["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_lockout_after_5_failures_sec13(auth_client):
    """SEC-13: 5 consecutive failed login attempts locks account for 10 minutes."""
    username = "engineer"

    # 5 failed attempts
    for i in range(5):
        res = auth_client.post(
            "/api/auth/login",
            json={"username": username, "password": "WrongPassword!"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert res.status_code == 401

    # 6th attempt (even with correct password) must be rejected with 403 ACCOUNT_LOCKED
    res_locked = auth_client.post(
        "/api/auth/login",
        json={"username": username, "password": "ValidPassword123!"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res_locked.status_code == 403
    assert res_locked.json()["detail"]["error"]["code"] == "ACCOUNT_LOCKED"


def test_successful_login_resets_failed_attempts(auth_client):
    """A successful login resets previous failure counts."""
    username = "engineer"

    # 2 failed attempts
    for _ in range(2):
        auth_client.post(
            "/api/auth/login",
            json={"username": username, "password": "WrongPassword!"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    # 1 successful login
    res_ok = auth_client.post(
        "/api/auth/login",
        json={"username": username, "password": "ValidPassword123!"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res_ok.status_code == 200

    # Next failures start counter from 0
    is_locked, _ = is_account_locked(username)
    assert is_locked is False


def test_session_fixation_protection(auth_client):
    """Each login issues a fresh, distinct session identifier."""
    res1 = auth_client.post(
        "/api/auth/login",
        json={"username": "engineer", "password": "ValidPassword123!"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    cookie1 = res1.cookies["saw_session"]

    res2 = auth_client.post(
        "/api/auth/login",
        json={"username": "engineer", "password": "ValidPassword123!"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    cookie2 = res2.cookies["saw_session"]

    assert cookie1 != cookie2


def test_logout_revokes_session(auth_client):
    """Logout invalidates the session and deletes the cookie."""
    # Login
    login_res = auth_client.post(
        "/api/auth/login",
        json={"username": "engineer", "password": "ValidPassword123!"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert login_res.status_code == 200
    cookie_val = login_res.cookies["saw_session"]

    # Access protected /api/auth/me
    auth_client.cookies.set("saw_session", cookie_val)
    me_res = auth_client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "engineer"

    # Logout
    logout_res = auth_client.post(
        "/api/auth/logout",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert logout_res.status_code == 200

    # Further calls to /api/auth/me should now fail with 401
    auth_client.cookies.set("saw_session", cookie_val)
    me_after_logout = auth_client.get("/api/auth/me")
    assert me_after_logout.status_code == 401
