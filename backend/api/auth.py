"""Authentication endpoints: login, logout, and current user profile."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.audit import log_event
from backend.core.config import get_settings
from backend.core.db import User, get_db, utc_now
from backend.core.security import (
    SESSION_COOKIE_NAME,
    create_session,
    get_current_user,
    is_account_locked,
    record_failed_login,
    record_successful_login,
    revoke_session,
    verify_password,
)
from backend.schemas.auth import LoginRequest, SessionResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=SessionResponse)
def login(
    login_req: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Authenticate user with username and password, returning a signed session cookie."""
    settings = get_settings()

    # 1. Check brute force lockout
    is_locked, remaining_seconds = is_account_locked(login_req.username)
    if is_locked:
        log_event(
            event_type="login_failed",
            status="denied",
            details={
                "username": login_req.username,
                "reason": "account_locked",
                "remaining_seconds": remaining_seconds,
            },
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "ACCOUNT_LOCKED",
                    "message": f"Account temporarily locked due to excessive failed attempts. Try again in {remaining_seconds}s.",
                }
            },
        )

    # 2. Query user from database
    stmt = select(User).where(User.username == login_req.username)
    user = db.execute(stmt).scalar_one_or_none()

    # 3. Verify credentials
    if not user or not verify_password(login_req.password, user.password_hash):
        did_lock = record_failed_login(login_req.username)
        event_type = "account_locked" if did_lock else "login_failed"
        log_event(
            event_type=event_type,
            status="error",
            user_id=user.id if user else None,
            details={"username": login_req.username, "locked": did_lock},
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid username or password",
                }
            },
        )

    if not user.active:
        log_event(
            event_type="login_failed",
            status="denied",
            user_id=user.id,
            details={"username": login_req.username, "reason": "user_inactive"},
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "USER_INACTIVE", "message": "User account is disabled"}},
        )

    # 4. Successful login: clear lockout, create session, update last_login
    record_successful_login(login_req.username)
    session_record, signed_cookie = create_session(db, user.id)

    user.last_login_at = utc_now()
    db.commit()

    log_event(
        event_type="login_ok",
        status="ok",
        user_id=user.id,
        role=user.role,
        details={"username": user.username},
        db=db,
    )

    # Set HttpOnly, SameSite=Strict cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=signed_cookie,
        max_age=settings.SESSION_TTL_MIN * 60,
        httponly=True,
        samesite="strict",
        secure=False,  # Set True when TLS is enabled; for localhost HTTP False is required
        path="/",
    )

    return SessionResponse(
        user=UserResponse.model_validate(user),
        expires_at=session_record.expires_at,
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Revoke active session and delete session cookie."""
    session_id = getattr(request.state, "session_id", None)
    if session_id:
        revoke_session(db, session_id)

    log_event(
        event_type="logout",
        status="ok",
        user_id=current_user.id,
        role=current_user.role,
        details={"username": current_user.username},
        db=db,
    )

    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"status": "ok", "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return profile and clearance information of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
