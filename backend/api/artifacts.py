"""Artifact management and download endpoints for Sovereign AI Workbench.

Implements secure deliverable listing, metadata retrieval with validation reports,
and scoped downloads enforcing:
- SEC-19: Auditor role cannot download deliverables (403 Forbidden)
- SEC-20: Reviewers cannot access or download artifacts assigned to others (403 Forbidden)
- Path confinement via safe_path to DATA_DIR/outputs
- Content-Disposition: attachment header
- Audit logging of download events
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.core.audit import log_event
from backend.core.config import get_settings
from backend.core.db import Artifact, Task, User, get_db
from backend.core.paths import AccessDenied, safe_path
from backend.core.rbac import (
    Role,
    can_access_artifact,
    can_download_artifact,
    can_review_artifact,
    require_role,
)
from backend.core.security import get_current_user

logger = logging.getLogger("sovereign-workbench.artifacts")

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])
review_router = APIRouter(prefix="/review", tags=["Review"])


class ArtifactDetailResponse(BaseModel):
    """Artifact metadata and validation report schema."""
    id: str
    task_id: str
    owner_id: str
    kind: str
    filename: str
    sha256: str
    status: str
    validation_results: Optional[List[Dict[str, Any]]] = None
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_comment: Optional[str] = None
    created_at: str


@router.get("", response_model=List[ArtifactDetailResponse])
async def list_artifacts(
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    kind: Optional[str] = Query(None, description="Filter by deliverable kind"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ArtifactDetailResponse]:
    """List accessible artifacts based on role and ownership scoping."""
    query = select(Artifact)

    if task_id:
        query = query.where(Artifact.task_id == task_id)
    if kind:
        query = query.where(Artifact.kind == kind)

    # Scoping per role:
    # - Admin & Auditor: view all artifact metadata
    # - Engineer: own artifacts
    # - Reviewer: own artifacts or assigned to them or unassigned pending review
    if current_user.role == Role.ENGINEER.value:
        query = query.where(Artifact.owner_id == current_user.id)
    elif current_user.role == Role.REVIEWER.value:
        query = query.where(
            (Artifact.owner_id == current_user.id)
            | (Artifact.reviewer_id == current_user.id)
            | (Artifact.reviewer_id.is_(None))
        )

    query = query.order_by(desc(Artifact.created_at)).offset(offset).limit(limit)
    records = db.execute(query).scalars().all()

    results: List[ArtifactDetailResponse] = []
    for art in records:
        val_list = None
        if art.validation_json:
            try:
                val_list = json.loads(art.validation_json)
            except Exception:
                val_list = None

        results.append(
            ArtifactDetailResponse(
                id=art.id,
                task_id=art.task_id,
                owner_id=art.owner_id,
                kind=art.kind,
                filename=art.filename,
                sha256=art.sha256,
                status=art.status,
                validation_results=val_list,
                reviewer_id=art.reviewer_id,
                reviewed_at=art.reviewed_at.isoformat() if art.reviewed_at else None,
                review_comment=art.review_comment,
                created_at=art.created_at.isoformat(),
            )
        )

    return results


@router.get("/{artifact_id}", response_model=ArtifactDetailResponse)
async def get_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ArtifactDetailResponse:
    """Get artifact metadata, validation checklist, and review status."""
    artifact = db.execute(select(Artifact).where(Artifact.id == artifact_id)).scalar_one_or_none()
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Artifact '{artifact_id}' not found"}},
        )

    allowed, reason = can_access_artifact(current_user, artifact)
    if not allowed:
        log_event(
            event_type="access_denied",
            status="denied",
            user_id=current_user.id,
            role=current_user.role,
            details={"artifact_id": artifact_id, "reason": reason},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": reason}},
        )

    val_list = None
    if artifact.validation_json:
        try:
            val_list = json.loads(artifact.validation_json)
        except Exception:
            val_list = None

    return ArtifactDetailResponse(
        id=artifact.id,
        task_id=artifact.task_id,
        owner_id=artifact.owner_id,
        kind=artifact.kind,
        filename=artifact.filename,
        sha256=artifact.sha256,
        status=artifact.status,
        validation_results=val_list,
        reviewer_id=artifact.reviewer_id,
        reviewed_at=artifact.reviewed_at.isoformat() if artifact.reviewed_at else None,
        review_comment=artifact.review_comment,
        created_at=artifact.created_at.isoformat(),
    )


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download deliverable file as attachment with strict RBAC enforcement.
    
    SEC-19: Auditor role strictly prohibited (403 Forbidden).
    SEC-20: Reviewer prohibited if assigned to another reviewer (403 Forbidden).
    Path is strictly confined to DATA_DIR/outputs.
    """
    settings = get_settings()

    artifact = db.execute(select(Artifact).where(Artifact.id == artifact_id)).scalar_one_or_none()
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Artifact '{artifact_id}' not found"}},
        )

    allowed, reason = can_download_artifact(current_user, artifact)
    if not allowed:
        log_event(
            event_type="access_denied",
            status="denied",
            user_id=current_user.id,
            role=current_user.role,
            details={"artifact_id": artifact_id, "reason": reason},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": reason}},
        )

    try:
        # Confine path to allowed outputs directory
        allowed_dir = Path(settings.DATA_DIR) / "outputs"
        file_path = safe_path(artifact.stored_path, [allowed_dir])
    except AccessDenied as e:
        logger.error(f"Path traversal attempt downloading artifact {artifact_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Access outside outputs directory denied"}},
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "FILE_NOT_FOUND", "message": "Artifact file not found on disk"}},
        )

    # Determine media type based on deliverable kind
    media_types = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "code": "text/plain",
        "py": "text/x-python",
        "txt": "text/plain",
        "csv": "text/csv",
    }
    media_type = media_types.get(artifact.kind.lower(), "application/octet-stream")

    log_event(
        event_type="tool_call",
        status="ok",
        user_id=current_user.id,
        role=current_user.role,
        tool="download_artifact",
        details={
            "artifact_id": artifact.id,
            "filename": artifact.filename,
            "sha256": artifact.sha256,
        },
    )

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=artifact.filename,
        headers={"Content-Disposition": f'attachment; filename="{artifact.filename}"'},
    )


