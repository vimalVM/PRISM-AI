"""Docker-isolated hardened code sandbox execution tool for Sovereign AI Workbench.

Implements SEC-08, SEC-09, SEC-10, and 02_DESIGN_DOC.md §11 / 03_SECURITY_AND_ACCESS.md §8:
- Complete network isolation (--network=none).
- CPU & memory quotas (--cpus=1, --memory=512m, --memory-swap=512m).
- PID limit (--pids-limit=128) and read-only root with restricted /tmp tmpfs.
- Dropped capabilities (--cap-drop=ALL, no-new-privileges, non-root user 10001).
- Per-run isolated temporary directory mounted exclusively at /work.
- Host-side wall-clock timeout kill and 64 KB output cap.
- Pre-execution static denylist scanner.
- Audited tool @audited_tool(name="run_code").
"""

import logging
from pathlib import Path
import re
import shutil
import tempfile
import time
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

from backend.core.config import get_settings
from tools.registry import ToolContext, audited_tool

logger = logging.getLogger("sovereign-workbench.tools.sandbox")

# Pre-execution static denylist patterns (report in audit, container hardening prevents harm)
STATIC_DENYLIST_PATTERNS = [
    (r"\b(socket|urllib|requests|http\.client|ftplib)\b", "Network / socket operations attempted in sandboxed code"),
    (r"\b(os\.system|subprocess\.|pty\.|os\.popen|ctypes\.)\b", "Process execution or foreign function interface attempted"),
    (r"\b(shutil\.rmtree|os\.remove|os\.unlink)\b", "Destructive filesystem operation attempted"),
]

# Global test runner override hook for unit testing without a live Docker daemon
_SANDBOX_RUNNER_OVERRIDE: Optional[Callable[..., Any]] = None


def set_sandbox_runner_override(runner: Optional[Callable[..., Any]]) -> None:
    """Inject a custom sandbox runner (used for unit tests and mocks)."""
    global _SANDBOX_RUNNER_OVERRIDE
    _SANDBOX_RUNNER_OVERRIDE = runner


def scan_code_security(code_texts: List[str]) -> List[str]:
    """Perform static denylist scan across generated code files."""
    warnings: List[str] = []
    combined_code = "\n".join(code_texts)

    for pattern, description in STATIC_DENYLIST_PATTERNS:
        if re.search(pattern, combined_code, re.IGNORECASE):
            warnings.append(description)

    return warnings


class RunCodeArgs(BaseModel):
    """Input parameters for running code in the Docker sandbox."""

    code: Optional[str] = Field(default=None, description="Primary source code content (saved to solution.py if not specified in files)")
    tests: Optional[str] = Field(default=None, description="Pytest test file content (saved to test_solution.py)")
    files: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Relative filepath to file content mapping (e.g. {'src/logic.py': '...', 'tests/test_logic.py': '...'}).",
    )
    entrypoint: str = Field(default="pytest -q", description="Execution command line inside container (default: 'pytest -q')")
    timeout_s: Optional[int] = Field(default=None, description="Wall-clock timeout in seconds (defaults to SANDBOX_TIMEOUT_S)")


class RunCodeResult(BaseModel):
    """Execution outcome from the hardened sandbox."""

    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    status: Literal["passed", "failed", "timeout", "error", "security_flagged"]
    security_warnings: List[str] = Field(default_factory=list)
    files_created: List[str] = Field(default_factory=list)


