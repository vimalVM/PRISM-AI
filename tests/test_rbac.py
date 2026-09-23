"""Tests for Role-Based Access Control, clearance hierarchy, and segregation of duties (SEC-11, SEC-12)."""

import pytest
from fastapi import HTTPException

from backend.core.db import Artifact, Task, User
from backend.core.rbac import (
    Clearance,
    PERMISSION_MATRIX,
    Role,
    can_access_task,
    can_review_artifact,
    has_permission,
    require_clearance,
    require_role,
)


@pytest.fixture
def users_by_role():
    """Create mock User objects for each defined role and clearance."""
    return {
        "admin": User(id="user-admin-1", username="admin", role=Role.ADMIN.value, clearance=Clearance.RESTRICTED.value),
        "engineer": User(id="user-eng-1", username="engineer", role=Role.ENGINEER.value, clearance=Clearance.CONFIDENTIAL.value),
        "reviewer": User(id="user-rev-1", username="reviewer", role=Role.REVIEWER.value, clearance=Clearance.RESTRICTED.value),
        "auditor": User(id="user-aud-1", username="auditor", role=Role.AUDITOR.value, clearance=Clearance.RESTRICTED.value),
    }


def test_clearance_hierarchy():
    """Clearance hierarchy: PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED."""
    assert Clearance.PUBLIC < Clearance.INTERNAL
    assert Clearance.INTERNAL < Clearance.CONFIDENTIAL
    assert Clearance.CONFIDENTIAL < Clearance.RESTRICTED


@pytest.mark.parametrize(
    "role,capability,expected",
    [
        # manage_users (admin only)
        ("admin", "manage_users", True),
        ("engineer", "manage_users", False),
        ("reviewer", "manage_users", False),
        ("auditor", "manage_users", False),
        # approve_reject_artifacts (reviewer only - admin explicitly excluded)
        ("admin", "approve_reject_artifacts", False),
        ("engineer", "approve_reject_artifacts", False),
        ("reviewer", "approve_reject_artifacts", True),
        ("auditor", "approve_reject_artifacts", False),
        # upload_task_files
        ("admin", "upload_task_files", True),
        ("engineer", "upload_task_files", True),
        ("reviewer", "upload_task_files", True),
        ("auditor", "upload_task_files", False),
        # start_agent_runs
        ("admin", "start_agent_runs", True),
        ("engineer", "start_agent_runs", True),
        ("reviewer", "start_agent_runs", False),
        ("auditor", "start_agent_runs", False),
        # ingest_delete_kb
        ("admin", "ingest_delete_kb", True),
        ("engineer", "ingest_delete_kb", False),
        ("reviewer", "ingest_delete_kb", False),
        ("auditor", "ingest_delete_kb", False),
        # reload_models
        ("admin", "reload_models", True),
        ("engineer", "reload_models", False),
        ("reviewer", "reload_models", False),
        ("auditor", "reload_models", False),
        # view_audit
        ("admin", "view_audit", True),
        ("engineer", "view_audit", False),
        ("reviewer", "view_audit", False),
        ("auditor", "view_audit", True),
    ],
)
def test_permission_matrix_rules(role, capability, expected):
    """Test permission matrix rules from 03_SECURITY_AND_ACCESS.md §5.3."""
    assert has_permission(role, capability) == expected


def test_require_role_authorized(users_by_role):
    """require_role passes without error when user has permitted role."""
    admin_checker = require_role(Role.ADMIN)
    result = admin_checker(user=users_by_role["admin"])
    assert result.username == "admin"


def test_require_role_forbidden_sec12(users_by_role):
    """SEC-12: Engineer blocked from calling admin endpoints with 403."""
    admin_checker = require_role(Role.ADMIN)

    with pytest.raises(HTTPException) as exc_info:
        admin_checker(user=users_by_role["engineer"])

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error"]["code"] == "FORBIDDEN"


def test_require_clearance_enforcement(users_by_role):
    """require_clearance permits >= level and forbids < level."""
    # Clearance requirement: RESTRICTED (3)
    restricted_checker = require_clearance(Clearance.RESTRICTED)

    # Admin has clearance 3 -> OK
    assert restricted_checker(user=users_by_role["admin"]) is not None

    # Engineer has clearance 2 (CONFIDENTIAL) -> 403
    with pytest.raises(HTTPException) as exc_info:
        restricted_checker(user=users_by_role["engineer"])

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error"]["code"] == "INSUFFICIENT_CLEARANCE"


def test_segregation_of_duties_sec11(users_by_role):
    """SEC-11: Segregation of duties on artifact review."""
    reviewer = users_by_role["reviewer"]
    admin = users_by_role["admin"]
    engineer = users_by_role["engineer"]

    # 1. Standard artifact created by engineer
    eng_artifact = Artifact(
        id="art-1",
        task_id="task-1",
        owner_id=engineer.id,
        kind="docx",
        filename="report.docx",
        stored_path="data/outputs/report.docx",
        sha256="abc",
    )

    # Reviewer can review engineer's artifact
    allowed, msg = can_review_artifact(reviewer, eng_artifact)
    assert allowed is True
    assert msg == "OK"

    # Admin CANNOT review/approve artifact (separation of admin from approval)
    allowed, msg = can_review_artifact(admin, eng_artifact)
    assert allowed is False
    assert "cannot review" in msg

    # Engineer CANNOT review/approve artifact
    allowed, msg = can_review_artifact(engineer, eng_artifact)
    assert allowed is False
    assert "cannot review" in msg

    # 2. Reviewer who is also an author CANNOT approve their own artifact
    rev_own_artifact = Artifact(
        id="art-2",
        task_id="task-2",
        owner_id=reviewer.id,
        kind="docx",
        filename="reviewer_work.docx",
        stored_path="data/outputs/reviewer_work.docx",
        sha256="xyz",
    )
    allowed, msg = can_review_artifact(reviewer, rev_own_artifact)
    assert allowed is False
    assert "own artifacts" in msg


def test_task_access_scoping(users_by_role):
    """Task access rules based on user role and ownership."""
    engineer = users_by_role["engineer"]
    admin = users_by_role["admin"]
    auditor = users_by_role["auditor"]

    own_task = Task(
        id="task-own",
        owner_id=engineer.id,
        request_text="My task",
        status="completed",
    )
    other_task = Task(
        id="task-other",
        owner_id="someone-else",
        request_text="Other task",
        status="completed",
    )

    # Engineer can view own task but not others'
    assert can_access_task(engineer, own_task) is True
    assert can_access_task(engineer, other_task) is False

    # Admin and Auditor can view any task
    assert can_access_task(admin, other_task) is True
    assert can_access_task(auditor, other_task) is True
