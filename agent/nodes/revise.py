"""Revision node for Sovereign AI Workbench agent.

Enforces bounded retries (MAX_AGENT_RETRIES=3). Builds concise feedback
for re-planning or triggers graceful terminal halt.
"""

from typing import Any, Dict

from agent.state import AgentState
from backend.core.audit import log_event
from backend.core.config import get_settings
from backend.core.events import get_event_broker


def revise_node(state: AgentState) -> Dict[str, Any]:
    """Increment retry count and decide whether to re-plan or halt."""
    run_id = state.get("run_id", "adhoc")
    user_id = state.get("user_id", "unknown")
    user_role = state.get("user_role", "engineer")
    current_retry = state.get("retry_count", 0) + 1
    errors = list(state.get("errors", []))
    validation_results = state.get("validation_results", [])

    settings = get_settings()
    max_retries = settings.MAX_AGENT_RETRIES
    broker = get_event_broker()

    failed_reasons = [vr.detail for vr in validation_results if not vr.passed and vr.detail]
    reason_str = "; ".join(failed_reasons) if failed_reasons else "Validation check failed"

    log_event(
        event_type="retry",
        status="retry" if current_retry < max_retries else "exhausted",
        user_id=user_id,
        role=user_role,
        run_id=run_id,
        details={
            "retry_count": current_retry,
            "max_retries": max_retries,
            "reason": reason_str[:250],
        },
    )

    if current_retry >= max_retries:
        terminal_msg = f"Bounded retry limit reached ({max_retries} retries). Halting execution."
        errors.append(terminal_msg)

        broker.emit(
            run_id=run_id,
            event_type="retry",
            node="revise",
            status="error",
            summary=f"Retry limit exhausted ({current_retry}/{max_retries}): {terminal_msg}",
        )

        return {
            "retry_count": current_retry,
            "errors": errors,
        }

    broker.emit(
        run_id=run_id,
        event_type="retry",
        node="revise",
        status="ok",
        summary=f"Triggering revision {current_retry}/{max_retries} due to: {reason_str[:120]}",
    )

    # Clear current plan and append revision feedback to user request context
    revision_feedback = f"[SYSTEM REVISION FEEDBACK - RETRY {current_retry}]: Previous attempt failed: {reason_str}. Re-plan carefully."
    return {
        "retry_count": current_retry,
        "plan": [],
        "tool_results": [],
        "user_request": f"{state.get('user_request', '')}\n\n{revision_feedback}",
        "errors": [],  # Clear transient errors for new attempt
    }
