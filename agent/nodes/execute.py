"""Execution node for Sovereign AI Workbench agent.

Executes plan steps sequentially through the audited tool registry.
Enforces step limits (MAX_TOOL_STEPS) and captures structured ToolResult records.
"""

import time
from typing import Any, Dict, List
from pydantic import BaseModel

from agent.state import AgentState, ToolResult
from backend.core.config import get_settings
from backend.core.events import get_event_broker
from tools.registry import ToolContext, get_tool_registry


def execute_node(state: AgentState) -> Dict[str, Any]:
    """Execute steps in the plan using the central ToolRegistry."""
    run_id = state.get("run_id", "adhoc")
    user_id = state.get("user_id", "unknown")
    user_role = state.get("user_role", "engineer")
    user_clearance = state.get("user_clearance", "INTERNAL")
    selected_model = state.get("selected_model", "qwen3.5:4b")
    plan = state.get("plan", [])
    step_count = state.get("step_count", 0)
    existing_results = list(state.get("tool_results", []))
    errors = list(state.get("errors", []))

    settings = get_settings()
    max_steps = settings.MAX_TOOL_STEPS
    registry = get_tool_registry()
    broker = get_event_broker()

    ctx = ToolContext(
        user_id=user_id,
        role=user_role,
        clearance=user_clearance,
        run_id=run_id,
    )

    for step in plan:
        if step_count >= max_steps:
            err_msg = f"Execution halted: reached MAX_TOOL_STEPS limit ({max_steps})"
            errors.append(err_msg)
            broker.emit(
                run_id=run_id,
                event_type="error",
                node="execute",
                status="error",
                summary=err_msg,
            )
            break

        step_count += 1
        t_start = time.perf_counter()

        try:
            raw_res = registry.execute(step.tool, step.args, ctx)
            duration_ms = int((time.perf_counter() - t_start) * 1000)

            # Convert result to dict
            out_dict: Dict[str, Any] = {}
            if isinstance(raw_res, BaseModel):
                out_dict = raw_res.model_dump()
            elif isinstance(raw_res, dict):
                out_dict = raw_res

            # Summary for SSE
            summary_parts = []
            if "filename" in out_dict:
                summary_parts.append(f"file: {out_dict['filename']}")
            if "size_bytes" in out_dict:
                summary_parts.append(f"size: {out_dict['size_bytes']}B")
            summary_str = f"Tool '{step.tool}' completed ({', '.join(summary_parts)})" if summary_parts else f"Tool '{step.tool}' completed"

            broker.emit(
                run_id=run_id,
                event_type="tool_call",
                node="execute",
                tool=step.tool,
                model=selected_model,
                status="ok",
                duration_ms=duration_ms,
                summary=summary_str,
            )

            existing_results.append(
                ToolResult(
                    step_id=step.step_id,
                    tool=step.tool,
                    status="ok",
                    output=out_dict,
                    duration_ms=duration_ms,
                )
            )

        except Exception as exc:
            duration_ms = int((time.perf_counter() - t_start) * 1000)
            err_text = str(exc)
            errors.append(f"Step {step.step_id} ({step.tool}) failed: {err_text}")

            broker.emit(
                run_id=run_id,
                event_type="tool_call",
                node="execute",
                tool=step.tool,
                model=selected_model,
                status="error",
                duration_ms=duration_ms,
                summary=f"Tool '{step.tool}' failed: {err_text[:120]}",
            )

            existing_results.append(
                ToolResult(
                    step_id=step.step_id,
                    tool=step.tool,
                    status="error",
                    error=err_text,
                    duration_ms=duration_ms,
                )
            )
            # Break further plan execution on step error so validation/revise can intervene
            break

    return {
        "tool_results": existing_results,
        "step_count": step_count,
        "errors": errors,
    }
