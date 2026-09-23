"""Tests for model registry loading, validation, and capability routing."""

import pytest
from pydantic import ValidationError
from models.registry import (
    ModelEntry,
    get_registry,
    load_registry,
    reload_registry,
    resolve_route,
)


def test_registry_loading():
    """Verify registry loads models/registry.yaml cleanly."""
    registry = load_registry("models/registry.yaml")
    assert "default" in registry.models
    assert "vision" in registry.models
    assert registry.models["default"].model == "qwen3.5:4b"
    assert registry.models["vision"].model == "gemma4:e4b"
    assert registry.embeddings.provider == "sentence_transformers"
    assert registry.ocr.engine == "paddleocr"


def test_reject_cloud_model_tags():
    """Verify :cloud model tags and cloud providers raise validation errors."""
    with pytest.raises(ValidationError) as exc:
        ModelEntry(provider="ollama", model="qwen3.5:4b:cloud")
    assert "forbidden cloud marker" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ModelEntry(provider="openai", model="gpt-4")
    assert "not an authorized local inference runtime" in str(exc.value)


def test_routing_text_task():
    """Verify general text tasks route to default model (qwen3.5:4b)."""
    facts = {"task_type": "summary", "modality": {"text"}, "complexity": "low"}
    plan = resolve_route(facts)
    assert plan.rule_name == "text_default"
    assert plan.selected_model == "qwen3.5:4b"


def test_routing_scanned_document():
    """Verify scanned PDFs route to OCR + vision pipeline."""
    facts = {"modality": {"scanned_pdf"}}
    plan = resolve_route(facts)
    assert plan.rule_name == "scanned_document"
    assert "ocr" in plan.pipeline
    assert "vision" in plan.pipeline
    assert "gemma4:e4b" in plan.models
    assert "qwen3.5:4b" in plan.models


def test_routing_image():
    """Verify photographs and images route to vision model (gemma4:e4b)."""
    facts = {"modality": {"image"}}
    plan = resolve_route(facts)
    assert plan.rule_name == "image_or_photo"
    assert "gemma4:e4b" in plan.models


def test_routing_skip_disabled_models():
    """Verify disabled models are skipped and their configured fallback is used."""
    registry = get_registry()
    assert registry.models["future_strong_reasoning"].enabled is False

    facts = {"complexity": "high"}
    plan = resolve_route(facts, registry=registry)
    assert plan.rule_name == "complex_reasoning"
    assert plan.selected_model == "qwen3.5:4b"  # Falls back to default model
    assert "fallback to 'default'" in plan.reason


def test_registry_reload():
    """Verify registry can be reloaded without code change."""
    r = reload_registry("models/registry.yaml")
    assert r is not None
    assert len(r.models) >= 2
