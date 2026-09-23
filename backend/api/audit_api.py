"""Audit trail query, verification, and export endpoints (Admin & Auditor)."""

import csv
import io
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.audit import verify_chain
from backend.core.db import AuditLog, User, get_db
from backend.core.rbac import Role, require_role
from backend.schemas.auth import AuditEventResponse, AuditListResponse, AuditVerifyResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditListResponse)
def query_audit_logs(
    event_type: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    run_id: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(Role.ADMIN, Role.AUDITOR)),
    db: Session = Depends(get_db),
) -> AuditListResponse:
    """Query audit logs with filtering and pagination. Accessible to admin and auditor."""
    query = select(AuditLog)

    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if run_id:
        query = query.where(AuditLog.run_id == run_id)
    if status_filter:
        query = query.where(AuditLog.status == status_filter)

    total_query = select(func.count()).select_from(query.subquery())
    total = db.execute(total_query).scalar_one()

    query = query.order_by(AuditLog.id.desc()).offset(offset).limit(limit)
    records = db.execute(query).scalars().all()

    return AuditListResponse(
        items=[AuditEventResponse.model_validate(r) for r in records],
        total=total,
    )


@router.get("/verify", response_model=AuditVerifyResponse)
def verify_audit_chain(
    user: User = Depends(require_role(Role.ADMIN, Role.AUDITOR)),
    db: Session = Depends(get_db),
) -> AuditVerifyResponse:
    """Cryptographically verify the SHA-256 hash chain of the entire audit log."""
    valid, detail = verify_chain(db)
    return AuditVerifyResponse(valid=valid, detail=detail)


@router.get("/export")
def export_audit_log(
    export_format: str = Query(default="jsonl", alias="format", pattern="^(jsonl|csv)$"),
    user: User = Depends(require_role(Role.ADMIN, Role.AUDITOR)),
    db: Session = Depends(get_db),
) -> Response:
    """Export complete audit log in JSONL or CSV format."""
    query = select(AuditLog).order_by(AuditLog.id.asc())
    records = db.execute(query).scalars().all()

    if export_format == "jsonl":
        output = io.StringIO()
        for r in records:
            row_dict = {
                "id": r.id,
                "ts": r.ts,
                "run_id": r.run_id,
                "user_id": r.user_id,
                "role": r.role,
                "event_type": r.event_type,
                "model": r.model,
                "tool": r.tool,
                "file_ids_json": r.file_ids_json,
                "status": r.status,
                "duration_ms": r.duration_ms,
                "details_json": r.details_json,
                "prev_hash": r.prev_hash,
                "hash": r.hash,
            }
            output.write(json.dumps(row_dict, ensure_ascii=True) + "\n")
        content = output.getvalue()
        return Response(
            content=content,
            media_type="application/x-ndjson",
            headers={"Content-Disposition": 'attachment; filename="audit_export.jsonl"'},
        )
    else:
        # CSV format
        output = io.StringIO()
        fieldnames = [
            "id", "ts", "run_id", "user_id", "role", "event_type", "model", "tool",
            "file_ids_json", "status", "duration_ms", "details_json", "prev_hash", "hash",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "id": r.id,
                "ts": r.ts,
                "run_id": r.run_id,
                "user_id": r.user_id,
                "role": r.role,
                "event_type": r.event_type,
                "model": r.model,
                "tool": r.tool,
                "file_ids_json": r.file_ids_json,
                "status": r.status,
                "duration_ms": r.duration_ms,
                "details_json": r.details_json,
                "prev_hash": r.prev_hash,
                "hash": r.hash,
            })
        content = output.getvalue()
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="audit_export.csv"'},
        )
