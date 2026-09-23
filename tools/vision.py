"""Multimodal visual observation tools for Sovereign AI Workbench.

Implements 02_DESIGN_DOC.md §9 and 04_ANTIGRAVITY_BUILD_PLAN.md Phase 6:
- Multimodal analysis using Gemma 4 E4B via the local model registry.
- Strict VisualObservation JSON schema enforcement.
- Engineering safety boundary: observations are explicitly non-authoritative;
  mandatory limitation field and strict 'observed' vs 'inferred' typing.
- Image downscaling to max edge (e.g. 1280 px) via Lanczos filtering.
- One-shot JSON repair retry on malformed model responses.
- Batch analysis mode to minimise local Ollama model swaps.
- Graceful vision failure handling and fallback support.
- Fully audited via @audited_tool with path confinement.
"""

import base64
import io
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from PIL import Image
from pydantic import BaseModel, Field, field_validator

from agent.prompts import VISION_ANALYSIS_SYSTEM_PROMPT, VISION_REPAIR_PROMPT
from backend.core.config import get_settings
from backend.core.paths import AccessDenied, safe_path
from models.ollama_client import OllamaClient
from models.registry import get_registry
from tools.registry import ToolContext, audited_tool

logger = logging.getLogger("sovereign-workbench.vision")

# Model client singleton or test hook override
_OLLAMA_CLIENT: Optional[OllamaClient] = None
_VISION_HOOK: Optional[Any] = None


def set_vision_hook(hook: Optional[Any]) -> None:
    """Override vision generation for fast offline unit tests."""
    global _VISION_HOOK
    _VISION_HOOK = hook


def get_ollama_client() -> OllamaClient:
    """Get active Ollama client instance."""
    global _OLLAMA_CLIENT
    if _OLLAMA_CLIENT is None:
        _OLLAMA_CLIENT = OllamaClient()
    return _OLLAMA_CLIENT


class VisualObservation(BaseModel):
    """Structured visual observation complying with 02_DESIGN_DOC.md §9.3."""

    component: str = Field(description="Name or label of the visible equipment, part, or feature")
    visible_condition: str = Field(description="Qualitative surface appearance, condition, or defect indication")
    source: str = Field(description="Source image identifier or filename, e.g. page_2_image_1.png")
    limitation: str = Field(description="Mandatory note emphasizing this is a non-authoritative visual observation")
    type: Literal["observed", "inferred"] = Field(
        description="Whether the condition is directly visible on the surface ('observed') or deduced ('inferred')"
    )
    confidence: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Model's stated qualitative confidence level (non-calibrated)",
    )

    @field_validator("limitation")
    @classmethod
    def validate_limitation_mandatory(cls, v: str) -> str:
        """Enforce that limitation is present, non-empty, and explicit."""
        if not v or not v.strip():
            raise ValueError("The 'limitation' field is mandatory on all visual observations.")
        return v.strip()

    @field_validator("visible_condition")
    @classmethod
    def validate_no_authoritative_claims(cls, v: str) -> str:
        """Reject observations claiming certified or authoritative engineering measurements."""
        forbidden_terms = [
            "certified measurement",
            "authoritative measurement",
            "exact dimensional proof",
            "legal inspection standard",
        ]
        lower_v = v.lower()
        for term in forbidden_terms:
            if term in lower_v:
                raise ValueError(
                    f"Engineering safety boundary violation: visual observations cannot claim '{term}'."
                )
        return v


class VisionAnalyzeArgs(BaseModel):
    """Input arguments for single-image vision analysis."""

    image_ref: str = Field(description="Path to local image file (within allowed roots)")
    question: Optional[str] = Field(
        default=None,
        description="Optional specific inspection question (e.g. 'Identify weld defects or corrosion pitting')",
    )
    max_edge: int = Field(default=1280, ge=256, le=2048, description="Maximum edge resolution for vision downscaling")


class VisionBatchAnalyzeArgs(BaseModel):
    """Input arguments for batch multimodal analysis."""

    images: List[VisionAnalyzeArgs] = Field(description="List of image analysis requests to execute in a single session")


class VisionAnalyzeResult(BaseModel):
    """Structured visual analysis result for a single image."""

    image_ref: str
    observations: List[VisualObservation] = Field(default_factory=list)
    model: str
    evidence_available: bool = True
    error: Optional[str] = None


class VisionBatchAnalyzeResult(BaseModel):
    """Structured result for batch multimodal analysis."""

    results: List[VisionAnalyzeResult]
    total_images: int
    model: str


