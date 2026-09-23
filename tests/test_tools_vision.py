"""Unit and integration tests for multimodal vision analysis tool (tools/vision.py).

Verifies Phase 6 requirements:
- VisualObservation strict schema, mandatory limitation field, and observed/inferred typing.
- Engineering safety boundary rejection of certified measurement claims.
- High-fidelity image downscaling to max edge resolution.
- Vision analysis with mocked Ollama client and audit logging.
- One-shot JSON repair on malformed model outputs.
- Safe failure handling when repair fails (evidence_available=False).
- Batch mode image processing.
- Model registry disabled/fallback behavior.
- Path confinement against unauthorized paths.
- Live smoke test against local Gemma 4 E4B marked @pytest.mark.live_model.
"""

import io
from pathlib import Path
import pytest
from PIL import Image
from pydantic import ValidationError

from backend.core.config import get_settings
from backend.core.paths import AccessDenied, PathTraversalError
from models.ollama_client import OllamaClient
from tools.registry import ToolContext
from tools.vision import (
    VisionAnalyzeArgs,
    VisionBatchAnalyzeArgs,
    VisualObservation,
    prepare_image,
    set_vision_hook,
    vision_analyze,
    vision_analyze_batch,
)


@pytest.fixture
def test_image(tmp_path, monkeypatch):
    """Create a temporary test image within allowed incoming directory."""
    incoming_dir = tmp_path / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(get_settings(), "ALLOWED_INPUT_DIRS", str(incoming_dir))

    img_path = incoming_dir / "sample_weld.png"
    img = Image.new("RGB", (640, 480), color=(180, 190, 200))
    img.save(str(img_path), format="PNG")
    return img_path


@pytest.fixture
def engineer_ctx():
    return ToolContext(
        user_id="user_eng_vision",
        role="engineer",
        clearance=2,
        run_id="run_vis_001",
    )


def test_visual_observation_schema_validation():
    """VisualObservation enforces mandatory limitation, type literals, and rejects measurement claims."""
    # 1. Valid observation
    valid_obs = VisualObservation(
        component="Pipe Elbow",
        visible_condition="Minor discoloration and surface pitting",
        source="page_1_image_1.png",
        limitation="Visual observation only; not a dimensional wall thickness measurement",
        type="observed",
        confidence="high",
    )
    assert valid_obs.component == "Pipe Elbow"
    assert valid_obs.type == "observed"

    # 2. Missing limitation rejected
    with pytest.raises(ValidationError):
        VisualObservation(
            component="Pipe Elbow",
            visible_condition="Discoloration",
            source="page_1_image_1.png",
            limitation="",  # Empty string rejected
            type="observed",
        )

    # 3. Invalid type rejected
    with pytest.raises(ValidationError):
        VisualObservation(
            component="Pipe Elbow",
            visible_condition="Discoloration",
            source="page_1_image_1.png",
            limitation="Visual note",
            type="measured",  # Only 'observed' or 'inferred' allowed
        )

    # 4. Authoritative measurement claims rejected
    with pytest.raises(ValidationError, match="Engineering safety boundary violation"):
        VisualObservation(
            component="Pipe Elbow",
            visible_condition="Certified measurement confirms 1.2 mm thinning",
            source="page_1_image_1.png",
            limitation="Visual note",
            type="observed",
        )


def test_prepare_image_downscaling():
    """Images exceeding max_edge are downscaled proportionally preserving aspect ratio."""
    # Create large image: 2400 x 1200 (aspect 2:1)
    large_img = Image.new("RGB", (2400, 1200), color="blue")
    buf = io.BytesIO()
    large_img.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()

    jpeg_bytes, b64_str = prepare_image(raw_bytes, max_edge=1200)

    # Inspect downscaled dimensions
    processed = Image.open(io.BytesIO(jpeg_bytes))
    assert processed.size[0] == 1200
    assert processed.size[1] == 600
    assert len(b64_str) > 0


def test_vision_analyze_with_mock_client(test_image, engineer_ctx):
    """Vision analysis parses model response into valid VisualObservation list."""
    canned_json = """
    [
      {
        "component": "Circumferential Weld Seam CW-3",
        "visible_condition": "Surface irregularity and pitting marks visible in heat-affected zone",
        "source": "sample_weld.png",
        "limitation": "Non-authoritative visual observation; not a dimensional measurement",
        "type": "observed",
        "confidence": "high"
      }
    ]
    """

    def mock_hook(model, prompt, system, image_b64):
        assert "sample_weld.png" in prompt
        assert "VisualObservation" in prompt
        return canned_json

    set_vision_hook(mock_hook)
    try:
        args = VisionAnalyzeArgs(image_ref=str(test_image))
        result = vision_analyze(args, engineer_ctx)

        assert result.evidence_available is True
        assert len(result.observations) == 1
        obs = result.observations[0]
        assert obs.component == "Circumferential Weld Seam CW-3"
        assert obs.type == "observed"
        assert "not a dimensional measurement" in obs.limitation
        assert result.error is None
    finally:
        set_vision_hook(None)


