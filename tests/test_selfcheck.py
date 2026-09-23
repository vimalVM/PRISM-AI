"""Tests for startup self-checks."""

from backend.core.selfcheck import run_startup_self_checks


def test_startup_self_checks():
    """Verify pre-flight startup self checks pass on local environment."""
    all_passed, checks = run_startup_self_checks()
    assert len(checks) >= 5
    # Loopback bind address, ollama connectivity, qwen & gemma presence, and offline embeddings should pass
    check_names = {c["check"]: c["status"] for c in checks}
    assert check_names.get("bind_address") == "pass"
    assert check_names.get("ollama_loopback") == "pass"
    assert check_names.get("model_registry") == "pass"
    assert check_names.get("ollama_reachable") == "pass"
    assert check_names.get("qwen_model_local") == "pass"
    assert check_names.get("gemma_model_local") == "pass"
    assert check_names.get("embeddings_offline") == "pass"
    assert all_passed is True
