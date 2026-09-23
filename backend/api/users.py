"""User management endpoints (Admin only)."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.audit import log_event
from backend.core.db import User, get_db, utc_now
from backend.core.rbac import Role, require_role
from backend.core.security import hash_password
from backend.schemas.auth import UserCreateRequest, UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    admin: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> List[UserResponse]:
    """List all registered system users. Requires admin role."""
    stmt = select(User).order_by(User.created_at.asc())
    users = db.execute(stmt).scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    req: UserCreateRequest,
    admin: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Create a new user account. Requires admin role."""
    # Check if username exists
    stmt = select(User).where(User.username == req.username)
    if db.execute(stmt).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "USERNAME_TAKEN", "message": "Username already exists"}},
        )

    pw_hash = hash_password(req.password)
    new_user = User(
        username=req.username,
        password_hash=pw_hash,
        role=req.role,
        clearance=req.clearance,
        active=True,
        created_at=utc_now(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_event(
        event_type="user_changed",
        status="ok",
        user_id=admin.id,
        role=admin.role,
        details={
            "action": "create_user",
            "target_user_id": new_user.id,
            "target_username": new_user.username,
            "target_role": new_user.role,
            "target_clearance": new_user.clearance,
        },
        db=db,
    )

    return UserResponse.model_validate(new_user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    req: UserUpdateRequest,
    admin: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update user role, clearance, status, or password. Requires admin role."""
    stmt = select(User).where(User.id == user_id)
    target_user = db.execute(stmt).scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )

    changes = {}
    if req.role is not None:
        target_user.role = req.role
        changes["role"] = req.role
    if req.clearance is not None:
        target_user.clearance = req.clearance
        changes["clearance"] = req.clearance
    if req.active is not None:
        target_user.active = req.active
        changes["active"] = req.active
    if req.password is not None:
        target_user.password_hash = hash_password(req.password)
        changes["password_updated"] = True

    db.commit()
    db.refresh(target_user)

    log_event(
        event_type="user_changed",
        status="ok",
        user_id=admin.id,
        role=admin.role,
        details={
            "action": "update_user",
            "target_user_id": target_user.id,
            "target_username": target_user.username,
            "changes": changes,
        },
        db=db,
    )

    return UserResponse.model_validate(target_user)
