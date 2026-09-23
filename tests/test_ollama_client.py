"""Tests for local Ollama client security and parameter handling."""

import pytest
from models.ollama_client import OllamaClient, OllamaSecurityError


def test_ollama_client_loopback_enforcement():
    """Verify client rejects non-loopback base URLs."""
    with pytest.raises(OllamaSecurityError) as exc:
        OllamaClient(base_url="http://10.0.0.5:11434")
    assert "non-loopback" in str(exc.value)

    # Valid loopback URLs
    client_ip = OllamaClient(base_url="http://127.0.0.1:11434")
    assert client_ip.base_url == "http://127.0.0.1:11434"

    client_loc = OllamaClient(base_url="http://localhost:11434")
    assert client_loc.base_url == "http://localhost:11434"


def test_ollama_client_reject_cloud_models():
    """Verify client rejects any invocation of :cloud tags."""
    client = OllamaClient()
    with pytest.raises(OllamaSecurityError) as exc:
        client.generate(model="qwen3.5:4b:cloud", prompt="hello")
    assert "contains ':cloud' marker" in str(exc.value)

    with pytest.raises(OllamaSecurityError) as exc:
        client.chat(model="gemma4:e4b:cloud", messages=[{"role": "user", "content": "hi"}])
    assert "contains ':cloud' marker" in str(exc.value)


def test_ollama_client_health_and_list():
    """Verify local Ollama service can be queried and reports installed models."""
    client = OllamaClient()
    is_healthy = client.is_healthy()
    assert is_healthy is True

    models = client.list_models()
    assert len(models) >= 2
    model_names = [m["name"] for m in models]
    assert any("qwen3.5:4b" in n for n in model_names)
    assert any("gemma4:e4b" in n for n in model_names)


def test_ollama_client_is_model_available():
    """Verify is_model_available check."""
    client = OllamaClient()
    assert client.is_model_available("qwen3.5:4b") is True
    assert client.is_model_available("gemma4:e4b") is True
    assert client.is_model_available("nonexistent_model_tag") is False
