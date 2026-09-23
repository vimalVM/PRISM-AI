"""Comprehensive unit and integration tests for Agent Router & Model Selection.

Tests all scenarios in docs/05_TEST_EVAL_DEMO.md §4.1:
1. "Summarize this SOP." -> rule text_default -> Qwen3.5 4B
2. "Analyze this inspection photograph." + photo -> rule image_or_photo -> Gemma 4 E4B + Qwen
3. "Read this scanned inspection report and prepare an approval note." + scanned PDF -> rule scanned_document -> OCR + Gemma + Qwen
4. "Write a Python function that ... with tests." -> rule coding -> Qwen3.5 4B
5. Registry: enable future_strong_reasoning + high complexity -> rule complex_reasoning selects bonsai2:27b (zero code change)
6. Registry: disable Gemma -> vision route skipped / marked unavailable with audit note
Plus:
- Deterministic vs LLM fallback classification
- ModelSwapManager tracking, unloading, and step grouping
- Intake node LangGraph integration
"""

import json
from pathlib import Path
import pytest
from sqlalchemy import select

from agent.graph import run_agent
from agent.nodes.intake import intake_node
from agent.nodes.plan import set_llm_client_override
from agent.router import (
    ClassificationResult,
    ModelSwapManager,
    classify_request,
    detect_file_modality,
    get_model_swap_manager,
    route_task,
)
from agent.state import AgentState, FileRef, PlanStep
from backend.core.audit import log_event, verify_chain
from backend.core.db import AuditLog, get_session_factory
from models.registry import ModelRegistry, get_registry, load_registry, reload_registry, resolve_route


@pytest.fixture
def clean_audit():
    """Ensure clean audit state before and after test."""
    yield
    # No action needed, SQLite rolls over in tests


# ==============================================================================
# 1. Deterministic file modality detection tests
# ==============================================================================

def test_detect_file_modality_images(tmp_path):
    img_file = tmp_path / "turbine_blade.jpg"
    img_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
    mod, has_img = detect_file_modality(img_file)
    assert mod == "image"
    assert has_img is True

    photo_file = tmp_path / "site_photo_01.png"
    photo_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)
    mod2, has_img2 = detect_file_modality(photo_file)
    assert mod2 == "photograph"
    assert has_img2 is True


def test_detect_file_modality_pdf(tmp_path):
    import fitz

    # 1. Create a native text PDF (many characters)
    native_pdf = tmp_path / "sop_native.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Standard Operating Procedure " * 20)
    doc.save(str(native_pdf))
    doc.close()

    mod, has_img = detect_file_modality(native_pdf)
    assert mod == "native_pdf"

    # 2. Create a scanned-like PDF (<50 chars total)
    scanned_pdf = tmp_path / "scanned_report.pdf"
    doc2 = fitz.open()
    page2 = doc2.new_page()
    page2.insert_text((50, 50), "p.1")  # only 3 chars
    doc2.save(str(scanned_pdf))
    doc2.close()

    mod2, has_img2 = detect_file_modality(scanned_pdf)
    assert mod2 == "scanned_pdf"


def test_detect_file_modality_office_formats():
    assert detect_file_modality("report.docx")[0] == "docx"
    assert detect_file_modality("data.xlsx")[0] == "xlsx"
    assert detect_file_modality("records.csv")[0] == "tabular"
    assert detect_file_modality("deck.pptx")[0] == "pptx"
    assert detect_file_modality("notes.txt")[0] == "text"


# ==============================================================================
# 2. The 6 Required Routing Scenarios from docs/05 §4.1
# ==============================================================================

def test_scenario_1_summarize_sop():
    """Scenario 1: 'Summarize this SOP.' -> rule text_default -> Qwen3.5 4B"""
    req = "Summarize this SOP."
    classification = classify_request(req, files=[])
    assert classification.task_type == "summary"

    facts = {
        "user_request": req,
        "task_type": classification.task_type,
        "modality": classification.modalities,
        "complexity": classification.complexity,
    }

    plan = route_task(facts, run_id="scen-1", user_id="eng1", role="engineer")
    assert plan.rule_name == "text_default"
    assert plan.selected_model == "qwen3.5:4b"
    assert "default" in plan.reason.lower() or "text_default" in plan.reason

    # Verify audit log
    with get_session_factory()() as session:
        audit_row = session.execute(
            select(AuditLog).where(AuditLog.run_id == "scen-1").order_by(AuditLog.id.desc())
        ).scalars().first()
        assert audit_row is not None
        assert audit_row.event_type == "model_route"
        assert audit_row.model == "qwen3.5:4b"
        data = json.loads(audit_row.details_json)
        assert data["rule_name"] == "text_default"
        # SEC-14: Content-free check
        assert "user_request" not in data.get("facts", {})


