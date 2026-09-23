"""Integration tests for the LangGraph agent state machine.

Tests end-to-end flow with a fake Ollama client:
- Normal execution: intake -> plan -> execute -> observe -> validate -> finalize
- Unknown tool in plan rejected
- Bounded retries enforced on repeated failure (MAX_AGENT_RETRIES)
- Audit log records every model route and tool call
"""

import json
from pathlib import Path
import pytest
from sqlalchemy import select

from agent.graph import run_agent
from agent.nodes.plan import set_llm_client_override
from backend.core.audit import verify_chain
from backend.core.config import get_settings
from backend.core.db import AuditLog, Task, TaskEvent, User, get_session_factory
from tools.files import WriteFileArgs, write_file
from tools.registry import ToolContext


class MockOllamaClient:
    """Configurable mock Ollama client returning predetermined responses."""

    def __init__(self, plan_json: str, finalize_text: str = "Verified summary."):
        self.plan_json = plan_json
        self.finalize_text = finalize_text
        self.call_count = 0

    def generate(self, model: str, prompt: str, system: str = None, **kwargs):
        self.call_count += 1
        if "Generate a concise, step-by-step execution plan" in prompt or "Your previous plan output" in prompt:
            return {"response": self.plan_json}
        # Finalize / summary prompt
        return {"response": self.finalize_text}


@pytest.fixture(autouse=True)
def cleanup_mock():
    yield
    set_llm_client_override(None)


@pytest.fixture
def setup_test_file(tmp_path, monkeypatch):
    """Set up input/output directories and write a sample text file."""
    incoming = tmp_path / "incoming"
    outputs = tmp_path / "outputs"
    incoming.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(get_settings(), "ALLOWED_INPUT_DIRS", str(incoming))
    monkeypatch.setattr(get_settings(), "ALLOWED_OUTPUT_DIRS", str(outputs))

    test_doc = incoming / "sample_sop.txt"
    test_doc.write_text("SOP-001: Pressure safety valves must be inspected annually.")
    return test_doc


def test_agent_normal_flow_read_and_summarize(setup_test_file):
    test_doc = setup_test_file

    plan = {
        "steps": [
            {
                "step_id": 1,
                "tool": "read_file",
                "args": {"path": str(test_doc)},
                "reason": "Read the standard operating procedure document",
            }
        ]
    }
    mock_client = MockOllamaClient(
        plan_json=json.dumps(plan),
        finalize_text="FACT: SOP-001 mandates annual pressure safety valve inspection.",
    )
    set_llm_client_override(mock_client)

    run_id = "test_run_normal_001"
    user_id = "eng_user_01"

    factory = get_session_factory()
    with factory() as db:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            user = User(
                id=user_id,
                username="eng_user_graph_test",
                password_hash="mock_hash_argon2id",
                role="engineer",
                clearance=1,
                active=True,
            )
            db.add(user)
            db.commit()

        task = db.execute(select(Task).where(Task.id == run_id)).scalar_one_or_none()
        if not task:
            task = Task(
                id=run_id,
                owner_id=user_id,
                request_text="Read sample_sop.txt and summarize the inspection interval",
                status="pending",
            )
            db.add(task)
            db.commit()

    state = run_agent(
        user_request="Read sample_sop.txt and summarize the inspection interval",
        user_id=user_id,
        user_role="engineer",
        user_clearance="INTERNAL",
        run_id=run_id,
    )

    # 1. State assertions
    assert state["retry_count"] == 0
    assert len(state["errors"]) == 0
    assert len(state["tool_results"]) == 1
    assert state["tool_results"][0].tool == "read_file"
    assert state["tool_results"][0].status == "ok"
    assert "Pressure safety valves" in state["tool_results"][0].output["content"]
    assert "annual" in state["final_answer"].lower()

    # 2. Verify TaskEvent persistence in DB
    factory = get_session_factory()
    with factory() as db:
        events = db.execute(
            select(TaskEvent).where(TaskEvent.task_id == run_id).order_by(TaskEvent.seq.asc())
        ).scalars().all()
        event_types = [e.type for e in events]

        assert "run_started" in event_types
        assert "route_selected" in event_types
        assert "tool_call" in event_types
        assert "validation" in event_types
        assert "run_finished" in event_types

        # 3. Verify AuditLog entries
        audit_rows = db.execute(
            select(AuditLog).where(AuditLog.run_id == run_id)
        ).scalars().all()
        audit_types = [a.event_type for a in audit_rows]
        assert "run_started" in audit_types
        assert "tool_call" in audit_types
        assert "run_finished" in audit_types

        # 4. Verify audit hash chain
        valid, err = verify_chain(db)
        assert valid, f"Audit chain verification failed: {err}"


def test_agent_unknown_tool_rejection_and_bounded_retry(setup_test_file):
    """Plan proposing an unknown tool must be rejected and stop after MAX_AGENT_RETRIES."""
    invalid_plan = {
        "steps": [
            {
                "step_id": 1,
                "tool": "unauthorized_remote_fetch",
                "args": {"url": "http://cloud.example.com"},
                "reason": "Attempting external request",
            }
        ]
    }
    mock_client = MockOllamaClient(plan_json=json.dumps(invalid_plan))
    set_llm_client_override(mock_client)

    run_id = "test_run_unknown_tool_002"
    settings = get_settings()

    state = run_agent(
        user_request="Fetch external info",
        user_id="eng_user_01",
        user_role="engineer",
        user_clearance="INTERNAL",
        run_id=run_id,
    )

    # Must halt after MAX_AGENT_RETRIES (3)
    assert state["retry_count"] >= settings.MAX_AGENT_RETRIES
    assert len(state["errors"]) > 0
    assert any("Bounded retry limit reached" in e for e in state["errors"])
    assert "failed" in state["final_answer"].lower()


def test_agent_bounded_retries_on_tool_failure(tmp_path, monkeypatch):
    """Tool failure should trigger revise loop and halt at MAX_AGENT_RETRIES."""
    incoming = tmp_path / "incoming"
    outputs = tmp_path / "outputs"
    incoming.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(get_settings(), "ALLOWED_INPUT_DIRS", str(incoming))
    monkeypatch.setattr(get_settings(), "ALLOWED_OUTPUT_DIRS", str(outputs))

    # Read non-existent file will fail
    plan = {
        "steps": [
            {
                "step_id": 1,
                "tool": "read_file",
                "args": {"path": str(incoming / "does_not_exist.txt")},
                "reason": "Reading missing file",
            }
        ]
    }
    mock_client = MockOllamaClient(plan_json=json.dumps(plan))
    set_llm_client_override(mock_client)

    run_id = "test_run_tool_fail_003"
    settings = get_settings()

    state = run_agent(
        user_request="Read non-existent file",
        user_id="eng_user_01",
        user_role="engineer",
        user_clearance="INTERNAL",
        run_id=run_id,
    )

    assert state["retry_count"] >= settings.MAX_AGENT_RETRIES
    assert len(state["errors"]) > 0
    assert "failed" in state["final_answer"].lower()
