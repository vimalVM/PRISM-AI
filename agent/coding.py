"""Coding Agent loop helpers, error trimming, and package deliverable generator.

Implements 02_DESIGN_DOC.md §11 and 05_TEST_EVAL_DEMO.md §4.5:
- Generates verified code deliverable packages: src/, tests/, README.md, RESULT.txt.
- Extracts trimmed pytest errors (last N lines) for the bounded LLM correction loop.
- Manages coding attempt iterations (0..MAX_AGENT_RETRIES).
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.state import ArtifactRef
from backend.core.paths import safe_path


def extract_trimmed_error(stdout: str, stderr: str, max_lines: int = 25) -> str:
    """Extract a concise, focused failure summary from pytest stdout/stderr.

    Prevents context blowup by taking the most relevant error lines (e.g. failure summary).
    """
    combined = (stdout + "\n" + stderr).strip()
    if not combined:
        return "Unknown failure (empty output)."

    lines = [line.rstrip() for line in combined.splitlines() if line.strip()]

    # If FAILURES or short test summary info exists, focus from there
    failure_idx = -1
    for idx, line in enumerate(lines):
        if "FAILURES" in line or "short test summary info" in line or "ERRORS" in line:
            failure_idx = idx
            break

    if failure_idx != -1:
        extracted = lines[failure_idx:]
    else:
        extracted = lines[-max_lines:]

    if len(extracted) > max_lines:
        extracted = extracted[-max_lines:]

    return "\n".join(extracted)


def package_code_deliverable(
    run_id: str,
    files: Dict[str, str],
    exit_code: int = 0,
    test_summary: str = "All tests passed.",
    output_base_dir: str = "data/outputs",
) -> ArtifactRef:
    """Package verified code files into a formal deliverable package on disk.

    Layout per 05_TEST_EVAL_DEMO.md §4.5:
    data/outputs/<run_id>/code_package/
      src/
        solution.py
      tests/
        test_solution.py
      README.md
      RESULT.txt
    """
    package_dir = Path(output_base_dir) / run_id / "code_package"
    package_dir.mkdir(parents=True, exist_ok=True)

    src_dir = package_dir / "src"
    tests_dir = package_dir / "tests"
    src_dir.mkdir(exist_ok=True)
    tests_dir.mkdir(exist_ok=True)

    # Ensure __init__.py exists
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")

    # Write files
    for rel_path, content in files.items():
        target = package_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    # Ensure README.md exists
    readme_path = package_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            f"# Code Deliverable — Task {run_id}\n\n"
            f"Generated and verified in isolated Docker sandbox at {datetime.now(timezone.utc).isoformat()}.\n\n"
            "## Structure\n"
            "- `src/`: Solution source code\n"
            "- `tests/`: Automated pytest verification suite\n"
            "- `RESULT.txt`: Execution and test pass record\n",
            encoding="utf-8",
        )

    # Ensure RESULT.txt exists with exit code 0 and summary
    result_path = package_dir / "RESULT.txt"
    result_path.write_text(
        f"EXIT_CODE: {exit_code}\n"
        f"STATUS: {'PASS' if exit_code == 0 else 'FAIL'}\n"
        f"TIMESTAMP: {datetime.now(timezone.utc).isoformat()}\n"
        f"SUMMARY: {test_summary}\n",
        encoding="utf-8",
    )

    # Compute SHA-256 hash of RESULT.txt for artifact integrity
    hasher = hashlib.sha256()
    for item in sorted(package_dir.rglob("*")):
        if item.is_file():
            hasher.update(item.read_bytes())
    pkg_hash = hasher.hexdigest()

    return ArtifactRef(
        id=f"pkg-{run_id}",
        kind="code",
        filename="code_package",
        path=str(package_dir),
        sha256=pkg_hash,
    )
