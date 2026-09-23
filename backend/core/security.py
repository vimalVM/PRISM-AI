"""Authentication, session security, password hashing, and brute-force protection.

Implements SEC-13 (Argon2id hashing, signed session cookies, sliding TTL,
login lockout after 5 failures within 10 minutes).
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
from pathlib import Path
import secrets
import threading
from typing import Dict, List, Optional, Tuple

import argon2
from argon2.exceptions import VerifyMismatchError
from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.audit import log_event
from backend.core.config import get_settings
from backend.core.db import User, UserSession, get_db, utc_now


SESSION_COOKIE_NAME = "saw_session"

_ph = argon2.PasswordHasher()

# Lockout tracker state
_lockout_lock = threading.Lock()
_failed_attempts: Dict[str, List[datetime]] = {}
_locked_until: Dict[str, datetime] = {}


def hash_password(password: str) -> str:
    """Hash password with Argon2id using a per-user random salt."""
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against Argon2id hash. Never logs or leaks plaintext."""
    try:
        return _ph.verify(password_hash, password)
    except (VerifyMismatchError, Exception):
        return False


def get_secret_key() -> bytes:
    """Load or generate the secret key stored in data/secrets/session.key.
    
    Generates a cryptographically strong 256-bit key on first run.
    """
    settings = get_settings()
    key_path = Path(settings.SECRET_KEY_FILE)

    if not key_path.exists():
        key_path.parent.mkdir(parents=True, exist_ok=True)
        raw_key = secrets.token_bytes(32)
        try:
            # On POSIX, restrict permissions to owner only
            flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
            mode = 0o600
            fd = os.open(key_path, flags, mode)
            with open(fd, "wb") as f:
                f.write(raw_key)
        except Exception:
            # Fallback for Windows or environments where os.open mode behaves differently
            with open(key_path, "wb") as f:
                f.write(raw_key)
        return raw_key

    with open(key_path, "rb") as f:
        return f.read()


def sign_session_id(session_id: str) -> str:
    """Sign session id with HMAC-SHA256."""
    key = get_secret_key()
    signature = hmac.new(key, session_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{session_id}.{signature}"


def unsign_session_id(cookie_value: str) -> Optional[str]:
    """Verify HMAC signature and return raw session id if valid."""
    if not cookie_value or "." not in cookie_value:
        return None

    parts = cookie_value.split(".", 1)
    if len(parts) != 2:
        return None

    session_id, signature = parts
    key = get_secret_key()
    expected_sig = hmac.new(key, session_id.encode("utf-8"), hashlib.sha256).hexdigest()

    if hmac.compare_digest(signature, expected_sig):
        return session_id
    return None


# --- Lockout mechanism (SEC-13) ---

def is_account_locked(username: str) -> Tuple[bool, int]:
    """Check if account is currently locked out.
    
    Returns (is_locked, remaining_seconds).
    """
    settings = get_settings()
    now = utc_now()
    with _lockout_lock:
        if username in _locked_until:
            unlock_time = _locked_until[username]
            if now < unlock_time:
                remaining = int((unlock_time - now).total_seconds())
                return True, remaining
            else:
                del _locked_until[username]
                _failed_attempts.pop(username, None)
        return False, 0


def record_failed_login(username: str) -> bool:
    """Record a failed login attempt. If attempts exceed limit, lock account.
    
    Returns True if this attempt resulted in account lockout.
    """
    settings = get_settings()
    now = utc_now()
    window = timedelta(minutes=settings.LOGIN_LOCK_MIN)

    with _lockout_lock:
        attempts = _failed_attempts.setdefault(username, [])
        # Filter attempts within window
        attempts = [t for t in attempts if now - t <= window]
        attempts.append(now)
        _failed_attempts[username] = attempts

        if len(attempts) >= settings.LOGIN_MAX_FAILS:
            _locked_until[username] = now + timedelta(minutes=settings.LOGIN_LOCK_MIN)
            return True
        return False


def record_successful_login(username: str) -> None:
    """Reset failed login attempts upon successful authentication."""
    with _lockout_lock:
        _failed_attempts.pop(username, None)
        _locked_until.pop(username, None)


# --- Session Management ---

def create_session(db: Session, user_id: str) -> Tuple[UserSession, str]:
    """Create a new server-side session and return (UserSession, signed_cookie_value)."""
    settings = get_settings()
    now = utc_now()
    expires_at = now + timedelta(minutes=settings.SESSION_TTL_MIN)

    session = UserSession(
        user_id=user_id,
        created_at=now,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    signed_cookie = sign_session_id(session.id)
    return session, signed_cookie


def revoke_session(db: Session, session_id: str) -> None:
    """Revoke a session in the database."""
    stmt = select(UserSession).where(UserSession.id == session_id)
    session = db.execute(stmt).scalar_one_or_none()
    if session:
        session.revoked = True
        db.commit()


def get_current_user(
    request: Request,
    saw_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to authenticate requests via signed session cookie.
    
    Implements sliding session expiration.
    """
    if not saw_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}},
        )

    raw_session_id = unsign_session_id(saw_session)
    if not raw_session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_SESSION", "message": "Invalid session signature"}},
        )

    stmt = select(UserSession).where(UserSession.id == raw_session_id)
    session_record = db.execute(stmt).scalar_one_or_none()

    if not session_record or session_record.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "SESSION_REVOKED", "message": "Session expired or revoked"}},
        )

    now = utc_now()
    # Handle both timezone-aware and naive stored datetimes cleanly
    expires = session_record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now > expires:
        session_record.revoked = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "SESSION_EXPIRED", "message": "Session has expired"}},
        )

    # Slide expiration TTL
    settings = get_settings()
    session_record.expires_at = now + timedelta(minutes=settings.SESSION_TTL_MIN)
    db.commit()

    # Fetch User
    stmt_user = select(User).where(User.id == session_record.user_id)
    user = db.execute(stmt_user).scalar_one_or_none()

    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_INACTIVE", "message": "User account is disabled or missing"}},
        )

    # Attach session_id to request state for use in logout
    request.state.session_id = raw_session_id
    return user
