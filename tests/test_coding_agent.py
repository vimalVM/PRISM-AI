"""Integration tests for the Coding Agent loop and Demo B workflow.

Tests 02_DESIGN_DOC.md §11 and 04_ANTIGRAVITY_BUILD_PLAN.md Phase 8:
- Demo B: A coding task passes tests in the sandbox and returns a code package.
- A failing first attempt triggers exactly one bounded correction cycle.
- Runaway failure halts at MAX_AGENT_RETRIES.
"""

import json
from pathlib import Path
import pytest
from sqlalchemy import select

from agent.coding import package_code_deliverable
from agent.graph import run_agent
from agent.nodes.plan import set_llm_client_override
from backend.core.config import get_settings
from backend.core.db import Task, User, get_session_factory
from tools.registry import ToolContext
from tools.sandbox import (
    RunCodeArgs,
    RunCodeResult,
    run_code,
    set_sandbox_runner_override,
)


class MockCodingLLMClient:
    """Mock LLM simulating first-attempt failure followed by successful correction."""

    def __init__(self, plan_success: str, plan_retry: str = None, finalize_summary: str = "Code verified."):
        self.plan_success = plan_success
        self.plan_retry = plan_retry or plan_success
        self.finalize_summary = finalize_summary
        self.call_count = 0

    def generate(self, model: str, prompt: str, system: str = None, **kwargs):
        self.call_count += 1
        if self.call_count == 1:
            return {"response": self.plan_retry}
        elif self.call_count == 2:
            return {"response": self.plan_success}
        return {"response": self.finalize_summary}


@pytest.fixture(autouse=True)
def cleanup():
    yield
    set_llm_client_override(None)
    set_sandbox_runner_override(None)


def test_demo_b_coding_workflow_success(tmp_path, monkeypatch):
    """Demo B: A coding task generates code + tests, executes in sandbox, passes, and packages deliverable."""
    outputs = tmp_path / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(get_settings(), "ALLOWED_OUTPUT_DIRS", str(outputs))

    # Mock successful sandbox run
    def mock_sandbox_success(args, ctx, warnings):
        # Emulate writing verified files and returning 0 exit code
        pkg = package_code_deliverable(
            run_id=ctx.run_id,
            files={
                "src/solution.py": args.code or "def valve_flow(): return 100\n",
                "tests/test_solution.py": args.tests or "def test_valve(): assert True\n",
            },
            exit_code=0,
            test_summary="1 passed in 0.05s",
            output_base_dir=str(outputs),
        )
        return RunCodeResult(
            exit_code=0,
            stdout="1 passed in 0.05s",
            stderr="",
            duration_ms=50,
            status="passed",
            security_warnings=warnings,
            files_created=["src/solution.py", "tests/test_solution.py", "RESULT.txt"],
        )

    set_sandbox_runner_override(mock_sandbox_success)

    plan = {
        "steps": [
            {
                "step_id": 1,
                "tool": "run_code",
                "args": {
                    "code": "def valve_flow(dp: float, kv: float) -> float:\n    import math\n    return kv * math.sqrt(dp)\n",
                    "tests": "from solution import valve_flow\ndef test_flow():\n    assert valve_flow(4.0, 50.0) == 100.0\n",
                    "entrypoint": "pytest -q",
                },
                "reason": "Test valve flow calculation function",
            }
        ]
    }

    mock_llm = MockCodingLLMClient(
        plan_success=json.dumps(plan),
        finalize_summary="FACT: Function valve_flow passes all tests in isolated sandbox with exit code 0.",
    )
    set_llm_client_override(mock_llm)

    run_id = "test_demo_b_coding_001"
    user_id = "eng_coder_01"

    # Seed DB user
    with get_session_factory()() as db:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            user = User(id=user_id, username="coder_01", password_hash="mock_hash", role="engineer", clearance=1)
            db.add(user)
            db.commit()

    state = run_agent(
        user_request="Write a Python function for valve flow rate calculation with unit tests.",
        user_id=user_id,
        user_role="engineer",
        user_clearance="INTERNAL",
        run_id=run_id,
    )

    assert state["retry_count"] == 0
    assert len(state["errors"]) == 0
    assert len(state["tool_results"]) == 1
    assert state["tool_results"][0].tool == "run_code"
    assert state["tool_results"][0].status == "ok"
    assert state["tool_results"][0].output["exit_code"] == 0

    # Verify deliverable files on disk
    pkg_dir = outputs / run_id / "code_package"
    assert (pkg_dir / "src" / "solution.py").exists()
    assert (pkg_dir / "tests" / "test_solution.py").exists()
    assert (pkg_dir / "RESULT.txt").exists()
    res_text = (pkg_dir / "RESULT.txt").read_text(encoding="utf-8")
    assert "STATUS: PASS" in res_text


