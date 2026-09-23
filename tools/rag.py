"""Knowledge base search tool for Sovereign AI Workbench agent.

Implements 02_DESIGN_DOC.md §7.3 and SEC-04:
- @audited_tool search_knowledge
- Automatically extracts user clearance and identity from ToolContext
- Returns structured chunk references with verifiable citations
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from rag.retrieve import RetrievedChunk, retrieve_chunks
from tools.registry import ToolContext, audited_tool


class SearchKnowledgeArgs(BaseModel):
    """Input parameters for search_knowledge tool."""

    query: str = Field(..., min_length=2, description="Semantic or keyword query to search internal knowledge base.")
    k: Optional[int] = Field(default=5, ge=1, le=20, description="Maximum number of chunks to retrieve (default 5).")
    doc_id: Optional[str] = Field(default=None, description="Optional doc_id filter to search a specific document.")


class SearchKnowledgeResult(BaseModel):
    """Result returned by search_knowledge tool."""

    query: str
    total_found: int
    chunks: List[RetrievedChunk]


@audited_tool(
    name="search_knowledge",
    side_effects=False,
    needs_role=None,
    description="Search internal organizational documents, SOPs, and manuals within authenticated clearance.",
)
def search_knowledge(args: SearchKnowledgeArgs, ctx: ToolContext) -> SearchKnowledgeResult:
    """Search knowledge base with mandatory clearance enforcement."""
    results = retrieve_chunks(
        query=args.query,
        user_clearance=ctx.clearance,
        k=args.k or 5,
        doc_id=args.doc_id,
        user_id=ctx.user_id,
        role=ctx.role,
    )

    return SearchKnowledgeResult(
        query=args.query,
        total_found=len(results),
        chunks=results,
    )
