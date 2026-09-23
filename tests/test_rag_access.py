"""Security and provenance tests for Knowledge Base RAG (SEC-04 & SEC-05).

SEC-04: Strict retrieval-time clearance filtering (INTERNAL user gets zero RESTRICTED chunks).
SEC-05: Provenance citations and version superseding.
"""

from pathlib import Path
import pytest

from backend.core.rbac import Clearance
from rag.chunking import chunk_text
from rag.ingest import (
    get_chroma_client,
    get_kb_collection,
    ingest_document,
    set_embedding_hook,
)
from rag.retrieve import retrieve_chunks


def mock_embedding_fn(texts):
    """Deterministic fast embedding generator for isolated testing."""
    import hashlib
    vectors = []
    for t in texts:
        h = hashlib.sha256(t.encode()).digest()
        # Create 1024-dim normalized vector
        vec = [(b / 255.0) for b in (h * 32)]
        vectors.append(vec)
    return vectors


@pytest.fixture
def rag_test_env(tmp_path):
    """Set up isolated ChromaDB directory and mock embeddings."""
    chroma_dir = tmp_path / "test_chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    set_embedding_hook(mock_embedding_fn)

    # 1. Create a Public SOP
    sop_pub = tmp_path / "sop_public.txt"
    sop_pub.write_text("SOP-101: General site safety rules. Hard hats must be worn at all times.")

    # 2. Create an Internal SOP
    sop_int = tmp_path / "sop_internal.txt"
    sop_int.write_text("SOP-201: Turbine oil change schedule. Oil pressure must remain between 180 and 220 kPa.")

    # 3. Create a Confidential SOP
    sop_conf = tmp_path / "sop_confidential.txt"
    sop_conf.write_text("SOP-301: Pressure vessel weld tolerances. Maximum general wall thinning is 1.5 mm.")

    # 4. Create a Restricted SOP
    sop_rest = tmp_path / "sop_restricted.txt"
    sop_rest.write_text("SOP-401: Nuclear reactor emergency scram. Coolant outlet temperature threshold is 335.0 C.")

    # Ingest documents with respective classifications
    ingest_document(sop_pub, doc_id="SOP-101", classification=Clearance.PUBLIC.value, version=1, chroma_dir=chroma_dir)
    ingest_document(sop_int, doc_id="SOP-201", classification=Clearance.INTERNAL.value, version=1, chroma_dir=chroma_dir)
    ingest_document(sop_conf, doc_id="SOP-301", classification=Clearance.CONFIDENTIAL.value, version=1, chroma_dir=chroma_dir)
    ingest_document(sop_rest, doc_id="SOP-401", classification=Clearance.RESTRICTED.value, version=1, chroma_dir=chroma_dir)

    yield chroma_dir

    set_embedding_hook(None)


def test_sec_04_rag_access_control_clearance_filtering(rag_test_env):
    """SEC-04: User with INTERNAL clearance gets ZERO chunks from CONFIDENTIAL or RESTRICTED docs.

    Even if the query text matches the RESTRICTED document verbatim.
    """
    chroma_dir = rag_test_env
    query_exact_restricted = "Nuclear reactor emergency scram coolant outlet temperature threshold"

    # Query as INTERNAL user (Clearance = 1)
    internal_results = retrieve_chunks(
        query=query_exact_restricted,
        user_clearance=Clearance.INTERNAL,
        k=10,
        chroma_dir=chroma_dir,
    )

    # Must NOT contain SOP-301 or SOP-401
    retrieved_doc_ids = {c.doc_id for c in internal_results}
    assert "SOP-401" not in retrieved_doc_ids, "CRITICAL: Restricted document leaked to INTERNAL user!"
    assert "SOP-301" not in retrieved_doc_ids, "CRITICAL: Confidential document leaked to INTERNAL user!"

    # All returned chunks must have classification <= Clearance.INTERNAL (1)
    for c in internal_results:
        assert c.classification <= Clearance.INTERNAL.value

    # Now query the exact same query as RESTRICTED user (Clearance = 3)
    restricted_results = retrieve_chunks(
        query=query_exact_restricted,
        user_clearance=Clearance.RESTRICTED,
        k=10,
        chroma_dir=chroma_dir,
    )

    restricted_doc_ids = {c.doc_id for c in restricted_results}
    assert "SOP-401" in restricted_doc_ids, "RESTRICTED user should be able to retrieve SOP-401"


def test_sec_05_version_superseding_and_citations(rag_test_env, tmp_path):
    """SEC-05: When document version increments, old chunks are marked superseded=True.

    Standard retrieval returns only the new version. Citations include document version and section.
    """
    chroma_dir = rag_test_env

    # 1. Update SOP-201 to Version 2
    sop_v2 = tmp_path / "sop_201_v2.txt"
    sop_v2.write_text("SOP-201: Updated turbine lubrication schedule. Oil pressure must remain between 190 and 230 kPa.")

    ingest_document(
        sop_v2,
        doc_id="SOP-201",
        classification=Clearance.INTERNAL.value,
        version=2,
        chroma_dir=chroma_dir,
    )

    # 2. Check collection directly: old version 1 chunks must have superseded=True
    collection = get_kb_collection(chroma_dir)
    all_chunks = collection.get(where={"doc_id": "SOP-201"})

    v1_found = False
    v2_found = False
    for meta in all_chunks["metadatas"]:
        if meta["doc_version"] == 1:
            assert meta["superseded"] is True, "Old version chunk was not marked superseded!"
            v1_found = True
        elif meta["doc_version"] == 2:
            assert meta["superseded"] is False, "New version chunk was incorrectly marked superseded!"
            v2_found = True

    assert v1_found and v2_found

    # 3. Retrieve chunks as INTERNAL user
    retrieved = retrieve_chunks(
        query="turbine lubrication oil pressure",
        user_clearance=Clearance.INTERNAL,
        k=5,
        doc_id="SOP-201",
        chroma_dir=chroma_dir,
    )

    assert len(retrieved) > 0
    for c in retrieved:
        assert c.doc_version == 2
        assert not c.superseded
        # Verifiable citation string
        assert "[SOP-201 v2," in c.citation_str