class ReviewRequest(BaseModel):
    """Payload schema for human review decisions."""
    decision: Literal["approve", "reject", "changes_requested"]
    comment: str


@router.post("/{artifact_id}/review", response_model=ArtifactDetailResponse)
async def review_artifact(
    artifact_id: str,
    payload: ReviewRequest,
    current_user: User = Depends(require_role(Role.REVIEWER)),
    db: Session = Depends(get_db),
) -> ArtifactDetailResponse:
    """Submit human review decision for an artifact deliverable.
    
    SEC-11 Enforcement:
    - Only 'reviewer' role is authorized.
    - Authors cannot review or approve their own artifacts (403 Forbidden).
    - Admins cannot review or approve artifacts (403 Forbidden).
    """
    artifact = db.execute(select(Artifact).where(Artifact.id == artifact_id)).scalar_one_or_none()
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Artifact '{artifact_id}' not found"}},
        )

    # Check segregation of duties
    can_review, reason = can_review_artifact(current_user, artifact)
    if not can_review:
        log_event(
            event_type="access_denied",
            status="denied",
            user_id=current_user.id,
            role=current_user.role,
            details={"artifact_id": artifact_id, "reason": reason, "decision_attempted": payload.decision},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": reason}},
        )

    # Map decision to database status
    decision_status_map = {
        "approve": "APPROVED",
        "reject": "REJECTED",
        "changes_requested": "CHANGES_REQUESTED",
    }
    new_status = decision_status_map[payload.decision]

    artifact.status = new_status
    artifact.reviewer_id = current_user.id
    artifact.reviewed_at = datetime.now(timezone.utc)
    artifact.review_comment = payload.comment

    db.commit()
    db.refresh(artifact)

    # Record review_decision in hash-chained audit log
    log_event(
        event_type="review_decision",
        status="ok",
        user_id=current_user.id,
        role=current_user.role,
        details={
            "artifact_id": artifact.id,
            "decision": payload.decision,
            "new_status": new_status,
            "task_id": artifact.task_id,
            "comment_length": len(payload.comment),
        },
    )

    val_list = None
    if artifact.validation_json:
        try:
            val_list = json.loads(artifact.validation_json)
        except Exception:
            val_list = None

    return ArtifactDetailResponse(
        id=artifact.id,
        task_id=artifact.task_id,
        owner_id=artifact.owner_id,
        kind=artifact.kind,
        filename=artifact.filename,
        sha256=artifact.sha256,
        status=artifact.status,
        validation_results=val_list,
        reviewer_id=artifact.reviewer_id,
        reviewed_at=artifact.reviewed_at.isoformat() if artifact.reviewed_at else None,
        review_comment=artifact.review_comment,
        created_at=artifact.created_at.isoformat(),
    )


@review_router.get("/queue", response_model=List[ArtifactDetailResponse])
async def get_review_queue(
    current_user: User = Depends(require_role(Role.REVIEWER)),
    db: Session = Depends(get_db),
) -> List[ArtifactDetailResponse]:
    """List artifacts awaiting human review (reviewer role only)."""
    query = (
        select(Artifact)
        .where(Artifact.status == "PENDING_REVIEW")
        .order_by(desc(Artifact.created_at))
    )
    records = db.execute(query).scalars().all()

    results: List[ArtifactDetailResponse] = []
    for art in records:
        val_list = None
        if art.validation_json:
            try:
                val_list = json.loads(art.validation_json)
            except Exception:
                val_list = None

        results.append(
            ArtifactDetailResponse(
                id=art.id,
                task_id=art.task_id,
                owner_id=art.owner_id,
                kind=art.kind,
                filename=art.filename,
                sha256=art.sha256,
                status=art.status,
                validation_results=val_list,
                reviewer_id=art.reviewer_id,
                reviewed_at=art.reviewed_at.isoformat() if art.reviewed_at else None,
                review_comment=art.review_comment,
                created_at=art.created_at.isoformat(),
            )
        )

    return results
