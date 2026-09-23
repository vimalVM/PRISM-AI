"""API tests for task lifecycle management and SSE streaming endpoints.

Tests /api/tasks CRUD, RBAC, background execution, cancellation, and SSE events.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from agent.nodes.plan import set_llm_client_override
from backend.core.config import get_settings
from backend.core.db import User, get_session_factory
from backend.core.security import SESSION_COOKIE_NAME, create_session, hash_password
from backend.main import create_app


class MockOllamaClientForAPI:
    def generate(self, model: str, prompt: str, system: str = None, **kwargs):
        if "Generate a concise, step-by-step execution plan" in prompt:
            return {"response": '{"steps": []}'}
        return {"response": "Task completed with empty plan."}


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """Create test client with authenticated session cookies."""
    app = create_app()
    client = TestClient(app)

    import uuid
    suffix = uuid.uuid4().hex[:8]

    factory = get_session_factory()
    with factory() as db:
        # Create engineer user
        eng_user = User(
            username=f"eng_task_{suffix}",
            password_hash=hash_password("EngineerPass123!"),
            role="engineer",
            clearance=1,
            active=True,
        )
        db.add(eng_user)

        # Create auditor user
        auditor_user = User(
            username=f"auditor_task_{suffix}",
            password_hash=hash_password("AuditorPass123!"),
            role="auditor",
            clearance=1,
            active=True,
        )
        db.add(auditor_user)
        db.commit()

        # Create active sessions
        _, eng_cookie = create_session(db, eng_user.id)
        _, auditor_cookie = create_session(db, auditor_user.id)

    return client, eng_cookie, auditor_cookie


@pytest.fixture(autouse=True)
def mock_llm():
    set_llm_client_override(MockOllamaClientForAPI())
    yield
    set_llm_client_override(None)


def test_create_and_get_task(api_client):
    client, eng_cookie, _ = api_client

    headers = {"X-Requested-With": "XMLHttpRequest"}
    cookies = {SESSION_COOKIE_NAME: eng_cookie}

    # 1. Create Task
    resp = client.post(
        "/api/tasks",
        json={"request_text": "Analyze the pressure system data."},
        headers=headers,
        cookies=cookies,
    )
    assert resp.status_code == 201
    data = resp.json()
    task_id = data["id"]
    assert data["request_text"] == "Analyze the pressure system data."
    assert data["status"] in {"pending", "running", "completed"}

    # 2. Get Task by ID
    get_resp = client.get(f"/api/tasks/{task_id}", headers=headers, cookies=cookies)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == task_id

    # 3. List Tasks
    list_resp = client.get("/api/tasks", headers=headers, cookies=cookies)
    assert list_resp.status_code == 200
    tasks = list_resp.json()
    assert any(t["id"] == task_id for t in tasks)


def test_cancel_task(api_client):
    client, eng_cookie, _ = api_client
    headers = {"X-Requested-With": "XMLHttpRequest"}
    cookies = {SESSION_COOKIE_NAME: eng_cookie}

    # Create task
    resp = client.post(
        "/api/tasks",
        json={"request_text": "Task to be cancelled"},
        headers=headers,
        cookies=cookies,
    )
    task_id = resp.json()["id"]

    # Cancel task
    cancel_resp = client.post(
        f"/api/tasks/{task_id}/cancel",
        headers=headers,
        cookies=cookies,
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] in {"cancelled", "completed"}


def test_stream_task_events_sse(api_client):
    client, eng_cookie, _ = api_client
    headers = {"X-Requested-With": "XMLHttpRequest"}
    cookies = {SESSION_COOKIE_NAME: eng_cookie}

    # Create task
    resp = client.post(
        "/api/tasks",
        json={"request_text": "Stream test task"},
        headers=headers,
        cookies=cookies,
    )
    task_id = resp.json()["id"]

    # Connect to SSE endpoint (read stream with timeout or chunk limit)
    with client.stream("GET", f"/api/tasks/{task_id}/events", headers=headers, cookies=cookies) as stream:
        assert stream.status_code == 200
        assert "text/event-stream" in stream.headers.get("content-type", "")

        events_received = 0
        for line in stream.iter_lines():
            if line:
                events_received += 1
                if events_received >= 2:
                    break
        assert events_received > 0
