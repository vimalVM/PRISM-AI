"""Unit tests for the search_knowledge audited tool.

Tests tool invocation, clearance inheritance from ToolContext, and audit records.
"""

from pathlib import Path
import pytest

from backend.core.config import get_settings
from backend.core.rbac import Clearance
from rag.ingest import ingest_document, set_embedding_hook
from tools.rag import SearchKnowledgeArgs, search_knowledge
from tools.registry import ToolContext, get_tool_registry


def mock_embedding_fn(texts):
    import hashlib
    vectors = []
    for t in texts:
        h = hashlib.sha256(t.encode()).digest()
        vectors.append([(b / 255.0) for b in (h * 32)])
    return vectors


@pytest.fixture
def rag_tool_env(tmp_path, monkeypatch):
    chroma_dir = tmp_path / "chroma_tool"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(get_settings(), "CHROMA_DIR", str(chroma_dir))
    set_embedding_hook(mock_embedding_fn)

    doc_file = tmp_path / "sop_tool.txt"
    doc_file.write_text("SOP-501: Emergency generator backup procedures and power startup.")
    ingest_document(
        doc_file,
        doc_id="SOP-501",
        classification=Clearance.CONFIDENTIAL.value,
        version=1,
        chroma_dir=chroma_dir,
    )

    yield chroma_dir
    set_embedding_hook(None)


def test_search_knowledge_tool_execution(rag_tool_env):
    reg = get_tool_registry()
    assert reg.is_registered("search_knowledge")

    # Call with CONFIDENTIAL clearance
    conf_ctx = ToolContext(
        user_id="user_conf_1",
        role="engineer",
        clearance=Clearance.CONFIDENTIAL,
        run_id="run_rag_tool_01",
    )

    args = SearchKnowledgeArgs(query="emergency generator backup", k=3)
    res = reg.execute("search_knowledge", args, conf_ctx)

    assert res.total_found > 0
    assert any(c.doc_id == "SOP-501" for c in res.chunks)
    assert "[SOP-501 v1," in res.chunks[0].citation_str


def test_search_knowledge_tool_blocks_low_clearance(rag_tool_env):
    reg = get_tool_registry()

    # Call with PUBLIC clearance (0) on a CONFIDENTIAL doc (2)
    public_ctx = ToolContext(
        user_id="user_pub_1",
        role="engineer",
        clearance=Clearance.PUBLIC,
        run_id="run_rag_tool_02",
    )

    args = SearchKnowledgeArgs(query="emergency generator backup", k=3)
    res = reg.execute("search_knowledge", args, public_ctx)

    # Must return 0 chunks from the CONFIDENTIAL doc
    assert not any(c.doc_id == "SOP-501" for c in res.chunks)
