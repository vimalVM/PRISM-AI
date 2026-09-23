"""Intake node for Sovereign AI Workbench agent.

Classifies incoming request, identifies uploaded files, establishes baseline model routing,
records run_started in audit log and emits initial streaming event.
"""

from typing import Any, Dict

from agent.state import AgentState
from backend.core.audit import log_event
from backend.core.events import get_event_broker
from models.registry import get_registry, resolve_route


def intake_node(state: AgentState) -> Dict[str, Any]:
    """Intake node: classifies task, assigns model, and audits startup."""
    run_id = state.get("run_id", "adhoc")
    user_id = state.get("user_id", "unknown")
    user_role = state.get("user_role", "engineer")
    user_request = state.get("user_request", "")
    files = state.get("uploaded_files", [])

    # Derive modalities
    modalities = {f.modality for f in files} if files else set()
    facts: Dict[str, Any] = {
        "user_request": user_request,
        "modality": modalities if modalities else "text",
    }

    # Resolve initial route via registry
    registry = get_registry()
    route_plan = resolve_route(facts, registry=registry)

    selected_model = route_plan.selected_model
    route_reason = route_plan.reason

    # Audit run start
    log_event(
        event_type="run_started",
        status="ok",
        user_id=user_id,
        role=user_role,
        run_id=run_id,
        model=selected_model,
        file_ids=[f.id for f in files] if files else None,
        details={
            "task_type": state.get("task_type", "general"),
            "model_route": route_plan.rule_name,
            "route_reason": route_reason,
        },
    )

    # Emit streaming event
    broker = get_event_broker()
    broker.emit(
        run_id=run_id,
        event_type="run_started",
        node="intake",
        model=selected_model,
        status="ok",
        summary=f"Task initiated with model '{selected_model}' ({route_reason})",
    )

    broker.emit(
        run_id=run_id,
        event_type="route_selected",
        node="intake",
        model=selected_model,
        status="ok",
        summary=f"Model route '{route_plan.rule_name}' assigned: {route_reason}",
    )

    return {
        "selected_model": selected_model,
        "route_reason": route_reason,
        "step_count": 0,
        "retry_count": state.get("retry_count", 0),
        "errors": [],
    }
