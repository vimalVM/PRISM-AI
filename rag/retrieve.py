"""Clearance-filtered vector retrieval with provenance and citation generation.

Implements SEC-04 and 02_DESIGN_DOC.md §8.5:
- Enforces strict server-side clearance filtering in ChromaDB where clause.
- Permitted classifications: chunk.classification <= user.clearance.
- Excludes superseded chunks (superseded == False).
- Produces verifiable citation strings ([doc_id v{version}, p.{page}, §{section}]).
- Audits retrieval actions omitting sensitive query text.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from backend.core.audit import log_event
from backend.core.rbac import Clearance
from rag.ingest import compute_embeddings, get_kb_collection


class RetrievedChunk(BaseModel):
    """Structured chunk result with provenance and formatted citation."""

    chunk_id: str
    doc_id: str
    filename: str
    page: int
    section: str
    doc_version: int
    classification: int
    text: str
    citation_str: str
    superseded: bool = False
    distance: Optional[float] = None


def resolve_clearance_int(clearance: Union[int, str, Clearance]) -> int:
    """Normalize clearance to integer (0=PUBLIC, 1=INTERNAL, 2=CONFIDENTIAL, 3=RESTRICTED)."""
    if isinstance(clearance, Clearance):
        return int(clearance.value)
    if isinstance(clearance, int):
        return clearance
    if isinstance(clearance, str):
        c_upper = clearance.strip().upper()
        if hasattr(Clearance, c_upper):
            return int(getattr(Clearance, c_upper).value)
        try:
            return int(clearance)
        except ValueError:
            return Clearance.INTERNAL.value
    return Clearance.PUBLIC.value


def retrieve_chunks(
    query: str,
    user_clearance: Union[int, str, Clearance],
    k: int = 5,
    doc_id: Optional[str] = None,
    user_id: Optional[str] = None,
    role: Optional[str] = None,
    chroma_dir: Optional[Union[str, Path]] = None,
) -> List[RetrievedChunk]:
    """Execute clearance-controlled vector search against local Knowledge Base.

    CRITICAL SECURITY INVARIANT (SEC-04):
    The vector search filter enforces classification <= user_clearance at the database layer.
    A user cannot retrieve chunks above their clearance under any circumstance.
    """
    user_clearance_int = resolve_clearance_int(user_clearance)

    # Allowed classifications are all integer levels <= user's clearance
    allowed_levels = [lvl.value for lvl in Clearance if lvl.value <= user_clearance_int]

    # Build server-side where filter
    where_conditions: List[Dict[str, Any]] = [
        {"classification": {"$in": allowed_levels}},
        {"superseded": {"$eq": False}},
    ]

    if doc_id:
        where_conditions.append({"doc_id": {"$eq": doc_id}})

    where_filter = {"$and": where_conditions}

    from backend.core.config import get_settings
    settings = get_settings()
    effective_chroma_dir = chroma_dir or settings.CHROMA_DIR

    collection = get_kb_collection(effective_chroma_dir)
    count = collection.count()
    if count == 0:
        return []

    # Limit k to available records
    n_results = min(k, count)

    # Compute dense query embedding
    query_embeddings = compute_embeddings([query])
    if not query_embeddings:
        return []

    res = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        where=where_filter,
    )

    retrieved: List[RetrievedChunk] = []

    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0] if res.get("distances") else [None] * len(ids)

    for i in range(len(ids)):
        m = metas[i] if i < len(metas) else {}
        d_id = m.get("doc_id", "UNKNOWN")
        v = m.get("doc_version", 1)
        p = m.get("page", 1)
        sec = m.get("section", "General")
        c_class = m.get("classification", 1)
        fname = m.get("filename", "document")
        is_superseded = m.get("superseded", False)
        dist = distances[i] if i < len(distances) else None

        citation = f"[{d_id} v{v}, p.{p}, §{sec}]"

        retrieved.append(
            RetrievedChunk(
                chunk_id=ids[i],
                doc_id=d_id,
                filename=fname,
                page=p,
                section=sec,
                doc_version=v,
                classification=c_class,
                text=docs[i] if i < len(docs) else "",
                citation_str=citation,
                superseded=is_superseded,
                distance=dist,
            )
        )

    # Cryptographic audit logging (SEC-14: content-free details)
    log_event(
        event_type="rag_retrieval",
        status="ok",
        user_id=user_id or "system",
        role=role or "engineer",
        details={
            "k": k,
            "returned_count": len(retrieved),
            "max_clearance_applied": user_clearance_int,
            "doc_ids": sorted(list({c.doc_id for c in retrieved})),
            "filter_doc_id": doc_id,
        },
    )

    return retrieved
