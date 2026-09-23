"""Tests for append-only audit log, cryptographic hash chaining, and tamper detection (SEC-14)."""

import json
from pathlib import Path
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.core.audit import (
    GENESIS_PREV_HASH,
    compute_audit_hash,
    log_event,
    sanitize_details,
    verify_chain,
)
from backend.core.db import AuditLog, Base


@pytest.fixture
def memory_db():
    """In-memory SQLite database for audit tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = factory()
    yield session
    session.close()


def test_hash_chain_integrity_10_records(memory_db):
    """SEC-14: Verify hash chain integrity across 10 consecutive audit events."""
    for i in range(10):
        log_event(
            event_type="model_call" if i % 2 == 0 else "tool_call",
            status="ok",
            user_id=f"user-{i}",
            role="engineer",
            run_id=f"run-{i}",
            duration_ms=100 + i,
            details={"step": i, "token_count": 42 + i},
            db=memory_db,
        )

    # Chain should verify successfully
    valid, detail = verify_chain(db=memory_db)
    assert valid is True
    assert detail is None

    # Check that genesis prev_hash is GENESIS_PREV_HASH
    first = memory_db.execute(select(AuditLog).order_by(AuditLog.id.asc())).scalars().first()
    assert first.prev_hash == GENESIS_PREV_HASH


def test_audit_tamper_detection_sec14(memory_db):
    """SEC-14: Modifying any field in an existing audit log entry must break the hash chain."""
    for i in range(5):
        log_event(
            event_type="tool_call",
            status="ok",
            user_id="user-1",
            role="engineer",
            details={"step": i},
            db=memory_db,
        )

    # Verify initially valid
    assert verify_chain(db=memory_db)[0] is True

    # Tamper with row 3 (e.g. change status from 'ok' to 'error')
    row_3 = memory_db.execute(select(AuditLog).where(AuditLog.id == 3)).scalar_one()
    row_3.status = "error"
    memory_db.commit()

    # Now verify_chain MUST fail and report tampering at ID 3
    valid, detail = verify_chain(db=memory_db)
    assert valid is False
    assert "Tamper detected at ID 3" in detail


def test_audit_tamper_prev_hash_detection(memory_db):
    """SEC-14: Modifying prev_hash in a row must be detected as a broken link."""
    for i in range(4):
        log_event(
            event_type="login_ok",
            status="ok",
            user_id=f"user-{i}",
            db=memory_db,
        )

    # Modify prev_hash of row 2
    row_2 = memory_db.execute(select(AuditLog).where(AuditLog.id == 2)).scalar_one()
    row_2.prev_hash = "deadbeef" * 8
    memory_db.commit()

    valid, detail = verify_chain(db=memory_db)
    assert valid is False
    assert "Hash chain broken at ID 2" in detail


def test_audit_content_free_rule():
    """Audit details must NEVER store document text, passwords, secret keys, or prompts."""
    dirty_details = {
        "password": "SuperSecretPassword123!",
        "secret": "my-secret-key",
        "raw_text": "This is confidential nuclear facility specification document text.",
        "prompt": "Summarize this restricted document.",
        "document_text": "Classified contents...",
        "count": 5,
        "model": "qwen3.5:4b",
    }

    clean = sanitize_details(dirty_details)

    # Forbidden keys must be stripped
    assert "password" not in clean
    assert "secret" not in clean
    assert "raw_text" not in clean
    assert "prompt" not in clean
    assert "document_text" not in clean

    # Allowed non-content fields remain
    assert clean["count"] == 5
    assert clean["model"] == "qwen3.5:4b"

    # Very large strings must be truncated or hashed, not kept in full
    large_details = {"analysis": "A" * 1000}
    clean_large = sanitize_details(large_details)
    assert len(clean_large["analysis"]) < 100
    assert "[TRUNCATED_HASH:" in clean_large["analysis"]
