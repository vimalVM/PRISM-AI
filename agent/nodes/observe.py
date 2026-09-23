"""Observation node for Sovereign AI Workbench agent.

Processes tool outputs, indexes newly produced files and artifacts, and summarizes results.
"""

from typing import Any, Dict, List
import uuid

from agent.state import AgentState, ArtifactRef
from backend.core.events import get_event_broker


def observe_node(state: AgentState) -> Dict[str, Any]:
    """Observe tool results and register newly created artifacts."""
    run_id = state.get("run_id", "adhoc")
    tool_results = state.get("tool_results", [])
    artifacts = list(state.get("generated_artifacts", []))

    # Inspect results for generated files/artifacts
    for res in tool_results:
        if res.status == "ok" and res.output and res.tool == "write_file":
            path = res.output.get("path")
            filename = res.output.get("filename", "output.txt")
            sha256 = res.output.get("sha256", "")
            if path and not any(a.path == path for a in artifacts):
                kind = "text"
                if filename.endswith(".docx"):
                    kind = "docx"
                elif filename.endswith(".xlsx"):
                    kind = "xlsx"
                elif filename.endswith(".pptx"):
                    kind = "pptx"
                elif filename.endswith(".py"):
                    kind = "code"

                artifacts.append(
                    ArtifactRef(
                        id=str(uuid.uuid4()),
                        kind=kind,
                        filename=filename,
                        path=path,
                        sha256=sha256,
                    )
                )

    broker = get_event_broker()
    broker.emit(
        run_id=run_id,
        event_type="node_started",
        node="observe",
        status="ok",
        summary=f"Observed {len(tool_results)} tool result(s), {len(artifacts)} artifact(s)",
    )

    return {
        "generated_artifacts": artifacts,
    }
