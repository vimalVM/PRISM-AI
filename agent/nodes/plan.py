"""Plan node for Sovereign AI Workbench agent.

Queries Qwen3.5 4B (or configured primary reasoning model) for a strict JSON
execution plan. Validates that every proposed step references an authorized tool
in the tool registry. Unknown tools are strictly rejected.
"""

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

from agent.prompts import (
    PLAN_PROMPT_TEMPLATE,
    PLAN_REPAIR_PROMPT,
    WORKBENCH_SYSTEM_PROMPT,
    format_tools_description,
)
from agent.state import AgentState, PlanStep
from backend.core.audit import log_event
from backend.core.events import get_event_broker
from models.ollama_client import OllamaClient
from tools.registry import get_tool_registry

logger = logging.getLogger("sovereign-workbench.agent.plan")

# Global hook for client injection during tests
_LLM_CLIENT_OVERRIDE: Optional[Any] = None


def set_llm_client_override(client: Optional[Any]) -> None:
    """Set or clear a custom LLM client for testing."""
    global _LLM_CLIENT_OVERRIDE
    _LLM_CLIENT_OVERRIDE = client


def get_active_llm_client() -> Any:
    """Get active LLM client (override or default OllamaClient)."""
    global _LLM_CLIENT_OVERRIDE
    if _LLM_CLIENT_OVERRIDE is not None:
        return _LLM_CLIENT_OVERRIDE
    return OllamaClient()


def _clean_json_text(text: str) -> str:
    """Strip markdown code fence blocks if returned by model."""
    stripped = text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped)
    if match:
        return match.group(1).strip()
    return stripped


def plan_node(state: AgentState) -> Dict[str, Any]:
    """Generate execution plan via LLM and validate proposed tools."""
    run_id = state.get("run_id", "adhoc")
    user_id = state.get("user_id", "unknown")
    user_role = state.get("user_role", "engineer")
    user_clearance = state.get("user_clearance", "INTERNAL")
    user_request = state.get("user_request", "")
    selected_model = state.get("selected_model", "qwen3.5:4b")
    files = state.get("uploaded_files", [])
    errors = list(state.get("errors", []))

    registry = get_tool_registry()
    available_tools = []
    for t in registry.list_tools():
        args_schema_str = "{}"
        if t.args_schema:
            try:
                args_schema_str = json.dumps(t.args_schema.model_json_schema().get("properties", {}))
            except Exception:
                pass
        available_tools.append({
            "name": t.name,
            "description": t.description,
            "args_schema": args_schema_str,
        })

    tools_desc = format_tools_description(available_tools)
    files_summary = ", ".join(f"{f.path} ({f.modality})" for f in files) if files else "None"

    prompt = PLAN_PROMPT_TEMPLATE.format(
        tools_description=tools_desc,
        user_request=user_request,
        run_id=run_id,
        user_role=user_role,
        user_clearance=user_clearance,
        files_summary=files_summary,
    )

    client = get_active_llm_client()
    raw_response = ""
    try:
        resp = client.generate(
            model=selected_model,
            prompt=prompt,
            system=WORKBENCH_SYSTEM_PROMPT,
        )
        raw_response = resp.get("response", "")
    except Exception as exc:
        err_msg = f"Model call failed during planning: {exc}"
        logger.error(err_msg)
        return {
            "plan": [],
            "errors": errors + [err_msg],
        }

    # Parse JSON
    cleaned_json = _clean_json_text(raw_response)
    plan_data = None
    try:
        plan_data = json.loads(cleaned_json)
    except json.JSONDecodeError as jde:
        # One attempt at repair prompt
        logger.warning(f"Plan JSON malformed: {jde}. Attempting repair prompt.")
        repair_prompt = PLAN_REPAIR_PROMPT.format(
            error=str(jde),
            previous_response=raw_response[:500],
        )
        try:
            repair_resp = client.generate(
                model=selected_model,
                prompt=repair_prompt,
                system=WORKBENCH_SYSTEM_PROMPT,
            )
            repaired_text = _clean_json_text(repair_resp.get("response", ""))
            plan_data = json.loads(repaired_text)
        except Exception as repair_exc:
            err_msg = f"Failed to parse plan JSON after repair: {repair_exc}"
            return {
                "plan": [],
                "errors": errors + [err_msg],
            }

    raw_steps = plan_data.get("steps", []) if isinstance(plan_data, dict) else []
    validated_steps: List[PlanStep] = []

    # Validate tool names against ToolRegistry
    for idx, s in enumerate(raw_steps):
        tool_name = s.get("tool") if isinstance(s, dict) else None
        if not tool_name or not registry.is_registered(tool_name):
            err_msg = f"Plan proposes unknown or unregistered tool '{tool_name}' at step {idx + 1}"
            logger.warning(err_msg)
            return {
                "plan": [],
                "errors": errors + [err_msg],
            }

        validated_steps.append(
            PlanStep(
                step_id=s.get("step_id", idx + 1),
                tool=tool_name,
                args=s.get("args", {}),
                reason=s.get("reason", ""),
            )
        )

    # Group vision steps contiguously to minimize model swaps (02_DESIGN_DOC §6)
    from agent.router import ModelSwapManager
    optimized_steps = ModelSwapManager.group_plan_steps(validated_steps)
    for i, step in enumerate(optimized_steps):
        step.step_id = i + 1

    # Emit planning event
    broker = get_event_broker()
    broker.emit(
        run_id=run_id,
        event_type="node_started",
        node="plan",
        model=selected_model,
        status="ok",
        summary=f"Generated plan with {len(optimized_steps)} step(s)",
    )

    return {
        "plan": optimized_steps,
        "errors": errors,
    }
