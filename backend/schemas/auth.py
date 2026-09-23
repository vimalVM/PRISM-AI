"""Pydantic schemas for authentication, users, and audit records."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """User login credential payload."""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Public user information returned by API."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    role: str
    clearance: int
    active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserCreateRequest(BaseModel):
    """Payload for admin creating a new user account."""
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=12, max_length=128)
    role: str = Field(..., pattern="^(admin|engineer|reviewer|auditor)$")
    clearance: int = Field(default=0, ge=0, le=3)


class UserUpdateRequest(BaseModel):
    """Payload for admin updating an existing user account."""
    role: Optional[str] = Field(default=None, pattern="^(admin|engineer|reviewer|auditor)$")
    clearance: Optional[int] = Field(default=None, ge=0, le=3)
    active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=12, max_length=128)


class SessionResponse(BaseModel):
    """Current session and authenticated user profile."""
    user: UserResponse
    expires_at: datetime


class AuditEventResponse(BaseModel):
    """Audit log entry schema."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    ts: str
    run_id: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None
    event_type: str
    model: Optional[str] = None
    tool: Optional[str] = None
    file_ids_json: Optional[str] = None
    status: str
    duration_ms: Optional[int] = None
    details_json: Optional[str] = None
    prev_hash: str
    hash: str


class AuditListResponse(BaseModel):
    """Paginated list of audit events."""
    items: List[AuditEventResponse]
    total: int


class AuditVerifyResponse(BaseModel):
    """Verification outcome of the audit log hash chain."""
    valid: bool
    detail: Optional[str] = None
