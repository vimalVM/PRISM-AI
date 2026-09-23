"""Unit tests for document chunking and metadata preservation.

Tests paragraph/heading-aware text splitting and table chunking with repeated headers.
"""

import pytest

from rag.chunking import chunk_table, chunk_text


def test_chunk_text_heading_aware():
    sample_text = """# Executive Summary
This is the high level summary of the engineering facility.

# Operational Procedures
Step 1: Check baseline electrical power.
Step 2: Inspect hydraulic pressure.

## Emergency Actions
If pressure exceeds threshold, activate isolation valve immediately.
"""
    chunks = chunk_text(
        text=sample_text,
        doc_id="DOC-TEST-1",
        filename="summary.md",
        doc_version=1,
        classification=1,
        page=1,
        target_tokens=40,  # Small target to force splitting
        overlap_tokens=10,
    )

    assert len(chunks) >= 2
    for c in chunks:
        assert c.doc_id == "DOC-TEST-1"
        assert c.doc_version == 1
        assert c.classification == 1
        assert len(c.content_hash) == 64
        assert not c.superseded
        assert c.section in ["Executive Summary", "Operational Procedures", "Emergency Actions", "General"]


def test_chunk_table_repeats_headers():
    headers = ["Component", "Max Pressure (bar)", "Inspection Interval"]
    rows = [
        [f"Valve-{i}", f"{100 + i}", f"{i * 6} months"]
        for i in range(1, 35)
    ]

    chunks = chunk_table(
        headers=headers,
        rows=rows,
        doc_id="DOC-TABLE-1",
        filename="valves.xlsx",
        doc_version=1,
        classification=2,
        page=1,
        section="Pressure Valves",
        max_rows_per_chunk=10,
    )

    assert len(chunks) == 4
    for c in chunks:
        assert c.is_table is True
        assert c.classification == 2
        # Every chunk must contain the repeated headers
        assert "Component | Max Pressure (bar) | Inspection Interval" in c.text
        assert "Table (Pressure Valves):" in c.text
