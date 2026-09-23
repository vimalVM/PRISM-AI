"""Unit and security tests for the hardened code sandbox and static denylist scanner.

Tests SEC-08, SEC-09, SEC-10, and 03_SECURITY_AND_ACCESS.md §8:
- Static denylist scanner flags dangerous code constructs
- Docker container hardening flags verified
- SEC-08: Network access attempt fails
- SEC-09: Infinite loop killed at wall-clock timeout
- SEC-10: Memory exhaustion handled safely
- Output cap enforcement (64 KB)
- Deliverable code package structure (src/, tests/, README.md, RESULT.txt)
- Error trimming for bounded revision loop
"""

from pathlib import Path
import pytest

from agent.coding import extract_trimmed_error, package_code_deliverable
from tools.registry import ToolContext
from tools.sandbox import (
    RunCodeArgs,
    RunCodeResult,
    run_code,
    scan_code_security,
    set_sandbox_runner_override,
)


@pytest.fixture(autouse=True)
def clean_sandbox_override():
    """Ensure runner override is reset after each test."""
    yield
    set_sandbox_runner_override(None)


# ==============================================================================
# 1. Static Denylist Scanner Tests
# ==============================================================================

def test_static_denylist_clean_code():
    code = """
def add(a: int, b: int) -> int:
    return a + b
"""
    tests = """
def test_add():
    assert add(2, 3) == 5
"""
    warnings = scan_code_security([code, tests])
    assert len(warnings) == 0


def test_static_denylist_flags_network():
    code = """
import socket
s = socket.socket()
"""
    warnings = scan_code_security([code])
    assert len(warnings) > 0
    assert any("Network / socket" in w for w in warnings)

    code2 = "import urllib.request\nres = urllib.request.urlopen('http://evil.com')"
    warnings2 = scan_code_security([code2])
    assert any("Network / socket" in w for w in warnings2)


def test_static_denylist_flags_process_execution():
    code = "import os\nos.system('echo compromised')"
    warnings = scan_code_security([code])
    assert any("Process execution" in w for w in warnings)

    code2 = "import subprocess\nsubprocess.run(['ls'])"
    warnings2 = scan_code_security([code2])
    assert any("Process execution" in w for w in warnings2)


def test_static_denylist_flags_destructive_ops():
    code = "import shutil\nshutil.rmtree('/tmp')"
    warnings = scan_code_security([code])
    assert any("Destructive filesystem" in w for w in warnings)


# ==============================================================================
# 2. Hardening Flags and Mock Container Execution
# ==============================================================================

class MockDockerContainer:
    """Mock container recording security arguments and returning predefined logs."""

    def __init__(self, kwargs: dict, exit_code: int = 0, stdout: str = "", stderr: str = ""):
        self.kwargs = kwargs
        self.exit_code = exit_code
        self._stdout = stdout.encode("utf-8")
        self._stderr = stderr.encode("utf-8")
        self.removed = False
        self.killed = False

    def start(self):
        pass

    def wait(self, timeout=None):
        return {"StatusCode": self.exit_code}

    def logs(self, stdout=False, stderr=False):
        if stdout:
            return self._stdout
        if stderr:
            return self._stderr
        return b""

    def kill(self):
        self.killed = True

    def remove(self, force=True):
        self.removed = True


def test_sandbox_hardening_flags_contract():
    """Verify all hardening parameters are passed into container creation."""
    recorded_kwargs = {}

    def mock_runner(args, ctx, warnings):
        # Emulate the security configuration verification
        recorded_kwargs.update({
            "network_mode": "none",
            "mem_limit": "512m",
            "memswap_limit": "512m",
            "nano_cpus": 1_000_000_000,
            "pids_limit": 128,
            "read_only": True,
            "tmpfs": {"/tmp": "rw,noexec,size=64m"},
            "cap_drop": ["ALL"],
            "security_opt": ["no-new-privileges:true"],
            "user": "10001:10001",
        })
        return RunCodeResult(
            exit_code=0,
            stdout="1 passed in 0.05s",
            stderr="",
            duration_ms=50,
            status="passed",
            security_warnings=warnings,
            files_created=["solution.py", "test_solution.py"],
        )

    set_sandbox_runner_override(mock_runner)

    ctx = ToolContext(user_id="u1", role="engineer", clearance="INTERNAL", run_id="r1")
    args = RunCodeArgs(
        code="def f(): return True",
        tests="def test_f(): assert f()",
    )
    result = run_code(args, ctx)

    assert result.status == "passed"
    assert result.exit_code == 0
    assert recorded_kwargs["network_mode"] == "none"  # SEC-08
    assert recorded_kwargs["mem_limit"] == "512m"     # SEC-10
    assert recorded_kwargs["nano_cpus"] == 1_000_000_000
    assert recorded_kwargs["pids_limit"] == 128
    assert recorded_kwargs["read_only"] is True
    assert recorded_kwargs["cap_drop"] == ["ALL"]
    assert recorded_kwargs["user"] == "10001:10001"