def test_vision_analyze_one_shot_repair(test_image, engineer_ctx):
    """When model produces invalid JSON on first pass, repair retry successfully fixes it."""
    attempt = 0

    def mock_repair_hook(model, prompt, system, image_b64):
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            # First pass: malformed JSON (missing closing bracket)
            return "Here are my observations: [ {'component': 'Weld Seam', 'visible_condition': 'Pit'}"
        else:
            # Repair pass: valid JSON array
            return """
            [
              {
                "component": "Weld Seam",
                "visible_condition": "Surface pitting cluster",
                "source": "sample_weld.png",
                "limitation": "Visual inspection only",
                "type": "observed",
                "confidence": "medium"
              }
            ]
            """

    set_vision_hook(mock_repair_hook)
    try:
        args = VisionAnalyzeArgs(image_ref=str(test_image))
        result = vision_analyze(args, engineer_ctx)

        assert attempt == 2
        assert result.evidence_available is True
        assert len(result.observations) == 1
        assert result.observations[0].component == "Weld Seam"
    finally:
        set_vision_hook(None)


def test_vision_analyze_safe_failure_handling(test_image, engineer_ctx):
    """When model fails even after repair, safely reports evidence_available=False without crashing."""
    def mock_broken_hook(model, prompt, system, image_b64):
        return "I am an AI and cannot analyze this image properly."

    set_vision_hook(mock_broken_hook)
    try:
        args = VisionAnalyzeArgs(image_ref=str(test_image))
        result = vision_analyze(args, engineer_ctx)

        assert result.evidence_available is False
        assert len(result.observations) == 0
        assert result.error is not None
        assert "No JSON array found" in result.error or "Repair" in result.error
    finally:
        set_vision_hook(None)


def test_vision_batch_mode(tmp_path, monkeypatch, engineer_ctx):
    """Batch mode processes multiple images in sequence within one tool session."""
    incoming_dir = tmp_path / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(get_settings(), "ALLOWED_INPUT_DIRS", str(incoming_dir))

    img1 = incoming_dir / "img1.png"
    img2 = incoming_dir / "img2.png"
    Image.new("RGB", (200, 200), color="red").save(str(img1))
    Image.new("RGB", (200, 200), color="green").save(str(img2))

    call_count = 0

    def mock_batch_hook(model, prompt, system, image_b64):
        nonlocal call_count
        call_count += 1
        return f"""
        [
          {{
            "component": "Feature {call_count}",
            "visible_condition": "Normal",
            "source": "img.png",
            "limitation": "Visual only",
            "type": "observed",
            "confidence": "high"
          }}
        ]
        """

    set_vision_hook(mock_batch_hook)
    try:
        batch_args = VisionBatchAnalyzeArgs(
            images=[
                VisionAnalyzeArgs(image_ref=str(img1)),
                VisionAnalyzeArgs(image_ref=str(img2)),
            ]
        )
        batch_result = vision_analyze_batch(batch_args, engineer_ctx)

        assert batch_result.total_images == 2
        assert len(batch_result.results) == 2
        assert batch_result.results[0].evidence_available is True
        assert batch_result.results[1].evidence_available is True
        assert call_count == 2
    finally:
        set_vision_hook(None)


def test_vision_disabled_model_fallback(test_image, engineer_ctx, monkeypatch):
    """When vision model is disabled and no fallback exists, returns evidence_available=False."""
    # Point registry to a dummy or override
    from models.registry import ModelRegistry, ModelEntry

    empty_registry = ModelRegistry(
        models={
            "vision": ModelEntry(provider="ollama", model="gemma4:e4b", enabled=False),
            "vision_fallback": ModelEntry(provider="ollama", model="qwen3.5:4b", enabled=False),
        }
    )
    monkeypatch.setattr("tools.vision.get_registry", lambda path: empty_registry)

    args = VisionAnalyzeArgs(image_ref=str(test_image))
    result = vision_analyze(args, engineer_ctx)

    assert result.evidence_available is False
    assert "disabled" in result.error.lower()


def test_vision_path_confinement(engineer_ctx):
    """Paths outside allowed directories raise AccessDenied / PathTraversalError."""
    args = VisionAnalyzeArgs(image_ref="../../secret_photo.png")
    with pytest.raises((AccessDenied, PathTraversalError)):
        vision_analyze(args, engineer_ctx)


@pytest.mark.live_model
def test_vision_live_smoke(engineer_ctx):
    """Live smoke test executing Gemma 4 E4B on demo_inspection_photo.png (run if Ollama active)."""
    photo_path = Path("data/incoming/demo_inspection_photo.png")
    if not photo_path.exists():
        pytest.skip("demo_inspection_photo.png does not exist")

    client = OllamaClient()
    if not client.is_healthy():
        pytest.skip("Local Ollama is not active")

    if not client.is_model_available("gemma4:e4b"):
        pytest.skip("gemma4:e4b is not downloaded in Ollama")

    args = VisionAnalyzeArgs(
        image_ref=str(photo_path),
        question="Describe visible weld features and corrosion indications",
    )
    result = vision_analyze(args, engineer_ctx)

    assert result.evidence_available is True
    assert len(result.observations) >= 1
    obs = result.observations[0]
    assert obs.limitation != ""
    assert obs.type in {"observed", "inferred"}
    assert obs.confidence in {"low", "medium", "high"}
