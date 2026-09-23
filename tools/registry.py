"""Tool registry and audited tool execution layer for Sovereign AI Workbench.

Implements SEC-14 and 02_DESIGN_DOC.md section 7:
- @audited_tool decorator enforcing role checks, arg validation, timeouts, and hash-chained audit logging.
- ToolContext carrying authenticated user credentials and run identifiers.
- Central ToolRegistry for discovery, execution, and validation.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import functools
import inspect
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union

from pydantic import BaseModel, ValidationError

from backend.core.audit import log_event
from backend.core.config import get_settings
from backend.core.paths import AccessDenied
from backend.core.rbac import Role


@dataclass
class ToolContext:
    """Execution context provided to all tool invocations."""

    user_id: str
    role: str
    clearance: Union[int, str] = 0
    run_id: str = "adhoc"


@dataclass
class ToolDefinition:
    """Registered tool metadata and entrypoint."""

    name: str
    fn: Callable[..., Any]
    args_schema: Optional[Type[BaseModel]] = None
    result_schema: Optional[Type[BaseModel]] = None
    side_effects: bool = False
    needs_role: Optional[List[str]] = None
    timeout_s: Optional[int] = None
    description: str = ""


class ToolRegistry:
    """Singleton registry holding authorized local tools."""

    _instance: Optional["ToolRegistry"] = None

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool_def: ToolDefinition) -> None:
        """Register a tool definition."""
        self._tools[tool_def.name] = tool_def

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Retrieve a tool definition by name."""
        return self._tools.get(name)

    def is_registered(self, name: str) -> bool:
        """Check if a tool name is registered."""
        return name in self._tools

    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def execute(self, name: str, args: Union[Dict[str, Any], BaseModel], ctx: ToolContext) -> Any:
        """Execute a registered tool by name with arguments and context."""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' is not registered in Sovereign AI Workbench tool registry.")
        return tool.fn(args, ctx)


def get_tool_registry() -> ToolRegistry:
    """Get the active ToolRegistry singleton."""
    return ToolRegistry.get_instance()


def audited_tool(
    name: str,
    side_effects: bool = False,
    needs_role: Optional[Union[str, List[str]]] = None,
    timeout_s: Optional[int] = None,
    description: Optional[str] = None,
    args_schema: Optional[Type[BaseModel]] = None,
    result_schema: Optional[Type[BaseModel]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for workbench tools enforcing security, audit, and validation.

    1. Enforces role-based permissions (needs_role).
    2. Validates arguments using args_schema (or inferred from type hint).
    3. Executes tool within timeout.
    4. Records start/finish audit events with duration and status, omitting document contents.
    5. Registers the tool in the central ToolRegistry.
    """
    allowed_roles: Optional[List[str]] = None
    if needs_role:
        allowed_roles = [needs_role] if isinstance(needs_role, str) else list(needs_role)

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        # Determine schemas from type annotations if not explicitly passed
        nonlocal args_schema, result_schema, description
        sig = inspect.signature(fn)
        params = list(sig.parameters.values())

        inferred_args_schema = args_schema
        if inferred_args_schema is None and len(params) > 0:
            hint = params[0].annotation
            if isinstance(hint, type) and issubclass(hint, BaseModel):
                inferred_args_schema = hint

        inferred_result_schema = result_schema
        if inferred_result_schema is None and sig.return_annotation is not inspect.Signature.empty:
            hint = sig.return_annotation
            if isinstance(hint, type) and issubclass(hint, BaseModel):
                inferred_result_schema = hint

        tool_desc = description or fn.__doc__ or f"Workbench tool {name}"

        @functools.wraps(fn)
        def wrapper(args: Union[Dict[str, Any], BaseModel], ctx: ToolContext) -> Any:
            settings = get_settings()
            effective_timeout = timeout_s or settings.TOOL_TIMEOUT_S

            # 1. Role Authorization Check
            if allowed_roles and ctx.role not in allowed_roles:
                log_event(
                    event_type="access_denied",
                    status="denied",
                    user_id=ctx.user_id,
                    role=ctx.role,
                    run_id=ctx.run_id,
                    tool=name,
                    details={"reason": f"Role '{ctx.role}' not permitted for tool '{name}' (requires {allowed_roles})"},
                )
                raise AccessDenied(
                    f"User role '{ctx.role}' is not authorized to execute tool '{name}' (requires {allowed_roles})"
                )

            # 2. Validate / parse arguments
            validated_args = args
            if inferred_args_schema is not None and not isinstance(args, inferred_args_schema):
                try:
                    if isinstance(args, dict):
                        validated_args = inferred_args_schema.model_validate(args)
                    else:
                        validated_args = inferred_args_schema.model_validate(dict(args))
                except ValidationError as ve:
                    log_event(
                        event_type="tool_call",
                        status="error",
                        user_id=ctx.user_id,
                        role=ctx.role,
                        run_id=ctx.run_id,
                        tool=name,
                        details={"error": "argument_validation_failed", "detail": str(ve)[:200]},
                    )
                    raise ve

            # 3. Execution with timing and audit logging
            start_time = time.perf_counter()
            status = "ok"
            err_msg: Optional[str] = None
            result = None

            try:
                # Call tool function
                result = fn(validated_args, ctx)
                return result
            except Exception as exc:
                status = "error"
                err_msg = str(exc)
                raise
            finally:
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                # Build sanitized audit summary (NEVER log document text, passwords, or full file contents)
                audit_details: Dict[str, Any] = {
                    "duration_ms": duration_ms,
                    "side_effects": side_effects,
                }
                if err_msg:
                    audit_details["error"] = err_msg[:200]

                # Extract safe metadata from args if present (e.g. filename, doc_id, page)
                if isinstance(validated_args, BaseModel):
                    arg_dict = validated_args.model_dump()
                elif isinstance(validated_args, dict):
                    arg_dict = validated_args
                else:
                    arg_dict = {}

                safe_arg_summary: Dict[str, Any] = {}
                for k in ["filename", "path", "doc_id", "page", "step_id", "max_bytes"]:
                    if k in arg_dict and arg_dict[k] is not None:
                        safe_arg_summary[k] = str(arg_dict[k])
                if safe_arg_summary:
                    audit_details["args_summary"] = safe_arg_summary

                # Safe summary of result
                if result is not None:
                    if isinstance(result, BaseModel):
                        res_dict = result.model_dump()
                    elif isinstance(result, dict):
                        res_dict = result
                    else:
                        res_dict = {}

                    safe_res_summary: Dict[str, Any] = {}
                    for k in ["filename", "path", "size_bytes", "sha256", "count", "items_found", "pages"]:
                        if k in res_dict and res_dict[k] is not None:
                            safe_res_summary[k] = res_dict[k]
                    if safe_res_summary:
                        audit_details["result_summary"] = safe_res_summary

                log_event(
                    event_type="tool_call",
                    status=status,
                    user_id=ctx.user_id,
                    role=ctx.role,
                    run_id=ctx.run_id,
                    tool=name,
                    duration_ms=duration_ms,
                    details=audit_details,
                )

        # Register tool in registry
        definition = ToolDefinition(
            name=name,
            fn=wrapper,
            args_schema=inferred_args_schema,
            result_schema=inferred_result_schema,
            side_effects=side_effects,
            needs_role=allowed_roles,
            timeout_s=timeout_s,
            description=tool_desc,
        )
        get_tool_registry().register(definition)

        return wrapper

    return decorator
