"""Append-only audit logging with cryptographic hash chaining and JSONL mirroring.

Implements SEC-14 (audit tamper detection, content-free records, SHA-256 chain).
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.db import AuditLog, get_engine, get_session_factory


GENESIS_PREV_HASH = "0" * 64

VALID_EVENT_TYPES = {
    "login_ok",
    "login_failed",
    "account_locked",
    "logout",
    "run_started",
    "model_route",
    "model_call",
    "tool_call",
    "rag_retrieval",
    "access_denied",
    "sandbox_run",
    "validation",
    "retry",
    "artifact_created",
    "review_decision",
    "kb_ingested",
    "kb_deleted",
    "user_changed",
    "registry_reloaded",
    "config_check_failed",
    "run_finished",
    "error",
}

FORBIDDEN_DETAIL_KEYS = {"password", "secret", "token", "prompt", "raw_text", "document_text", "ocr_text"}

_lock = threading.Lock()


def canonical_json(data: Dict[str, Any]) -> str:
    """Format dictionary as canonical JSON string (deterministic whitespace & key sorting)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_audit_hash(prev_hash: str, canonical_record: str) -> str:
    """Compute SHA-256 hash from prev_hash and canonical record string."""
    payload = f"{prev_hash}{canonical_record}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sanitize_details(details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Ensure details dictionary does not store passwords, raw text or secrets."""
    if not details:
        return {}

    sanitized = {}
    for k, v in details.items():
        k_lower = k.lower()
        if any(f in k_lower for f in FORBIDDEN_DETAIL_KEYS):
            continue  # Drop forbidden content fields completely
        if isinstance(v, str) and len(v) > 500:
            # Document contents or large texts must not be stored in audit logs
            sanitized[k] = f"[TRUNCATED_HASH:{hashlib.sha256(v.encode()).hexdigest()[:16]}]"
        else:
            sanitized[k] = v
    return sanitized


def _get_jsonl_log_path() -> Path:
    settings = get_settings()
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return log_dir / f"audit-{today}.jsonl"


def _append_to_jsonl_mirror(record_dict: Dict[str, Any]) -> None:
    """Mirror audit record to daily JSONL file."""
    try:
        log_path = _get_jsonl_log_path()
        line = json.dumps(record_dict, sort_keys=True, ensure_ascii=True) + "\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # Logging error should not bring down the application, but must not crash
        pass


def log_event(
    event_type: str,
    status: str,
    user_id: Optional[str] = None,
    role: Optional[str] = None,
    run_id: Optional[str] = None,
    model: Optional[str] = None,
    tool: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    duration_ms: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> AuditLog:
    """Record an audit event with SHA-256 hash chaining into DB and JSONL mirror.
    
    Thread-safe to prevent hash-chain race conditions.
    """
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(f"Unknown audit event type: '{event_type}'")

    ts_iso = datetime.now(timezone.utc).isoformat()
    clean_details = sanitize_details(details)
    details_json = json.dumps(clean_details, sort_keys=True) if clean_details else None
    file_ids_json = json.dumps(file_ids) if file_ids else None

    owns_session = False
    if db is None:
        factory = get_session_factory()
        db = factory()
        owns_session = True

    with _lock:
        try:
            # 1. Fetch the latest record to get the prev_hash
            stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
            last_record = db.execute(stmt).scalar_one_or_none()
            prev_hash = last_record.hash if last_record else GENESIS_PREV_HASH

            # 2. Build canonical record representation for hashing
            record_for_hashing = {
                "ts": ts_iso,
                "run_id": run_id,
                "user_id": user_id,
                "role": role,
                "event_type": event_type,
                "model": model,
                "tool": tool,
                "file_ids_json": file_ids_json,
                "status": status,
                "duration_ms": duration_ms,
                "details_json": details_json,
            }
            canonical_str = canonical_json(record_for_hashing)
            current_hash = compute_audit_hash(prev_hash, canonical_str)

            # 3. Create ORM record and persist
            audit_entry = AuditLog(
                ts=ts_iso,
                run_id=run_id,
                user_id=user_id,
                role=role,
                event_type=event_type,
                model=model,
                tool=tool,
                file_ids_json=file_ids_json,
                status=status,
                duration_ms=duration_ms,
                details_json=details_json,
                prev_hash=prev_hash,
                hash=current_hash,
            )
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)

            # 4. Mirror to JSONL
            mirror_dict = {
                "id": audit_entry.id,
                "ts": ts_iso,
                "run_id": run_id,
                "user_id": user_id,
                "role": role,
                "event_type": event_type,
                "model": model,
                "tool": tool,
                "file_ids": file_ids,
                "status": status,
                "duration_ms": duration_ms,
                "details": clean_details,
                "prev_hash": prev_hash,
                "hash": current_hash,
            }
            _append_to_jsonl_mirror(mirror_dict)

            return audit_entry
        finally:
            if owns_session:
                db.close()


def verify_chain(db: Optional[Session] = None) -> Tuple[bool, Optional[str]]:
    """Verify cryptographic integrity of the entire audit log hash chain.
    
    Returns:
        (True, None) if the hash chain is fully valid.
        (False, error_message) if tampering or breakage is detected.
    """
    owns_session = False
    if db is None:
        factory = get_session_factory()
        db = factory()
        owns_session = True

    try:
        stmt = select(AuditLog).order_by(AuditLog.id.asc())
        records = db.execute(stmt).scalars().all()

        if not records:
            return True, None

        expected_prev_hash = GENESIS_PREV_HASH

        for record in records:
            # 1. Check link to previous record
            if record.prev_hash != expected_prev_hash:
                return (
                    False,
                    f"Hash chain broken at ID {record.id}: expected prev_hash '{expected_prev_hash}', "
                    f"found '{record.prev_hash}'",
                )

            # 2. Recompute current hash
            record_for_hashing = {
                "ts": record.ts,
                "run_id": record.run_id,
                "user_id": record.user_id,
                "role": record.role,
                "event_type": record.event_type,
                "model": record.model,
                "tool": record.tool,
                "file_ids_json": record.file_ids_json,
                "status": record.status,
                "duration_ms": record.duration_ms,
                "details_json": record.details_json,
            }
            canonical_str = canonical_json(record_for_hashing)
            computed_hash = compute_audit_hash(expected_prev_hash, canonical_str)

            if computed_hash != record.hash:
                return (
                    False,
                    f"Tamper detected at ID {record.id}: computed hash '{computed_hash}' != "
                    f"stored hash '{record.hash}'",
                )

            expected_prev_hash = record.hash

        return True, None
    finally:
        if owns_session:
            db.close()
