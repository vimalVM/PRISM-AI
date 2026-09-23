"""Review gate node for Sovereign AI Workbench agent.

Implements human-in-the-loop review policy from 02_DESIGN_DOC.md §6.3 and AGENTS.md rule 8:
If artifacts are generated or task risk is flagged, status is set to PENDING_REVIEW.
The agent cannot approve its own output (NEVER sets APPROVED).
"""

from typing import Any, Dict

from agent.state import AgentState
from backend.core.events import get_event_broker


def review_gate_node(state: AgentState) -> Dict[str, Any]:
    """Evaluate whether run deliverables require human confirmation."""
    run_id = state.get("run_id", "adhoc")
    risk = state.get("risk", "standard")
    artifacts = state.get("generated_artifacts", [])
    errors = state.get("errors", [])

    # If execution failed or errors exist, approval status remains NONE / REJECTED
    if errors:
        return {"approval_status": "NONE"}

    # Human review required if artifacts exist or risk is high
    requires_review = bool(artifacts) or risk == "high_impact"
    status = "PENDING_REVIEW" if requires_review else "NONE"

    if requires_review:
        broker = get_event_broker()
        broker.emit(
            run_id=run_id,
            event_type="review_required",
            node="review_gate",
            status="ok",
            summary=f"Deliverable review gate active: {len(artifacts)} artifact(s) require human authorization.",
        )

    return {
        "approval_status": status,
    }
