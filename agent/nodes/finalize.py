"""Finalize node for Sovereign AI Workbench agent.

Synthesizes final answer from verified tool results, updates DB task record,
logs run_finished audit record, and emits terminal streaming event.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict

from sqlalchemy import select

from agent.prompts import FINALIZE_PROMPT_TEMPLATE, WORKBENCH_SYSTEM_PROMPT
from agent.nodes.plan import get_active_llm_client
from agent.state import AgentState
from backend.core.audit import log_event
from backend.core.db import Task, get_session_factory
from backend.core.events import get_event_broker

logger = logging.getLogger("sovereign-workbench.agent.finalize")


def finalize_node(state: AgentState) -> Dict[str, Any]:
    """Finalize run: generate final answer, persist task completion, audit finish."""
    run_id = state.get("run_id", "adhoc")
    user_id = state.get("user_id", "unknown")
    user_role = state.get("user_role", "engineer")
    selected_model = state.get("selected_model", "qwen3.5:4b")
    user_request = state.get("user_request", "")
    tool_results = state.get("tool_results", [])
    artifacts = state.get("generated_artifacts", [])
    errors = state.get("errors", [])
    approval_status = state.get("approval_status", "NONE")
    retry_count = state.get("retry_count", 0)

    is_success = len(errors) == 0

    # Compose final answer
    final_answer = ""
    if not is_success:
        final_answer = f"Task execution failed.\n\nErrors encountered:\n" + "\n".join(f"- {e}" for e in errors)
    else:
        # Build synthesis from tool results
        results_summary_lines = []
        for r in tool_results:
            results_summary_lines.append(f"Tool '{r.tool}' (Status: {r.status}):")
            if r.output:
                for k, v in r.output.items():
                    if k == "content":
                        # Truncate content for synthesis prompt
                        results_summary_lines.append(f"  {k}: {str(v)[:1500]}")
                    else:
                        results_summary_lines.append(f"  {k}: {v}")
            if r.error:
                results_summary_lines.append(f"  error: {r.error}")

        results_summary = "\n".join(results_summary_lines) if results_summary_lines else "No tool steps were required."

        prompt = FINALIZE_PROMPT_TEMPLATE.format(
            user_request=user_request,
            tool_results_summary=results_summary,
        )

        client = get_active_llm_client()
        try:
            resp = client.generate(
                model=selected_model,
                prompt=prompt,
                system=WORKBENCH_SYSTEM_PROMPT,
            )
            final_answer = resp.get("response", "").strip()
        except Exception as exc:
            logger.warning(f"Synthesis call failed ({exc}); falling back to deterministic summary.")
            final_answer = f"Task completed successfully.\n\nTool Results:\n{results_summary}"

    # Update database record if persistent task exists
    try:
        factory = get_session_factory()
        with factory() as db:
            stmt = select(Task).where(Task.id == run_id)
            task_row = db.execute(stmt).scalar_one_or_none()
            if task_row:
                task_row.status = "completed" if is_success else "failed"
                task_row.finished_at = datetime.now(timezone.utc)
                task_row.retry_count = retry_count
                task_row.error = "; ".join(errors) if errors else None
                db.commit()
    except Exception as exc:
        logger.warning(f"Could not update task record in DB: {exc}")

    # Audit run finish
    log_event(
        event_type="run_finished",
        status="ok" if is_success else "failed",
        user_id=user_id,
        role=user_role,
        run_id=run_id,
        model=selected_model,
        details={
            "tool_calls_count": len(tool_results),
            "artifacts_count": len(artifacts),
            "approval_status": approval_status,
            "retry_count": retry_count,
            "errors_count": len(errors),
        },
    )

    # Emit terminal SSE event
    broker = get_event_broker()
    broker.emit(
        run_id=run_id,
        event_type="run_finished" if is_success else "error",
        node="finalize",
        status="ok" if is_success else "error",
        summary="Execution finished successfully." if is_success else f"Execution finished with errors ({len(errors)} error(s)).",
    )

    return {
        "final_answer": final_answer,
    }
