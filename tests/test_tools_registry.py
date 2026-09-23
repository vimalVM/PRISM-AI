"""Unit tests for the tool registry and @audited_tool decorator.

Tests role authorization checks, argument validation, execution, and audit logging.
"""

from typing import Dict
from pydantic import BaseModel, Field
import pytest

from backend.core.audit import verify_chain
from backend.core.db import get_session_factory
from backend.core.paths import AccessDenied
from tools.registry import ToolContext, ToolRegistry, audited_tool, get_tool_registry


class SampleToolArgs(BaseModel):
    name: str = Field(..., min_length=2)
    count: int = Field(default=1, ge=1)


class SampleToolResult(BaseModel):
    greeting: str
    items_found: int


@audited_tool(
    name="sample_restricted_tool",
    needs_role=["admin", "reviewer"],
    description="Tool restricted to admin and reviewer roles.",
)
def sample_restricted_tool(args: SampleToolArgs, ctx: ToolContext) -> SampleToolResult:
    return SampleToolResult(greeting=f"Hello {args.name}", items_found=args.count)


def test_tool_registration():
    reg = get_tool_registry()
    assert reg.is_registered("sample_restricted_tool")
    tool_def = reg.get("sample_restricted_tool")
    assert tool_def is not None
    assert "admin" in tool_def.needs_role


def test_tool_role_authorization():
    reg = get_tool_registry()

    # Engineer role should be denied
    eng_ctx = ToolContext(user_id="user_eng", role="engineer", run_id="run_101")
    with pytest.raises(AccessDenied, match="not authorized"):
        reg.execute("sample_restricted_tool", {"name": "Test"}, eng_ctx)

    # Admin role should succeed
    admin_ctx = ToolContext(user_id="user_admin", role="admin", run_id="run_101")
    res = reg.execute("sample_restricted_tool", {"name": "Test", "count": 3}, admin_ctx)
    assert res.greeting == "Hello Test"
    assert res.items_found == 3


def test_tool_argument_validation():
    reg = get_tool_registry()
    admin_ctx = ToolContext(user_id="user_admin", role="admin", run_id="run_102")

    # Name is too short (min_length=2)
    with pytest.raises(Exception):
        reg.execute("sample_restricted_tool", {"name": "X"}, admin_ctx)


def test_unknown_tool_rejection():
    reg = get_tool_registry()
    ctx = ToolContext(user_id="user_admin", role="admin", run_id="run_103")

    assert not reg.is_registered("non_existent_tool_123")
    with pytest.raises(ValueError, match="is not registered"):
        reg.execute("non_existent_tool_123", {}, ctx)


def test_audit_chain_validity_after_tool_calls():
    factory = get_session_factory()
    with factory() as db:
        valid, err = verify_chain(db)
        assert valid, f"Audit chain verification failed: {err}"
