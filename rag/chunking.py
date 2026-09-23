"""Document chunking and provenance metadata extraction for Sovereign AI Workbench.

Implements 02_DESIGN_DOC.md §8.3:
- Paragraph and heading-aware chunking (600–800 tokens, 80–100 overlap).
- Table chunking with repeated header rows.
- Structured chunk metadata: doc_id, filename, page, section, doc_version, classification, content_hash.
"""

import hashlib
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Normalized chunk representation ready for vector indexing and citation tracking."""

    chunk_id: str
    doc_id: str
    filename: str
    page: int = 1
    section: str = "General"
    doc_version: int = 1
    classification: int = 1  # 0=PUBLIC, 1=INTERNAL, 2=CONFIDENTIAL, 3=RESTRICTED
    text: str
    content_hash: str
    superseded: bool = False
    is_table: bool = False


def _compute_hash(text: str) -> str:
    """Compute SHA-256 hash of chunk text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _estimate_tokens(text: str) -> int:
    """Rough estimation of token count (~4 characters per token)."""
    return max(1, len(text) // 4)


def chunk_text(
    text: str,
    doc_id: str,
    filename: str,
    doc_version: int = 1,
    classification: int = 1,
    page: int = 1,
    initial_section: str = "General",
    target_tokens: int = 700,
    overlap_tokens: int = 80,
) -> List[DocumentChunk]:
    """Split unstructured document text into heading-aware chunks.

    Splits along headings and paragraphs while maintaining target size and overlap.
    """
    if not text.strip():
        return []

    target_chars = target_tokens * 4
    overlap_chars = overlap_tokens * 4

    # Regex detecting Markdown headings (e.g. # Heading, ## Section)
    heading_pattern = re.compile(r"^(#{1,6}\s+.+|[A-Z0-9\.\s]{4,60}:)$", re.MULTILINE)

    paragraphs = re.split(r"\n\s*\n", text)
    chunks: List[DocumentChunk] = []

    current_section = initial_section
    current_buffer: List[str] = []
    current_length = 0

    chunk_seq = 1

    for para in paragraphs:
        cleaned_para = para.strip()
        if not cleaned_para:
            continue

        # Check if paragraph is or starts with a section heading
        lines = cleaned_para.splitlines()
        first_line = lines[0].strip()
        if heading_pattern.match(first_line):
            current_section = first_line.lstrip("#").strip()

        para_len = len(cleaned_para)

        if current_length + para_len > target_chars and current_buffer:
            # Emit current buffer as a chunk
            chunk_content = "\n\n".join(current_buffer)
            c_hash = _compute_hash(chunk_content)
            chunk_id = f"{doc_id}_v{doc_version}_p{page}_c{chunk_seq}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    filename=filename,
                    page=page,
                    section=current_section,
                    doc_version=doc_version,
                    classification=classification,
                    text=chunk_content,
                    content_hash=c_hash,
                    superseded=False,
                    is_table=False,
                )
            )
            chunk_seq += 1

            # Build overlap from trailing content
            overlap_buffer = []
            overlap_len = 0
            for prev_para in reversed(current_buffer):
                if overlap_len + len(prev_para) <= overlap_chars:
                    overlap_buffer.insert(0, prev_para)
                    overlap_len += len(prev_para)
                else:
                    break

            current_buffer = overlap_buffer
            current_length = sum(len(p) for p in current_buffer)

        current_buffer.append(cleaned_para)
        current_length += para_len

    # Flush remaining buffer
    if current_buffer:
        chunk_content = "\n\n".join(current_buffer)
        c_hash = _compute_hash(chunk_content)
        chunk_id = f"{doc_id}_v{doc_version}_p{page}_c{chunk_seq}"
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                filename=filename,
                page=page,
                section=current_section,
                doc_version=doc_version,
                classification=classification,
                text=chunk_content,
                content_hash=c_hash,
                superseded=False,
                is_table=False,
            )
        )

    return chunks


def chunk_table(
    headers: List[str],
    rows: List[List[str]],
    doc_id: str,
    filename: str,
    doc_version: int = 1,
    classification: int = 1,
    page: int = 1,
    section: str = "Table",
    max_rows_per_chunk: int = 25,
) -> List[DocumentChunk]:
    """Chunk structured tabular data, repeating column headers on every chunk."""
    if not headers or not rows:
        return []

    header_line = " | ".join(str(h).strip() for h in headers)
    separator_line = " | ".join(["---"] * len(headers))
    table_header = f"| {header_line} |\n| {separator_line} |"

    chunks: List[DocumentChunk] = []
    chunk_seq = 1

    for i in range(0, len(rows), max_rows_per_chunk):
        batch = rows[i : i + max_rows_per_chunk]
        row_lines = [f"| {' | '.join(str(c).strip() for c in r)} |" for r in batch]
        chunk_content = f"Table ({section}):\n{table_header}\n" + "\n".join(row_lines)

        c_hash = _compute_hash(chunk_content)
        chunk_id = f"{doc_id}_v{doc_version}_p{page}_tbl_{chunk_seq}"

        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                filename=filename,
                page=page,
                section=section,
                doc_version=doc_version,
                classification=classification,
                text=chunk_content,
                content_hash=c_hash,
                superseded=False,
                is_table=True,
            )
        )
        chunk_seq += 1

    return chunks
