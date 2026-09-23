"""Router and Model Selection Engine for Sovereign AI Workbench.

Implements 02_DESIGN_DOC.md §5:
- Deterministic file and keyword classification first, LLM JSON fallback on ambiguity.
- Config-driven routing against models/registry.yaml with fallback handling.
- Audit logging for every model_route event (SEC-14: content-free).
- ModelSwapManager to track active models, unload via Ollama keep_alive: 0,
  and group vision steps contiguously.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import threading
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from pydantic import BaseModel, Field

from agent.state import FileRef, PlanStep
from backend.core.audit import log_event
from models.ollama_client import OllamaClient
from models.registry import ModelRegistry, RoutePlan, get_registry, resolve_route

logger = logging.getLogger("sovereign-workbench.agent.router")


class ClassificationResult(BaseModel):
    """Result of incoming request classification."""

    task_type: str = "other"
    modalities: List[str] = Field(default_factory=lambda: ["text"])
    complexity: str = "medium"
    risk: str = "normal"
    method: Literal["deterministic", "llm_fallback"] = "deterministic"
    reason: str = ""


CLASSIFICATION_SYSTEM_PROMPT = """You are a strict classification engine for an air-gapped industrial AI workbench.
Classify the user's request into the exact JSON schema below.
DO NOT provide any commentary, explanations, or markdown fences outside the JSON.

Allowed task_type values:
- "summary" (summarizing documents or SOPs)
- "rag_qa" (question answering over reference documents)
- "reasoning" (logic, analysis, evaluation)
- "coding" (writing, debugging, or running Python/code)
- "inspection_report" (equipment inspections, defect analysis, approval notes)
- "image_analysis" (photographs, diagrams, visual observations)
- "deliverable" (generating formal Word, Excel, PowerPoint deliverables)
- "calculation" (engineering math, formulas, load calculations)
- "other"

Allowed complexity values:
- "low" (single-turn lookup, straightforward summary)
- "medium" (multi-step analysis, coding, synthesis)
- "high" (multi-modal inspection, complex safety reasoning, formal approval workflow)

Allowed risk values:
- "normal"
- "high_impact" (decisions regarding safety, approval notes, critical infrastructure)