def test_coding_workflow_bounded_correction_cycle(tmp_path, monkeypatch):
    """A failing first attempt triggers exactly one bounded correction cycle."""
    outputs = tmp_path / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(get_settings(), "ALLOWED_OUTPUT_DIRS", str(outputs))

    attempt_counter = [0]

    def mock_sandbox_first_fail_then_pass(args, ctx, warnings):
        attempt_counter[0] += 1
        if attempt_counter[0] == 1:
            # First attempt fails
            return RunCodeResult(
                exit_code=1,
                stdout="FAILED test_solution.py::test_calc - assert 4.0 == 5.0",
                stderr="AssertionError: assert 4.0 == 5.0",
                duration_ms=40,
                status="failed",
                security_warnings=warnings,
                files_created=[],
            )
        else:
            # Second attempt passes
            package_code_deliverable(
                run_id=ctx.run_id,
                files={"src/solution.py": args.code or "", "tests/test_solution.py": args.tests or ""},
                exit_code=0,
                test_summary="1 passed in 0.04s",
                output_base_dir=str(outputs),
            )
            return RunCodeResult(
                exit_code=0,
                stdout="1 passed in 0.04s",
                stderr="",
                duration_ms=40,
                status="passed",
                security_warnings=warnings,
                files_created=["src/solution.py", "tests/test_solution.py", "RESULT.txt"],
            )

    set_sandbox_runner_override(mock_sandbox_first_fail_then_pass)

    plan_step_fail = {
        "steps": [
            {
                "step_id": 1,
                "tool": "run_code",
                "args": {"code": "def f(): return 4", "tests": "def test_calc(): assert f() == 5"},
                "reason": "Initial attempt with bug",
            }
        ]
    }
    plan_step_success = {
        "steps": [
            {
                "step_id": 1,
                "tool": "run_code",
                "args": {"code": "def f(): return 5", "tests": "def test_calc(): assert f() == 5"},
                "reason": "Corrected code implementation",
            }
        ]
    }

    mock_llm = MockCodingLLMClient(
        plan_success=json.dumps(plan_step_success),
        plan_retry=json.dumps(plan_step_fail),
        finalize_summary="FACT: Function corrected and verified in sandbox.",
    )
    set_llm_client_override(mock_llm)

    run_id = "test_run_correction_002"
    user_id = "eng_coder_02"

    with get_session_factory()() as db:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            user = User(id=user_id, username="coder_02", password_hash="mock_hash", role="engineer", clearance=1)
            db.add(user)
            db.commit()

    state = run_agent(
        user_request="Implement function f with tests.",
        user_id=user_id,
        user_role="engineer",
        user_clearance="INTERNAL",
        run_id=run_id,
    )

    # Exactly one retry occurred
    assert state["retry_count"] == 1
    assert attempt_counter[0] == 2
    assert "corrected" in state["final_answer"].lower()

    # Deliverable created after successful fix
    pkg_dir = outputs / run_id / "code_package"
    assert (pkg_dir / "RESULT.txt").exists()
    assert "STATUS: PASS" in (pkg_dir / "RESULT.txt").read_text(encoding="utf-8")


def test_coding_workflow_halts_at_max_retries(tmp_path, monkeypatch):
    """Repeated failures must halt gracefully at MAX_AGENT_RETRIES (3) without runaway loops."""
    outputs = tmp_path / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(get_settings(), "ALLOWED_OUTPUT_DIRS", str(outputs))

    def mock_sandbox_always_fails(args, ctx, warnings):
        return RunCodeResult(
            exit_code=1,
            stdout="FAILED test_solution.py::test_fail",
            stderr="AssertionError: failed",
            duration_ms=20,
            status="failed",
            security_warnings=warnings,
            files_created=[],
        )

    set_sandbox_runner_override(mock_sandbox_always_fails)

    plan = {
        "steps": [
            {
                "step_id": 1,
                "tool": "run_code",
                "args": {"code": "def f(): return 1", "tests": "def test_fail(): assert False"},
                "reason": "Persistent failing code",
            }
        ]
    }

    mock_llm = MockCodingLLMClient(
        plan_success=json.dumps(plan),
        finalize_summary="Task failed after maximum retries.",
    )
    set_llm_client_override(mock_llm)

    run_id = "test_run_halt_003"
    user_id = "eng_coder_03"

    with get_session_factory()() as db:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            user = User(id=user_id, username="coder_03", password_hash="mock_hash", role="engineer", clearance=1)
            db.add(user)
            db.commit()

    state = run_agent(
        user_request="Try to make tests pass.",
        user_id=user_id,
        user_role="engineer",
        user_clearance="INTERNAL",
        run_id=run_id,
    )

    settings = get_settings()
    assert state["retry_count"] >= settings.MAX_AGENT_RETRIES
    assert len(state["errors"]) > 0
    assert any("Bounded retry limit reached" in e for e in state["errors"])
    assert "failed" in state["final_answer"].lower()
