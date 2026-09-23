"""Tests for FastAPI core endpoints: /api/health and /api/models."""

from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_api_health():
    """Verify health endpoint returns status ok and offline flag."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Sovereign AI Workbench"
    assert data["offline"] is True


def test_api_models():
    """Verify models endpoint returns registry models and local presence."""
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert data["ollama_connected"] is True
    assert "models" in data

    models = data["models"]
    assert "default" in models
    assert models["default"]["model"] == "qwen3.5:4b"
    assert models["default"]["present_locally"] is True

    assert "vision" in models
    assert models["vision"]["model"] == "gemma4:e4b"
    assert models["vision"]["present_locally"] is True

    assert "routing_rules" in data
    assert "scanned_document" in data["routing_rules"]
    assert "text_default" in data["routing_rules"]


def test_api_models_reload():
    """Verify reload endpoint successfully reloads registry for admin users."""
    from backend.core.db import User
    from backend.core.security import get_current_user

    mock_admin = User(
        id="admin-test-id",
        username="admin",
        role="admin",
        clearance=3,
        active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: mock_admin

    try:
        response = client.post(
            "/api/models/reload",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["model_count"] >= 2
    finally:
        app.dependency_overrides.pop(get_current_user, None)
