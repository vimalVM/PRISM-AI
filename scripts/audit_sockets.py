"""Helper script to run passive socket connection audit and print JSON report.

Implements Phase 12 of docs/04_ANTIGRAVITY_BUILD_PLAN.md.
"""

import json
from pathlib import Path
import sys

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.api.system import audit_connections
from backend.core.db import User

if __name__ == "__main__":
    dummy_user = User(
        id="sys_audit",
        username="auditor",
        role="auditor",
        clearance=3,
        active=True,
    )
    res = audit_connections(current_user=dummy_user)
    print(json.dumps(res.model_dump(), indent=2))