def test_scenario_2_analyze_photograph(tmp_path):
    """Scenario 2: 'Analyze this inspection photograph.' + photo -> rule image_or_photo -> Gemma 4 E4B + Qwen"""
    photo_path = tmp_path / "inspection_photo.jpg"
    photo_path.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 10)

    f_ref = FileRef(id="f-photo-1", path=str(photo_path), modality="photograph")
    req = "Analyze this inspection photograph."
    classification = classify_request(req, files=[f_ref])

    assert "photograph" in classification.modalities or "image" in classification.modalities

    facts = {
        "user_request": req,
        "task_type": classification.task_type,
        "modality": classification.modalities,
        "complexity": classification.complexity,
    }

    plan = route_task(facts, run_id="scen-2", user_id="eng1", role="engineer")
    assert plan.rule_name == "image_or_photo"
    assert "gemma4:e4b" in plan.models
    assert "qwen3.5:4b" in plan.models
    assert "vision" in plan.pipeline


def test_scenario_3_scanned_inspection_report(tmp_path):
    """Scenario 3: 'Read this scanned inspection report and prepare an approval note.' + scanned PDF -> rule scanned_document -> OCR + Gemma + Qwen"""
    import fitz

    scanned_path = tmp_path / "scanned_report.pdf"
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Doc #9")  # sparse chars -> scanned
    doc.save(str(scanned_path))
    doc.close()

    f_ref = FileRef(id="f-scan-1", path=str(scanned_path), modality="scanned_pdf")
    req = "Read this scanned inspection report and prepare an approval note."
    classification = classify_request(req, files=[f_ref])

    assert classification.task_type == "inspection_report"
    assert classification.risk == "high_impact"
    assert "scanned_pdf" in classification.modalities

    facts = {
        "user_request": req,
        "task_type": classification.task_type,
        "modality": classification.modalities,
        "complexity": classification.complexity,
    }

    plan = route_task(facts, run_id="scen-3", user_id="eng1", role="engineer")
    assert plan.rule_name == "scanned_document"
    assert "ocr" in plan.pipeline
    assert "vision" in plan.pipeline
    assert "gemma4:e4b" in plan.models
    assert "qwen3.5:4b" in plan.models


def test_scenario_4_coding_task():
    """Scenario 4: 'Write a Python function that ... with tests.' -> rule coding -> Qwen3.5 4B"""
    req = "Write a Python function that computes flow rate with tests."
    classification = classify_request(req, files=[])

    assert classification.task_type == "coding"

    facts = {
        "user_request": req,
        "task_type": classification.task_type,
        "modality": classification.modalities,
        "complexity": classification.complexity,
    }

    plan = route_task(facts, run_id="scen-4", user_id="eng1", role="engineer")
    assert plan.rule_name == "coding"
    assert plan.selected_model == "qwen3.5:4b"


def test_scenario_5_zero_code_change_strong_reasoning():
    """Scenario 5: Registry: enable future_strong_reasoning + high complexity -> complex_reasoning selects bonsai2:27b with ZERO code change."""
    registry = get_registry(force_reload=True)

    # 1. When disabled in registry, high complexity falls back to default
    facts_high = {"complexity": ["high"], "task_type": "reasoning"}
    plan_disabled = resolve_route(facts_high, registry=registry)
    assert plan_disabled.rule_name == "complex_reasoning"
    assert plan_disabled.selected_model == "qwen3.5:4b"
    assert "disabled, fallback to 'default'" in plan_disabled.reason

    # 2. Dynamically enable future_strong_reasoning (simulating registry.yaml edit or reload)
    registry_copy = registry.model_copy(deep=True)
    registry_copy.models["future_strong_reasoning"].enabled = True

    plan_enabled = resolve_route(facts_high, registry=registry_copy)
    assert plan_enabled.rule_name == "complex_reasoning"
    assert plan_enabled.selected_model == "bonsai2:27b"
    assert "bonsai2:27b" in plan_enabled.models
    assert "targeting 'future_strong_reasoning'" in plan_enabled.reason


def test_scenario_6_vision_disabled_graceful_handling():
    """Scenario 6: Registry: disable Gemma -> vision route skipped with audit note; user sees vision unavailable."""
    registry = get_registry(force_reload=True)
    registry_copy = registry.model_copy(deep=True)

    # Disable Gemma in registry
    registry_copy.models["vision"].enabled = False

    facts = {"modality": ["photograph"]}
    plan = route_task(facts, registry=registry_copy, run_id="scen-6", user_id="eng1", role="engineer")

    assert plan.rule_name == "image_or_photo"
    assert "vision unavailable" in plan.reason
    assert "vision" not in plan.pipeline
    # Still resolves to primary reasoning model so the workflow doesn't crash
    assert plan.selected_model == "qwen3.5:4b"