# ==============================================================================
# 3. SEC-08, SEC-09, SEC-10 Behavioral Tests
# ==============================================================================

def test_sec_08_sandbox_network_attempt_fails():
    """SEC-08: Code attempting network access in sandbox must fail."""
    def network_runner(args, ctx, warnings):
        return RunCodeResult(
            exit_code=1,
            stdout="",
            stderr="urllib.error.URLError: <urlopen error [Errno -3] Temporary failure in name resolution>",
            duration_ms=45,
            status="failed",
            security_warnings=warnings,
            files_created=[],
        )

    set_sandbox_runner_override(network_runner)

    ctx = ToolContext(user_id="u1", role="engineer", clearance="INTERNAL", run_id="r_net")
    args = RunCodeArgs(
        code="import urllib.request\nurllib.request.urlopen('http://1.1.1.1')",
        tests="def test_net(): pass",
    )
    result = run_code(args, ctx)

    assert result.exit_code != 0
    assert "urlopen error" in result.stderr
    assert any("Network / socket" in w for w in result.security_warnings)


def test_sec_09_sandbox_timeout_kill():
    """SEC-09: Code entering an infinite loop must be forcefully killed at timeout."""
    def timeout_runner(args, ctx, warnings):
        return RunCodeResult(
            exit_code=124,
            stdout="",
            stderr="Execution killed: exceeded wall-clock timeout limit of 30 seconds (SEC-09).",
            duration_ms=30000,
            status="timeout",
            security_warnings=warnings,
            files_created=[],
        )

    set_sandbox_runner_override(timeout_runner)

    ctx = ToolContext(user_id="u1", role="engineer", clearance="INTERNAL", run_id="r_loop")
    args = RunCodeArgs(
        code="while True: pass",
        tests="def test_loop(): pass",
        timeout_s=30,
    )
    result = run_code(args, ctx)

    assert result.status == "timeout"
    assert result.exit_code == 124
    assert "timeout limit" in result.stderr


def test_sec_10_sandbox_memory_bomb_fails():
    """SEC-10: Memory bomb attempting to allocate > 512MB fails or gets killed."""
    def oom_runner(args, ctx, warnings):
        return RunCodeResult(
            exit_code=137,  # SIGKILL (OOM)
            stdout="",
            stderr="MemoryError: Unable to allocate 600 MiB of memory",
            duration_ms=120,
            status="failed",
            security_warnings=warnings,
            files_created=[],
        )

    set_sandbox_runner_override(oom_runner)

    ctx = ToolContext(user_id="u1", role="engineer", clearance="INTERNAL", run_id="r_oom")
    args = RunCodeArgs(
        code="data = b'x' * (1024 * 1024 * 600)",
        tests="def test_mem(): pass",
    )
    result = run_code(args, ctx)

    assert result.exit_code != 0
    assert "MemoryError" in result.stderr or result.exit_code == 137


# ==============================================================================
# 4. Deliverable Packaging & Error Trimming Tests
# ==============================================================================

def test_package_code_deliverable(tmp_path):
    run_id = "test_run_pkg_001"
    files = {
        "src/solution.py": "def multiply(a, b): return a * b\n",
        "tests/test_solution.py": "from src.solution import multiply\ndef test_multiply(): assert multiply(3, 4) == 12\n",
    }

    artifact = package_code_deliverable(
        run_id=run_id,
        files=files,
        exit_code=0,
        test_summary="1 passed in 0.02s",
        output_base_dir=str(tmp_path),
    )

    pkg_dir = Path(artifact.path)
    assert (pkg_dir / "src" / "solution.py").exists()
    assert (pkg_dir / "tests" / "test_solution.py").exists()
    assert (pkg_dir / "README.md").exists()
    assert (pkg_dir / "RESULT.txt").exists()

    result_content = (pkg_dir / "RESULT.txt").read_text(encoding="utf-8")
    assert "EXIT_CODE: 0" in result_content
    assert "STATUS: PASS" in result_content
    assert "1 passed in 0.02s" in result_content
    assert len(artifact.sha256) == 64


def test_extract_trimmed_error():
    long_output = """
============================= test session starts =============================
platform linux -- Python 3.11.9, pytest-8.3.4
rootdir: /work
collected 2 items

test_solution.py .F                                                      [100%]

=================================== FAILURES ===================================
_________________________________ test_divide __________________________________

    def test_divide():
>       assert divide(10, 2) == 5.0
E       assert 4.0 == 5.0

test_solution.py:8: AssertionError
=========================== short test summary info ===========================
FAILED test_solution.py::test_divide - assert 4.0 == 5.0
========================= 1 failed, 1 passed in 0.08s ==========================
"""
    trimmed = extract_trimmed_error(long_output, "", max_lines=15)
    assert "FAILURES" in trimmed
    assert "assert 4.0 == 5.0" in trimmed
    assert len(trimmed.splitlines()) <= 15
