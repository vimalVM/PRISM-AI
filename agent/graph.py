"""LangGraph StateGraph workflow definition for Sovereign AI Workbench.

Implements the bounded agent state machine from 02_DESIGN_DOC.md §6.1:
INTAKE -> PLAN -> EXECUTE -> OBSERVE -> VALIDATE
VALIDATE -> (success) -> REVIEW_GATE -> FINALIZE -> END
VALIDATE -> (failure) -> REVISE
REVISE   -> (retry_count < MAX_AGENT_RETRIES) -> PLAN
REVISE   -> (retry_count >= MAX_AGENT_RETRIES) -> FINALIZE -> END
"""

from typing import Any, Dict, List, Literal, Optional
import uuid

from langgraph.graph import END, START, StateGraph

from agent.nodes.execute import execute_node
from agent.nodes.finalize import finalize_node
from agent.nodes.intake import intake_node
from agent.nodes.observe import observe_node
from agent.nodes.plan import plan_node
from agent.nodes.review_gate import review_gate_node
from agent.nodes.revise import revise_node
from agent.nodes.validate import validate_node
from agent.state import AgentState, FileRef
from backend.core.config import get_settings


def route_after_validate(state: AgentState) -> Literal["review_gate", "revise"]:
    """Conditional edge after validation node."""
    val_results = state.get("validation_results", [])
    errors = state.get("errors", [])

    if errors or any(not vr.passed for vr in val_results):
        return "revise"
    return "review_gate"


def route_after_revise(state: AgentState) -> Literal["plan", "finalize"]:
    """Conditional edge after revise node enforcing bounded retries."""
    settings = get_settings()
    retry_count = state.get("retry_count", 0)
    if retry_count >= settings.MAX_AGENT_RETRIES:
        return "finalize"
    return "plan"


def build_workbench_graph() -> StateGraph:
    """Construct and configure the LangGraph StateGraph."""
    graph = StateGraph(AgentState)

    # Add Nodes
    graph.add_node("intake", intake_node)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("observe", observe_node)
    graph.add_node("validate", validate_node)
    graph.add_node("revise", revise_node)
    graph.add_node("review_gate", review_gate_node)
    graph.add_node("finalize", finalize_node)

    # Add Edges
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "plan")
    graph.add_edge("plan", "execute")
    graph.add_edge("execute", "observe")
    graph.add_edge("observe", "validate")

    # Conditional Branching from Validate
    graph.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "review_gate": "review_gate",
            "revise": "revise",
        },
    )

    # Review gate proceeds directly to finalize
    graph.add_edge("review_gate", "finalize")

    # Conditional Branching from Revise (bounded loop back to plan or terminal finalize)
    graph.add_conditional_edges(
        "revise",
        route_after_revise,
        {
            "plan": "plan",
            "finalize": "finalize",
        },
    )

    graph.add_edge("finalize", END)

    return graph


def compile_workbench_graph():
    """Compile the state graph into an executable runnable."""
    return build_workbench_graph().compile()


def run_agent(
    user_request: str,
    user_id: str = "anon",
    user_role: str = "engineer",
    user_clearance: str = "INTERNAL",
    run_id: Optional[str] = None,
    uploaded_files: Optional[List[FileRef]] = None,
    task_type: Optional[str] = "general",
) -> AgentState:
    """Convenience helper to run the compiled workbench agent to completion."""
    app = compile_workbench_graph()
    actual_run_id = run_id or str(uuid.uuid4())

    initial_state: AgentState = {
        "run_id": actual_run_id,
        "user_id": user_id,
        "user_role": user_role,
        "user_clearance": user_clearance,
        "user_request": user_request,
        "task_type": task_type or "general",
        "uploaded_files": uploaded_files or [],
        "retry_count": 0,
        "step_count": 0,
        "errors": [],
        "tool_results": [],
        "generated_artifacts": [],
        "validation_results": [],
        "approval_status": "NONE",
    }

    final_state = app.invoke(initial_state)
    return final_state


# Alias for evaluation harness
create_agent_graph = build_workbench_graph
