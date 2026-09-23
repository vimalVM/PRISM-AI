"""Knowledge Base management and clearance-filtered search endpoints.

Implements Phase 4 APIs per 02_DESIGN_DOC.md §8 and 03_SECURITY_AND_ACCESS.md §5.3:
- POST   /api/kb/documents: Ingest a document into the Knowledge Base (Admin only).
- GET    /api/kb/documents: List indexed documents (All authenticated users).
- DELETE /api/kb/documents/{doc_id}: Delete a document (Admin only).
- POST   /api/kb/documents/{doc_id}/reindex: Reindex a document (Admin only).
- POST   /api/kb/search: Search knowledge base within user's clearance (Admin, Engineer, Reviewer).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.db import KBDocument, User, get_db
from backend.core.paths import AccessDenied, safe_path
from backend.core.rbac import (
    Clearance,
    Role,
    get_current_user,
    require_role,
)
from backend.schemas.kb import (
    KBDocumentResponse,
    KBIngestRequest,
    KBSearchRequest,
    KBSearchResponse,
)
from rag.ingest import delete_document, ingest_document
from rag.retrieve import retrieve_chunks

router = APIRouter(prefix="/kb", tags=["knowledge_base"])


@router.get("/documents", response_model=List[KBDocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(default="active"),
) -> List[KBDocumentResponse]:
    """List documents in the knowledge base."""
    stmt = select(KBDocument)
    if status_filter:
        stmt = stmt.where(KBDocument.status == status_filter)
    stmt = stmt.order_by(KBDocument.ingested_at.desc())

    docs = db.execute(stmt).scalars().all()
    results = []
    for d in docs:
        label = Clearance(d.classification).name if d.classification in [0, 1, 2, 3] else "UNKNOWN"
        results.append(
            KBDocumentResponse(
                id=d.id,
                doc_id=d.doc_id,
                filename=d.filename,
                version=d.version,
                classification=d.classification,
                classification_label=label,
                status=d.status,
                chunks=d.chunks,
                uploaded_by=d.uploaded_by,
                ingested_at=d.ingested_at,
            )
        )
    return results


@router.post("/documents", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def ingest_kb_document(
    payload: KBIngestRequest,
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> Dict[str, Any]:
    """Ingest a document into the Knowledge Base (Admin only)."""
    settings = get_settings()
    allowed_roots = settings.input_dirs + [Path("data/knowledge_base")]

    # Validate file path
    try:
        resolved_path = safe_path(payload.file_path, allowed_roots=allowed_roots, must_exist=True)
    except AccessDenied as ad:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ad))

    try:
        result = ingest_document(
            file_path=resolved_path,
            doc_id=payload.doc_id,
            classification=payload.classification,
            version=payload.version,
            uploaded_by=current_user.id,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {exc}",
        )


@router.delete("/documents/{doc_id}", response_model=Dict[str, Any])
async def delete_kb_document(
    doc_id: str,
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> Dict[str, Any]:
    """Delete a document from the Knowledge Base (Admin only)."""
    success = delete_document(doc_id=doc_id, user_id=current_user.id)
    return {"doc_id": doc_id, "deleted": success}


@router.post("/documents/{doc_id}/reindex", response_model=Dict[str, Any])
async def reindex_kb_document(
    doc_id: str,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Reindex an active document in the Knowledge Base (Admin only)."""
    stmt = select(KBDocument).where(KBDocument.doc_id == doc_id, KBDocument.status == "active")
    doc_row = db.execute(stmt).scalar_one_or_none()
    if not doc_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Active document '{doc_id}' not found")

    settings = get_settings()
    candidate_paths = [
        Path(f"data/knowledge_base/{doc_row.filename}"),
        Path(f"data/incoming/{doc_row.filename}"),
    ]
    found_path = None
    for cp in candidate_paths:
        if cp.exists():
            found_path = cp
            break

    if not found_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source file for '{doc_id}' ({doc_row.filename}) not found in storage.",
        )

    result = ingest_document(
        file_path=found_path,
        doc_id=doc_row.doc_id,
        classification=doc_row.classification,
        version=doc_row.version,
        uploaded_by=current_user.id,
    )
    return {"reindexed": True, "details": result}


@router.post("/search", response_model=KBSearchResponse)
async def search_kb(
    payload: KBSearchRequest,
    current_user: User = Depends(require_role(Role.ADMIN, Role.ENGINEER, Role.REVIEWER)),
) -> KBSearchResponse:
    """Search knowledge base strictly within the caller's authenticated clearance."""
    chunks = retrieve_chunks(
        query=payload.query,
        user_clearance=current_user.clearance,
        k=payload.k or 5,
        doc_id=payload.doc_id,
        user_id=current_user.id,
        role=current_user.role,
    )

    return KBSearchResponse(
        query=payload.query,
        total=len(chunks),
        chunks=chunks,
    )