Response format:
{
  "task_type": "summary",
  "complexity": "low",
  "risk": "normal",
  "reason": "Request asks for SOP summary"
}
"""


def detect_file_modality(file_path: str | Path, declared_modality: Optional[str] = None) -> Tuple[str, bool]:
    """Detect file modality and whether it contains embedded raster images.

    Uses PyMuPDF (fitz) character count for PDFs: < 50 chars/page indicates a scanned document.
    """
    path_obj = Path(file_path)
    ext = path_obj.suffix.lower()

    if ext in {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}:
        return ("photograph" if "photo" in path_obj.name.lower() else "image", True)

    if ext == ".pdf":
        if path_obj.exists() and path_obj.is_file():
            try:
                import fitz  # PyMuPDF

                doc = fitz.open(path_obj)
                total_chars = 0
                has_images = False
                page_count = max(1, len(doc))
                for page in doc:
                    text = page.get_text()
                    total_chars += len(text.strip())
                    if page.get_images():
                        has_images = True
                doc.close()

                avg_chars = total_chars / page_count
                if avg_chars < 50:
                    return ("scanned_pdf", has_images)
                return ("native_pdf", has_images)
            except Exception as e:
                logger.warning(f"PyMuPDF inspection failed on {file_path}: {e}")
                if declared_modality:
                    return (declared_modality, False)
                return ("native_pdf", False)
        elif declared_modality:
            return (declared_modality, False)
        return ("native_pdf", False)

    if ext in {".docx"}:
        return ("docx", False)
    if ext in {".xlsx"}:
        return ("xlsx", False)
    if ext in {".csv", ".tsv"}:
        return ("tabular", False)
    if ext in {".pptx"}:
        return ("pptx", False)

    return (declared_modality or "text", False)


def classify_request(
    user_request: str,
    files: Optional[List[Any]] = None,
    client: Optional[Any] = None,
) -> ClassificationResult:
    """Classify incoming task facts using deterministic heuristics first, LLM fallback on ambiguity."""
    req_lower = user_request.lower()
    files = files or []

    # 1. Inspect files
    modalities: Set[str] = set()
    has_any_images = False
    for f in files:
        f_path = getattr(f, "path", None) or (f.get("path") if isinstance(f, dict) else str(f))
        f_mod = getattr(f, "modality", None) or (f.get("modality") if isinstance(f, dict) else None)
        mod, has_img = detect_file_modality(f_path, declared_modality=f_mod)
        modalities.add(mod)
        if has_img:
            has_any_images = True

    # If photo or photograph mentioned in prompt alongside image files
    if any(k in req_lower for k in ["photo", "photograph"]) and "image" in modalities:
        modalities.remove("image")
        modalities.add("photograph")

    # If no files, default modality is text
    if not modalities:
        modalities.add("text")

    # 2. Deterministic keyword heuristics
    is_coding = bool(re.search(r"\b(python|code|script|function|unit test|pytest|implement|coding|bug fix|refactor|programming)\b", req_lower))
    is_inspection = bool(re.search(r"\b(inspection|approval note|inspection report|defect|corrosion|cracking|ndt|weld|turbine|valve|site visit)\b", req_lower))
    is_summary = bool(re.search(r"\b(summarize|summary|sop|overview|standard operating procedure)\b", req_lower))
    is_calculation = bool(re.search(r"\b(calculate|calculation|formula|math|load bearing|equation|compute)\b", req_lower))
    is_image_intent = bool(re.search(r"\b(photo|photograph|picture|visual inspection|drawing|diagram|image)\b", req_lower))
    is_deliverable = bool(re.search(r"\b(docx|xlsx|pptx|slide deck|spreadsheet|formal report|approval note)\b", req_lower))
    is_general_action = bool(re.search(r"\b(fetch|get|read|show|list|find|query|check|run|search|lookup)\b", req_lower))

    # Determine risk
    risk = "normal"
    if any(k in req_lower for k in ["approval note", "approval", "critical", "safety", "nuclear", "hazardous", "defect"]) or is_inspection:
        risk = "high_impact"

    # Match deterministic task_type & complexity
    if "scanned_pdf" in modalities or (is_inspection and is_deliverable):
        return ClassificationResult(
            task_type="inspection_report",
            modalities=sorted(list(modalities)),
            complexity="high",
            risk="high_impact",
            method="deterministic",
            reason="Scanned document or inspection report workflow with deliverable generation",
        )

    if any(m in {"image", "photograph", "drawing", "chart_image"} for m in modalities) or (is_image_intent and has_any_images):
        return ClassificationResult(
            task_type="image_analysis",
            modalities=sorted(list(modalities)),
            complexity="medium",
            risk=risk,
            method="deterministic",
            reason="Image or visual photograph analysis request",
        )

    if is_coding:
        return ClassificationResult(
            task_type="coding",
            modalities=sorted(list(modalities)),
            complexity="medium",
            risk=risk,
            method="deterministic",
            reason="Coding, script development, or automated test generation request",
        )

    if is_summary:
        return ClassificationResult(
            task_type="summary",
            modalities=sorted(list(modalities)),
            complexity="low",
            risk=risk,
            method="deterministic",
            reason="Summary or SOP query request",
        )

    if is_calculation:
        return ClassificationResult(
            task_type="calculation",
            modalities=sorted(list(modalities)),
            complexity="low",
            risk=risk,
            method="deterministic",
            reason="Deterministic mathematical calculation request",
        )

    if is_general_action:
        return ClassificationResult(
            task_type="other",
            modalities=sorted(list(modalities)),
            complexity="low",
            risk=risk,
            method="deterministic",
            reason="General retrieval or execution request",
        )

    # 3. LLM Fallback on ambiguity
    try:
        from agent.nodes.plan import get_active_llm_client
        active_client = client or get_active_llm_client()
    except Exception:
        active_client = client or OllamaClient()
    registry = get_registry()
    default_model = registry.models.get("default")
    model_name = default_model.model if default_model else "qwen3.5:4b"

    prompt_content = f"User Request: {user_request}\nFiles provided: {list(modalities)}"
    try:
        resp = active_client.generate(
            model=model_name,
            prompt=prompt_content,
            system=CLASSIFICATION_SYSTEM_PROMPT,
        )
        raw_text = resp.get("response", "").strip()
        # Clean markdown code fences if present
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
        if match:
            raw_text = match.group(1).strip()

        data = json.loads(raw_text)
        task_type = data.get("task_type", "other")
        valid_tasks = {"summary", "rag_qa", "reasoning", "coding", "inspection_report", "image_analysis", "deliverable", "calculation", "other"}
        if task_type not in valid_tasks:
            task_type = "other"

        complexity = data.get("complexity", "medium")
        if complexity not in {"low", "medium", "high"}:
            complexity = "medium"

        llm_risk = data.get("risk", risk)
        if llm_risk not in {"normal", "high_impact"}:
            llm_risk = risk

        return ClassificationResult(
            task_type=task_type,
            modalities=sorted(list(modalities)),
            complexity=complexity,
            risk=llm_risk,
            method="llm_fallback",
            reason=data.get("reason", "LLM-assisted classification"),
        )
    except Exception as exc:
        logger.warning(f"LLM classification fallback failed: {exc}. Using safe defaults.")
        return ClassificationResult(
            task_type="other",
            modalities=sorted(list(modalities)),
            complexity="medium",
            risk=risk,
            method="llm_fallback",
            reason="Defaulted to general workflow after ambiguous classification",
        )


def route_task(
    facts: Dict[str, Any],
    registry: Optional[ModelRegistry] = None,
    run_id: Optional[str] = None,
    user_id: Optional[str] = None,
    role: Optional[str] = None,
) -> RoutePlan:
    """Resolve facts against registry rules and record an audited model_route event."""
    if registry is None:
        registry = get_registry()

    plan = resolve_route(facts, registry=registry)

    # SEC-14: Content-free audit record. Never log document text or user prompt contents.
    safe_facts = {
        k: list(v) if isinstance(v, (set, list)) else v
        for k, v in facts.items()
        if k != "user_request"
    }

    log_event(
        event_type="model_route",
        status="ok",
        user_id=user_id or "system",
        role=role or "system",
        run_id=run_id or "adhoc",
        model=plan.selected_model,
        details={
            "rule_name": plan.rule_name,
            "models": plan.models,
            "pipeline": plan.pipeline,
            "reason": plan.reason,
            "facts": safe_facts,
        },
    )

    return plan


class ModelSwapManager:
    """Manages active loaded model state, unloads models when switching on VRAM-limited systems,
    and groups vision operations to minimize swaps.
    """

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self._client = ollama_client or OllamaClient()
        self._current_loaded_model: Optional[str] = None
        self._lock = threading.RLock()
        self._swap_history: List[Dict[str, Any]] = []

    def get_current_model(self) -> Optional[str]:
        """Return the currently tracked active loaded model."""
        with self._lock:
            return self._current_loaded_model

    def set_current_model(self, model: str) -> None:
        """Explicitly update the currently tracked loaded model."""
        with self._lock:
            self._current_loaded_model = model

    def unload_model(self, model: str) -> bool:
        """Instruct Ollama to unload model from VRAM by setting keep_alive: 0."""
        try:
            self._client.generate(model=model, prompt="", options={"keep_alive": 0})
            with self._lock:
                if self._current_loaded_model == model:
                    self._current_loaded_model = None
            return True
        except Exception as e:
            logger.warning(f"Failed to unload model '{model}' via Ollama keep_alive: {e}")
            return False

    def switch_to_model(self, target_model: str, auto_unload_previous: bool = True) -> bool:
        """Switch to target model, unloading previous active model if requested."""
        with self._lock:
            if self._current_loaded_model == target_model:
                return True
            prev = self._current_loaded_model
            if prev and auto_unload_previous:
                self.unload_model(prev)
            self._current_loaded_model = target_model
            self._swap_history.append({
                "from": prev,
                "to": target_model,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return True

    def get_status(self) -> Dict[str, Any]:
        """Expose current model swap status for UI and diagnostics."""
        with self._lock:
            return {
                "current_loaded_model": self._current_loaded_model,
                "swap_count": len(self._swap_history),
                "recent_swaps": list(self._swap_history[-10:]),
            }

    @staticmethod
    def group_plan_steps(steps: List[PlanStep]) -> List[PlanStep]:
        """Group vision steps contiguously to minimize model swaps between Gemma and Qwen.

        Preserves relative order among non-vision tools while running vision operations
        together as a batched cluster.
        """
        vision_tools = {"vision_analyze", "vision_analyze_batch"}
        pre_vision_tools = {"ocr_document", "read_file", "search_knowledge"}

        pre_steps = [s for s in steps if s.tool in pre_vision_tools]
        vision_steps = [s for s in steps if s.tool in vision_tools]
        post_steps = [s for s in steps if s.tool not in vision_tools and s.tool not in pre_vision_tools]

        return pre_steps + vision_steps + post_steps


_SWAP_MANAGER_INSTANCE: Optional[ModelSwapManager] = None


def get_model_swap_manager() -> ModelSwapManager:
    """Get singleton ModelSwapManager instance."""
    global _SWAP_MANAGER_INSTANCE
    if _SWAP_MANAGER_INSTANCE is None:
        _SWAP_MANAGER_INSTANCE = ModelSwapManager()
    return _SWAP_MANAGER_INSTANCE
