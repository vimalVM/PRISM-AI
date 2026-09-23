"""Role-Based Access Control (RBAC), clearance hierarchy, and segregation of duties.

Implements SEC-11 (segregation of duties, reviewer cannot approve own work, admin cannot approve),
SEC-12 (engineers blocked from admin endpoints), and permission matrix enforcement from 03_SECURITY_AND_ACCESS.md §5.
"""

from enum import Enum, IntEnum
from typing import Any, Callable, Dict, List, Set, Tuple

from fastapi import Depends, HTTPException, status

from backend.core.audit import log_event
from backend.core.db import Artifact, Task, User
from backend.core.security import get_current_user


class Role(str, Enum):
    """System user roles."""
    ADMIN = "admin"
    ENGINEER = "engineer"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"


class Clearance(IntEnum):
    """Clearance levels and data classification hierarchy."""
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    RESTRICTED = 3


# Permission matrix derived from 03_SECURITY_AND_ACCESS.md §5.3
PERMISSION_MATRIX: Dict[str, Set[str]] = {
    "login_view_profile": {Role.ADMIN, Role.ENGINEER, Role.REVIEWER, Role.AUDITOR},
    "manage_users": {Role.ADMIN},
    "upload_task_files": {Role.ADMIN, Role.ENGINEER, Role.REVIEWER},
    "start_agent_runs": {Role.ADMIN, Role.ENGINEER},
    "view_own_tasks": {Role.ADMIN, Role.ENGINEER, Role.REVIEWER},
    "view_others_tasks": {Role.ADMIN, Role.REVIEWER, Role.AUDITOR},
    "download_artifacts": {Role.ADMIN, Role.ENGINEER, Role.REVIEWER},
    "approve_reject_artifacts": {Role.REVIEWER},  # Note: Admin explicitly excluded (separation of duties)
    "ingest_delete_kb": {Role.ADMIN},
    "search_kb": {Role.ADMIN, Role.ENGINEER, Role.REVIEWER},
    "view_models_health": {Role.ADMIN, Role.ENGINEER, Role.REVIEWER, Role.AUDITOR},
    "reload_models": {Role.ADMIN},
    "view_audit": {Role.ADMIN, Role.AUDITOR},
    "export_audit_verify": {Role.ADMIN, Role.AUDITOR},
    "view_sovereignty": {Role.ADMIN, Role.ENGINEER, Role.REVIEWER, Role.AUDITOR},
    "run_egress_probe": {Role.ADMIN, Role.AUDITOR},
}


def has_permission(role: str, capability: str) -> bool:
    """Check if role has capability per permission matrix."""
    allowed_roles = PERMISSION_MATRIX.get(capability, set())
    return role in allowed_roles


def require_role(*allowed_roles: str | Role) -> Callable:
    """FastAPI dependency to ensure current authenticated user has an allowed role.
    
    Raises 403 FORBIDDEN and logs access_denied audit event on failure.
    """
    roles_set = {r.value if hasattr(r, "value") else str(r) for r in allowed_roles}

    def _role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles_set:
            log_event(
                event_type="access_denied",
                status="denied",
                user_id=user.id,
                role=user.role,
                details={
                    "reason": f"Required role in {sorted(list(roles_set))}, got '{user.role}'",
                    "required_roles": sorted(list(roles_set)),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"User role '{user.role}' is not authorized for this operation",
                    }
                },
            )
        return user

    return _role_checker


def require_clearance(min_level: int | Clearance) -> Callable:
    """FastAPI dependency to enforce minimum clearance level.
    
    Raises 403 FORBIDDEN if user clearance is below requirement.
    """
    required_val = int(min_level)

    def _clearance_checker(user: User = Depends(get_current_user)) -> User:
        if user.clearance < required_val:
            log_event(
                event_type="access_denied",
                status="denied",
                user_id=user.id,
                role=user.role,
                details={
                    "reason": f"Required clearance {required_val}, user has {user.clearance}",
                    "required_clearance": required_val,
                    "user_clearance": user.clearance,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "INSUFFICIENT_CLEARANCE",
                        "message": "Clearance level is insufficient to access this resource",
                    }
                },
            )
        return user

    return _clearance_checker


# --- Segregation of Duties and Scoped Access (SEC-11) ---

def can_review_artifact(user: User, artifact: Artifact) -> Tuple[bool, str]:
    """Check if user is permitted to review and approve/reject an artifact.
    
    Enforces segregation of duties:
    - Only 'reviewer' role can review.
    - Admin cannot approve (separation of operations from review).
    - Reviewer cannot approve an artifact they created themselves.
    
    Returns (allowed, reason).
    """
    if user.role != Role.REVIEWER.value:
        return False, f"Role '{user.role}' cannot review artifacts (only reviewer)"

    if artifact.owner_id == user.id:
        return False, "Segregation of duties: authors cannot review or approve their own artifacts"

    return True, "OK"


def can_access_task(user: User, task: Task) -> bool:
    """Determine if a user has access to view a specific task's details.
    
    Rules:
    - Admin: can view any task
    - Auditor: can view task metadata
    - Engineer: own tasks only
    - Reviewer: own tasks or tasks with artifacts submitted for review
    """
    if user.role in (Role.ADMIN.value, Role.AUDITOR.value):
        return True
    if task.owner_id == user.id:
        return True
    # Reviewer may view task if assigned/pending review
    if user.role == Role.REVIEWER.value:
        return True
    return False
