"""Seed script for initializing default Sovereign AI Workbench demo users.

Creates:
  - admin (role: admin, clearance: 3)
  - engineer (role: engineer, clearance: 2)
  - reviewer (role: reviewer, clearance: 3)
  - auditor (role: auditor, clearance: 3)

Passwords are read from environment variables or prompted securely via getpass.
NO passwords are ever hard-coded in source, logs, or git.
"""

import getpass
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from backend.core.db import User, get_session_factory, init_db, utc_now
from backend.core.rbac import Clearance, Role
from backend.core.security import hash_password


USERS_TO_SEED = [
    {
        "username": "admin",
        "role": Role.ADMIN.value,
        "clearance": Clearance.RESTRICTED.value,
        "env_var": "SEED_ADMIN_PASSWORD",
    },
    {
        "username": "engineer",
        "role": Role.ENGINEER.value,
        "clearance": Clearance.CONFIDENTIAL.value,
        "env_var": "SEED_ENGINEER_PASSWORD",
    },
    {
        "username": "reviewer",
        "role": Role.REVIEWER.value,
        "clearance": Clearance.RESTRICTED.value,
        "env_var": "SEED_REVIEWER_PASSWORD",
    },
    {
        "username": "auditor",
        "role": Role.AUDITOR.value,
        "clearance": Clearance.RESTRICTED.value,
        "env_var": "SEED_AUDITOR_PASSWORD",
    },
]


def prompt_or_get_password(username: str, env_var: str) -> str:
    """Retrieve password from environment or prompt securely."""
    env_pw = os.environ.get(env_var) or os.environ.get("SEED_DEFAULT_PASSWORD")
    if env_pw:
        if len(env_pw) < 12:
            raise ValueError(f"Password in {env_var} must be at least 12 characters long.")
        return env_pw

    while True:
        pw = getpass.getpass(f"Enter password for '{username}' (min 12 chars): ")
        if len(pw) < 12:
            print("Password must be at least 12 characters. Please try again.")
            continue
        confirm = getpass.getpass(f"Confirm password for '{username}': ")
        if pw != confirm:
            print("Passwords do not match. Please try again.")
            continue
        return pw


def seed_users():
    """Seed initial system users into SQLite database."""
    print("Initializing database...")
    init_db()
    factory = get_session_factory()
    db = factory()

    try:
        created_count = 0
        for item in USERS_TO_SEED:
            username = item["username"]
            stmt = select(User).where(User.username == username)
            existing = db.execute(stmt).scalar_one_or_none()
            if existing:
                print(f"[SKIP] User '{username}' already exists.")
                continue

            pw = prompt_or_get_password(username, item["env_var"])
            user = User(
                username=username,
                password_hash=hash_password(pw),
                role=item["role"],
                clearance=item["clearance"],
                active=True,
                created_at=utc_now(),
            )
            db.add(user)
            db.commit()
            created_count += 1
            print(f"[CREATED] User '{username}' (role={item['role']}, clearance={item['clearance']})")

        print(f"\nSeeding complete. {created_count} user(s) created.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