def _execute_docker_sandbox(
    temp_dir: Path,
    entrypoint: str,
    timeout_s: int,
    output_limit_bytes: int,
    image_tag: str,
) -> Tuple[int, str, str, str]:
    """Execute container via Docker Python SDK enforcing all security hardening flags."""
    import docker
    from docker.errors import APIError, DockerException, NotFound

    client = docker.from_env()

    # Verify or resolve image
    try:
        client.images.get(image_tag)
    except (NotFound, ImageNotFound := docker.errors.ImageNotFound):
        # Fall back to base python:3.11-slim if custom tag not yet built
        logger.info(f"Image '{image_tag}' not found locally. Attempting fallback to 'python:3.11-slim'")
        image_tag = "python:3.11-slim"

    container = None
    status = "passed"
    stdout_text = ""
    stderr_text = ""
    exit_code = 0

    # Command split
    cmd_parts = entrypoint.split()

    try:
        container = client.containers.create(
            image=image_tag,
            command=cmd_parts,
            network_mode="none",  # SEC-08: Complete air-gap network isolation
            mem_limit="512m",  # SEC-10: 512 MB memory limit
            memswap_limit="512m",
            nano_cpus=1_000_000_000,  # 1.0 CPU limit
            pids_limit=128,  # Prevent fork bombs
            read_only=True,  # Read-only root filesystem
            tmpfs={"/tmp": "rw,noexec,size=64m"},  # Restricted temporary filesystem
            cap_drop=["ALL"],  # Drop all capabilities
            security_opt=["no-new-privileges:true"],
            user="10001:10001",  # Unprivileged non-root user
            volumes={str(temp_dir): {"bind": "/work", "mode": "rw"}},
            working_dir="/work",
        )

        container.start()

        # Enforce host-side wall-clock timeout (SEC-09)
        try:
            wait_res = container.wait(timeout=timeout_s)
            exit_code = wait_res.get("StatusCode", -1)
            status = "passed" if exit_code == 0 else "failed"
        except Exception:
            # Timeout exceeded -> forcefully kill container
            logger.warning(f"Sandbox container exceeded wall-clock timeout of {timeout_s}s. Force killing.")
            try:
                container.kill()
            except Exception:
                pass
            exit_code = 124  # Standard timeout exit code
            status = "timeout"
            stderr_text = f"Execution killed: exceeded wall-clock timeout limit of {timeout_s} seconds (SEC-09)."

        # Retrieve stdout and stderr logs
        try:
            raw_stdout = container.logs(stdout=True, stderr=False)
            raw_stderr = container.logs(stdout=False, stderr=True)
            if not stdout_text:
                stdout_text = raw_stdout.decode("utf-8", errors="replace")
            if not stderr_text:
                stderr_text = raw_stderr.decode("utf-8", errors="replace")
        except Exception as log_err:
            logger.warning(f"Failed to read container logs: {log_err}")

    except Exception as exc:
        exit_code = 1
        status = "error"
        stderr_text = f"Docker container execution error: {exc}"

    finally:
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass

    # Cap output size
    if len(stdout_text.encode("utf-8")) > output_limit_bytes:
        stdout_text = stdout_text[:output_limit_bytes] + "\n[OUTPUT TRUNCATED - Exceeded 64KB limit]"
    if len(stderr_text.encode("utf-8")) > output_limit_bytes:
        stderr_text = stderr_text[:output_limit_bytes] + "\n[OUTPUT TRUNCATED - Exceeded 64KB limit]"

    return exit_code, stdout_text, stderr_text, status


@audited_tool(name="run_code", side_effects=True, needs_role=None)
def run_code(args: RunCodeArgs, ctx: ToolContext) -> RunCodeResult:
    """Execute code and tests within the hardened Docker sandbox."""
    settings = get_settings()
    timeout_s = args.timeout_s or settings.SANDBOX_TIMEOUT_S
    output_limit_bytes = settings.SANDBOX_OUTPUT_LIMIT_KB * 1024
    image_tag = settings.SANDBOX_IMAGE_TAG

    # Collect all code texts for static security check
    all_code_texts: List[str] = []
    if args.code:
        all_code_texts.append(args.code)
    if args.tests:
        all_code_texts.append(args.tests)
    if args.files:
        all_code_texts.extend(args.files.values())

    security_warnings = scan_code_security(all_code_texts)
    if security_warnings:
        logger.info(f"Sandbox static scan flagged security patterns: {security_warnings}")

    # Check for runner override (used in unit tests / mocks)
    if _SANDBOX_RUNNER_OVERRIDE is not None:
        return _SANDBOX_RUNNER_OVERRIDE(args, ctx, security_warnings)

    # Create fresh isolated temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="workbench_sandbox_"))
    t_start = time.perf_counter()

    try:
        # Populate files in temp dir
        if args.code:
            (temp_dir / "solution.py").write_text(args.code, encoding="utf-8")
        if args.tests:
            (temp_dir / "test_solution.py").write_text(args.tests, encoding="utf-8")
        if args.files:
            for rel_path, content in args.files.items():
                p = temp_dir / rel_path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")

        # Execute container
        exit_code, stdout, stderr, status = _execute_docker_sandbox(
            temp_dir=temp_dir,
            entrypoint=args.entrypoint,
            timeout_s=timeout_s,
            output_limit_bytes=output_limit_bytes,
            image_tag=image_tag,
        )

        duration_ms = int((time.perf_counter() - t_start) * 1000)

        # Inspect any new files created by the run
        created = [
            str(f.relative_to(temp_dir))
            for f in temp_dir.rglob("*")
            if f.is_file() and not f.name.endswith(".pyc") and "__pycache__" not in str(f)
        ]

        return RunCodeResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            status=status,
            security_warnings=security_warnings,
            files_created=created,
        )

    finally:
        # Secure cleanup: remove temporary sandbox workspace
        shutil.rmtree(temp_dir, ignore_errors=True)
