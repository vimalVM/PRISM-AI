"""Validation node for Sovereign AI Workbench agent.

Evaluates execution outputs against deterministic safety and completion rules.
Detects errors to trigger bounded revision cycles.
"""

from typing import Any, Dict, List

from agent.state import AgentState, ValidationResult
from backend.core.events import get_event_broker


def validate_node(state: AgentState) -> Dict[str, Any]:
    """Validate task execution integrity and output criteria."""
    run_id = state.get("run_id", "adhoc")
    errors = state.get("errors", [])
    tool_results = state.get("tool_results", [])
    validation_results: List[ValidationResult] = []

    # Check 1: General error accumulation
    if errors:
        for err in errors:
            validation_results.append(
                ValidationResult(
                    rule="no_execution_errors",
                    passed=False,
                    detail=err,
                )
            )
    else:
        validation_results.append(
            ValidationResult(
                rule="no_execution_errors",
                passed=True,
                detail="All execution steps completed without error.",
            )
        )

    # Check 2: Tool execution status
    failed_tools = [r for r in tool_results if r.status == "error"]
    if failed_tools:
        for ft in failed_tools:
            validation_results.append(
                ValidationResult(
                    rule=f"tool_status_{ft.tool}",
                    passed=False,
                    detail=f"Step {ft.step_id} failed: {ft.error}",
                )
            )
    else:
        validation_results.append(
            ValidationResult(
                rule="all_tools_succeeded",
                passed=True,
                detail=f"All {len(tool_results)} tool calls succeeded.",
            )
        )

    all_passed = all(vr.passed for vr in validation_results)
    status_str = "ok" if all_passed else "fail"

    broker = get_event_broker()
    broker.emit(
        run_id=run_id,
        event_type="validation",
        node="validate",
        status=status_str,
        summary=f"Validation {'passed' if all_passed else 'failed'} ({len(validation_results)} checks evaluated)",
    )

    return {
        "validation_results": validation_results,
    }
