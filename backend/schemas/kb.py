"""Pydantic schemas for Knowledge Base management and search APIs.

Implements schemas for 02_DESIGN_DOC.md §8 and 03_SECURITY_AND_ACCESS.md §5.3.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from rag.retrieve import RetrievedChunk


class KBDocumentResponse(BaseModel):
    """Knowledge base document metadata representation."""

    id: str
    doc_id: str
    filename: str
    version: int
    classification: int
    classification_label: str
    status: str
    chunks: int
    uploaded_by: str
    ingested_at: datetime

    model_config = {"from_attributes": True}


class KBSearchRequest(BaseModel):
    """Payload to search knowledge base."""

    query: str = Field(..., min_length=2, max_length=1000, description="Search query string.")
    k: Optional[int] = Field(default=5, ge=1, le=20, description="Max results.")
    doc_id: Optional[str] = Field(default=None, description="Optional doc_id constraint.")


class KBSearchResponse(BaseModel):
    """Search results response with citations."""

    query: str
    total: int
    chunks: List[RetrievedChunk]


class KBIngestRequest(BaseModel):
    """Payload to ingest an existing document file into the knowledge base."""

    doc_id: str = Field(..., min_length=2, max_length=64, description="Document identifier, e.g. SOP-101.")
    file_path: str = Field(..., description="File path relative to data/incoming or data/knowledge_base.")
    classification: int = Field(default=1, ge=0, le=3, description="Classification level (0=PUBLIC, 1=INTERNAL, 2=CONFIDENTIAL, 3=RESTRICTED).")
    version: int = Field(default=1, ge=1, description="Document version number.")