# ==============================================================================
# 3. LLM Fallback Classification Tests
# ==============================================================================

class MockClassificationLLM:
    """Mock LLM returning structured classification JSON."""

    def __init__(self, response_text: str):
        self.response_text = response_text

    def generate(self, model: str, prompt: str, system: str = None, **kwargs):
        return {"response": self.response_text}


def test_classify_request_llm_fallback_success():
    """Ambiguous query triggers LLM fallback and parses structured JSON."""
    ambiguous_req = "Perform an assessment of the current thermal conditions."
    mock_json = json.dumps({
        "task_type": "reasoning",
        "complexity": "medium",
        "risk": "normal",
        "reason": "Engineering thermal analysis inquiry",
    })
    mock_llm = MockClassificationLLM(mock_json)

    res = classify_request(ambiguous_req, files=[], client=mock_llm)
    assert res.method == "llm_fallback"
    assert res.task_type == "reasoning"
    assert res.complexity == "medium"
    assert res.risk == "normal"
    assert "Engineering thermal analysis" in res.reason


def test_classify_request_llm_fallback_failure_safely_defaults():
    """Malformed LLM response triggers safe default values."""
    ambiguous_req = "Something random with no keywords."
    mock_llm = MockClassificationLLM("I am sorry, I cannot format as JSON.")

    res = classify_request(ambiguous_req, files=[], client=mock_llm)
    assert res.method == "llm_fallback"
    assert res.task_type == "other"
    assert res.complexity == "medium"
    assert res.risk == "normal"
    assert "Defaulted to general workflow" in res.reason


# ==============================================================================
# 4. ModelSwapManager Tests
# ==============================================================================

class MockOllamaClientWithUnload:
    def __init__(self):
        self.unloaded_models = []

    def generate(self, model: str, prompt: str, options: dict = None, **kwargs):
        if options and options.get("keep_alive") == 0:
            self.unloaded_models.append(model)
        return {"response": "ok"}


def test_model_swap_manager():
    fake_client = MockOllamaClientWithUnload()
    mgr = ModelSwapManager(ollama_client=fake_client)

    # Initial state
    assert mgr.get_current_model() is None

    # Switch to Qwen
    mgr.switch_to_model("qwen3.5:4b")
    assert mgr.get_current_model() == "qwen3.5:4b"

    # Switch to Gemma -> unloads Qwen
    mgr.switch_to_model("gemma4:e4b")
    assert mgr.get_current_model() == "gemma4:e4b"
    assert "qwen3.5:4b" in fake_client.unloaded_models

    # Explicit unload
    mgr.unload_model("gemma4:e4b")
    assert mgr.get_current_model() is None
    assert "gemma4:e4b" in fake_client.unloaded_models

    # Status check
    status = mgr.get_status()
    assert status["swap_count"] == 2
    assert len(status["recent_swaps"]) == 2


def test_model_swap_manager_group_plan_steps():
    """Ensure vision steps are grouped contiguously to avoid alternating swaps."""
    steps = [
        PlanStep(step_id=1, tool="read_file", args={"path": "a.txt"}),
        PlanStep(step_id=2, tool="vision_analyze", args={"image_path": "img1.png"}),
        PlanStep(step_id=3, tool="search_knowledge", args={"query": "test"}),
        PlanStep(step_id=4, tool="vision_analyze_batch", args={"image_paths": ["img2.png"]}),
        PlanStep(step_id=5, tool="write_file", args={"path": "out.txt", "content": "done"}),
    ]

    grouped = ModelSwapManager.group_plan_steps(steps)
    tool_sequence = [s.tool for s in grouped]

    # Pre-tools first
    assert tool_sequence[0] in {"read_file", "search_knowledge"}
    assert tool_sequence[1] in {"read_file", "search_knowledge"}
    # Vision steps grouped contiguously
    assert tool_sequence[2] in {"vision_analyze", "vision_analyze_batch"}
    assert tool_sequence[3] in {"vision_analyze", "vision_analyze_batch"}
    # Post tools last
    assert tool_sequence[4] == "write_file"


# ==============================================================================
# 5. LangGraph Intake Node Integration Test
# ==============================================================================

def test_intake_node_integration():
    state: AgentState = {
        "run_id": "test-intake-run",
        "user_id": "alice",
        "user_role": "engineer",
        "user_request": "Write a Python script to compute stress concentration.",
        "uploaded_files": [],
    }

    res = intake_node(state)
    assert res["task_type"] == "coding"
    assert res["selected_model"] == "qwen3.5:4b"
    assert "coding" in res["route_reason"].lower()

    # ModelSwapManager updated
    swap_mgr = get_model_swap_manager()
    assert swap_mgr.get_current_model() == "qwen3.5:4b"

    # Audit chain intact
    valid, err = verify_chain()
    assert valid is True
    assert err is None