def prepare_image(image_input: Union[str, Path, bytes], max_edge: int = 1280) -> Tuple[bytes, str]:
    """Load, validate, downscale, and encode image to JPEG bytes and Base64 string.

    Returns:
        Tuple of (jpeg_bytes, base64_str)
    """
    if isinstance(image_input, (str, Path)):
        raw_bytes = Path(image_input).read_bytes()
    else:
        raw_bytes = image_input

    img = Image.open(io.BytesIO(raw_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size
    if max(width, height) > max_edge:
        scale = max_edge / float(max(width, height))
        new_size = (int(width * scale), int(height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    out_buf = io.BytesIO()
    img.save(out_buf, format="JPEG", quality=90)
    jpeg_bytes = out_buf.getvalue()
    b64_str = base64.b64encode(jpeg_bytes).decode("utf-8")
    return jpeg_bytes, b64_str


def _extract_json_array(text: str) -> Optional[str]:
    """Extract JSON array substring from raw model output."""
    stripped = text.strip()
    # Strip markdown fenced blocks if present
    if stripped.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\[\s*\{.*\}\s*\])\s*```", stripped, re.DOTALL)
        if match:
            return match.group(1).strip()

    # Search for first '[' and matching ']'
    start = stripped.find("[")
    end = stripped.rfind("]")
    if start != -1 and end != -1 and end > start:
        return stripped[start : end + 1]

    return None


def _parse_and_validate_observations(
    json_text: str, source_name: str
) -> Tuple[List[VisualObservation], Optional[str]]:
    """Parse JSON text and validate against VisualObservation schema."""
    try:
        data = json.loads(json_text)
    except Exception as exc:
        return [], f"JSON decode error: {exc}"

    if not isinstance(data, list):
        return [], "Expected a JSON array of observation objects, got a dict or primitive."

    observations: List[VisualObservation] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            return [], f"Item at index {idx} is not a valid JSON object."
        # Ensure source defaults to image filename if omitted by model
        if "source" not in item or not item["source"]:
            item["source"] = source_name
        # Ensure limitation defaults to safe boundary note if omitted
        if "limitation" not in item or not str(item["limitation"]).strip():
            item["limitation"] = "Non-authoritative visual observation; not a certified dimensional measurement."
        try:
            obs = VisualObservation.model_validate(item)
            observations.append(obs)
        except Exception as ve:
            return [], f"Item {idx} schema validation error: {ve}"

    return observations, None


def _get_vision_model_config() -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Retrieve enabled vision model from registry.yaml with fallback resolution."""
    settings = get_settings()
    registry = get_registry(settings.MODEL_REGISTRY_PATH)

    vision_entry = registry.models.get("vision")
    if vision_entry and vision_entry.enabled:
        return vision_entry.model, vision_entry.options

    fallback_entry = registry.models.get("vision_fallback")
    if fallback_entry and fallback_entry.enabled:
        logger.info("Primary vision model disabled; using enabled vision_fallback.")
        return fallback_entry.model, fallback_entry.options

    return None, None


def _execute_vision_inference(
    model_name: str,
    prompt: str,
    system_prompt: str,
    image_b64: str,
    options: Optional[Dict[str, Any]] = None,
) -> str:
    """Send image and prompt to OllamaClient or test hook."""
    global _VISION_HOOK
    if _VISION_HOOK is not None:
        return _VISION_HOOK(model_name, prompt, system_prompt, image_b64)

    client = get_ollama_client()
    resp = client.generate(
        model=model_name,
        prompt=prompt,
        system=system_prompt,
        images=[image_b64],
        options=options,
    )
    return resp.get("response", "")


def _analyze_single_image(
    args: VisionAnalyzeArgs,
    allowed_roots: List[Path],
    model_name: str,
    model_options: Optional[Dict[str, Any]],
) -> VisionAnalyzeResult:
    """Internal helper to analyze one image with downscaling, one-shot repair, and validation."""
    # 1. Path confinement
    resolved_path = safe_path(args.image_ref, allowed_roots=allowed_roots, must_exist=True)
    source_name = resolved_path.name

    # 2. Downscale and encode image
    try:
        _, b64_str = prepare_image(resolved_path, max_edge=args.max_edge)
    except Exception as exc:
        return VisionAnalyzeResult(
            image_ref=args.image_ref,
            observations=[],
            model=model_name,
            evidence_available=False,
            error=f"Failed to load and prepare image: {exc}",
        )

    # 3. Construct prompt
    user_prompt = (
        f"Analyze this technical inspection image ({source_name}).\n"
        f"Question / Focus: {args.question or 'Identify all visible components, surface conditions, irregularities, or defects.'}\n"
        "Provide your findings as a strict JSON array of VisualObservation objects."
    )
    system_prompt = VISION_ANALYSIS_SYSTEM_PROMPT.replace("{source_image}", source_name)

    # 4. First inference attempt
    try:
        raw_response = _execute_vision_inference(
            model_name=model_name,
            prompt=user_prompt,
            system_prompt=system_prompt,
            image_b64=b64_str,
            options=model_options,
        )
    except Exception as exc:
        logger.error(f"Vision model inference failed: {exc}")
        return VisionAnalyzeResult(
            image_ref=args.image_ref,
            observations=[],
            model=model_name,
            evidence_available=False,
            error=f"Model execution error: {exc}",
        )

    # 5. Extract and validate JSON
    extracted_json = _extract_json_array(raw_response)
    observations, err = _parse_and_validate_observations(extracted_json or "", source_name) if extracted_json else ([], "No JSON array found in model response.")

    # 6. One-shot JSON repair retry if invalid
    if err is not None:
        logger.warning(f"Vision output invalid ({err}). Attempting one-shot repair retry.")
        repair_prompt = VISION_REPAIR_PROMPT.format(
            error=err,
            previous_response=raw_response[:1000],
            source_image=source_name,
        )
        try:
            repair_raw = _execute_vision_inference(
                model_name=model_name,
                prompt=repair_prompt,
                system_prompt=system_prompt,
                image_b64=b64_str,
                options=model_options,
            )
            repair_json = _extract_json_array(repair_raw)
            if repair_json:
                repaired_obs, repair_err = _parse_and_validate_observations(repair_json, source_name)
                if repair_err is None:
                    observations = repaired_obs
                    err = None
                else:
                    err = f"Repair validation failed: {repair_err}"
            else:
                err = "Repair attempt did not return a valid JSON array."
        except Exception as repair_exc:
            err = f"Repair retry failed: {repair_exc}"

    if err is not None:
        return VisionAnalyzeResult(
            image_ref=args.image_ref,
            observations=[],
            model=model_name,
            evidence_available=False,
            error=err,
        )

    return VisionAnalyzeResult(
        image_ref=args.image_ref,
        observations=observations,
        model=model_name,
        evidence_available=True,
        error=None,
    )


@audited_tool(
    name="vision_analyze",
    side_effects=False,
    needs_role=None,
    description="Analyze technical photographs or inspection drawings using Gemma 4 E4B vision model.",
)
def vision_analyze(
    args: Union[VisionAnalyzeArgs, Dict[str, Any]], ctx: ToolContext
) -> VisionAnalyzeResult:
    """Execute multimodal vision analysis on a single image."""
    if isinstance(args, dict):
        args = VisionAnalyzeArgs.model_validate(args)

    settings = get_settings()
    allowed_roots = settings.input_dirs + settings.output_dirs

    model_name, model_options = _get_vision_model_config()
    if not model_name:
        return VisionAnalyzeResult(
            image_ref=args.image_ref,
            observations=[],
            model="none",
            evidence_available=False,
            error="Vision model is disabled in registry configuration and no fallback is active.",
        )

    return _analyze_single_image(args, allowed_roots, model_name, model_options)


@audited_tool(
    name="vision_analyze_batch",
    side_effects=False,
    needs_role=None,
    description="Analyze multiple technical images in a single session to minimize model swaps.",
)
def vision_analyze_batch(
    args: Union[VisionBatchAnalyzeArgs, Dict[str, Any]], ctx: ToolContext
) -> VisionBatchAnalyzeResult:
    """Execute multimodal vision analysis over a batch of images."""
    if isinstance(args, dict):
        args = VisionBatchAnalyzeArgs.model_validate(args)

    settings = get_settings()
    allowed_roots = settings.input_dirs + settings.output_dirs

    model_name, model_options = _get_vision_model_config()
    if not model_name:
        results = [
            VisionAnalyzeResult(
                image_ref=item.image_ref,
                observations=[],
                model="none",
                evidence_available=False,
                error="Vision model is disabled in registry configuration.",
            )
            for item in args.images
        ]
        return VisionBatchAnalyzeResult(
            results=results,
            total_images=len(args.images),
            model="none",
        )

    results = []
    for item in args.images:
        res = _analyze_single_image(item, allowed_roots, model_name, model_options)
        results.append(res)

    return VisionBatchAnalyzeResult(
        results=results,
        total_images=len(results),
        model=model_name,
    )
