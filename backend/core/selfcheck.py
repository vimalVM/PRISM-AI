"""Startup self-checks for Sovereign AI Workbench.

Verifies air-gap integrity, model availability, local network binding,
and local weights before accepting traffic.
"""

from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from backend.core.config import get_settings
from models.ollama_client import OllamaClient
from models.registry import get_registry


LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def run_startup_self_checks() -> Tuple[bool, List[Dict[str, str]]]:
    """Execute all pre-flight self checks on startup.

    Returns (all_passed, results_list).
    """
    settings = get_settings()
    results = []

    # 1. Bind Address Check
    if settings.APP_HOST in LOOPBACK_HOSTS or settings.ALLOW_LAN:
        results.append({"check": "bind_address", "status": "pass", "detail": f"APP_HOST={settings.APP_HOST}"})
    else:
        results.append({"check": "bind_address", "status": "fail", "detail": f"Forbidden non-loopback host {settings.APP_HOST}"})

    # 2. Ollama Loopback Check
    parsed_ollama = urlparse(settings.OLLAMA_BASE_URL)
    if (parsed_ollama.hostname or "") in LOOPBACK_HOSTS:
        results.append({"check": "ollama_loopback", "status": "pass", "detail": f"Ollama on {settings.OLLAMA_BASE_URL}"})
    else:
        results.append({"check": "ollama_loopback", "status": "fail", "detail": f"Non-loopback Ollama URL {settings.OLLAMA_BASE_URL}"})

    # 3. Model Registry Check
    try:
        registry = get_registry(settings.MODEL_REGISTRY_PATH)
        cloud_models = [m.model for m in registry.models.values() if ":cloud" in m.model.lower()]
        if cloud_models:
            results.append({"check": "model_registry", "status": "fail", "detail": f"Found :cloud model tags: {cloud_models}"})
        else:
            results.append({"check": "model_registry", "status": "pass", "detail": f"{len(registry.models)} models configured"})
    except Exception as e:
        results.append({"check": "model_registry", "status": "fail", "detail": str(e)})

    # 4. Ollama Connectivity & Required Models Check
    try:
        client = OllamaClient()
        if client.is_healthy():
            results.append({"check": "ollama_reachable", "status": "pass", "detail": "Connected to localhost:11434"})
            local_models = client.list_models()
            local_names = [m["name"] for m in local_models]

            # Check primary model
            qwen_present = any("qwen3.5:4b" in n for n in local_names)
            if qwen_present:
                results.append({"check": "qwen_model_local", "status": "pass", "detail": "qwen3.5:4b present locally"})
            else:
                results.append({"check": "qwen_model_local", "status": "fail", "detail": "qwen3.5:4b missing from Ollama"})

            # Check vision model
            gemma_present = any("gemma4:e4b" in n for n in local_names)
            if gemma_present:
                results.append({"check": "gemma_model_local", "status": "pass", "detail": "gemma4:e4b present locally"})
            else:
                results.append({"check": "gemma_model_local", "status": "fail", "detail": "gemma4:e4b missing from Ollama"})
        else:
            results.append({"check": "ollama_reachable", "status": "fail", "detail": "Local Ollama service unreachable"})
    except Exception as e:
        results.append({"check": "ollama_reachable", "status": "fail", "detail": f"Ollama error: {e}"})

    # 5. Embedding Directory Check
    emb_path = Path(settings.DATA_DIR) / "models" / "Qwen3-Embedding-0.6B"
    if emb_path.exists() and (emb_path / "model.safetensors").exists():
        results.append({"check": "embeddings_offline", "status": "pass", "detail": f"Weights present at {emb_path}"})
    else:
        results.append({"check": "embeddings_offline", "status": "fail", "detail": f"Missing weights at {emb_path}"})

    all_passed = all(r["status"] == "pass" for r in results)
    return all_passed, results
