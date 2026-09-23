"""Unit and integration tests for sovereignty, air-gap status, and connection audit endpoints.

Implements Phase 12 of docs/04_ANTIGRAVITY_BUILD_PLAN.md:
- /api/system/status: live bindings, models, offline flags
- /api/system/connections: passive psutil socket audit (0 non-loopback sockets)
- /api/system/probe: active outbound egress probe (requires confirm=true, admin/auditor only)
- Startup enforcement: rejects non-loopback hosts and :cloud models
"""

import os
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.core.db import User, get_session_factory
from backend.core.security import SESSION_COOKIE_NAME, create_session, hash_password
from backend.main import create_app, enforce_startup_sovereignty


@pytest.fixture(scope="module")
def sovereignty_test_env():
    """Create test users (admin, engineer, auditor) and session tokens for system endpoint testing."""
    factory = get_session_factory()
    import uuid
    uid = uuid.uuid4().hex[:8]

    with factory() as db:
        admin_user = User(
            id=f"admin_sov_{uid}",
            username=f"admin_sov_{uid}",
            password_hash=hash_password("AdminPass123!"),
            role="admin",
            clearance=3,
            active=True,
        )
        engineer_user = User(
            id=f"eng_sov_{uid}",
            username=f"eng_sov_{uid}",
            password_hash=hash_password("EngPass123!"),
            role="engineer",
            clearance=2,
            active=True,
        )
        auditor_user = User(
            id=f"aud_sov_{uid}",
            username=f"aud_sov_{uid}",
            password_hash=hash_password("AudPass123!"),
            role="auditor",
            clearance=3,
            active=True,
        )
        db.add_all([admin_user, engineer_user, auditor_user])
        db.commit()

        _, admin_token = create_session(db, admin_user.id)
        _, eng_token = create_session(db, engineer_user.id)
        _, aud_token = create_session(db, auditor_user.id)

        tokens = {
            "admin": admin_token,
            "engineer": eng_token,
            "auditor": aud_token,
        }

    app = create_app()
    client = TestClient(app)

    return {
        "client": client,
        "tokens": tokens,
    }


def test_system_status_endpoint(sovereignty_test_env):
    """Verify /api/system/status returns loopback bindings, models, and offline flags."""
    client = sovereignty_test_env["client"]
    token = sovereignty_test_env["tokens"]["engineer"]

    res = client.get(
        "/api/system/status",
        headers={"X-Requested-With": "XMLHttpRequest"},
        cookies={SESSION_COOKIE_NAME: token},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["app_host"] in {"127.0.0.1", "localhost", "::1"}
    assert data["app_port"] == 8000
    assert "127.0.0.1:11434" in data["ollama_base_url"]
    assert len(data["models"]) >= 2
    assert data["sovereign_enforced"] is True
    assert data["offline_flags"]["HF_HUB_OFFLINE"] == "1"
    assert data["offline_flags"]["TRANSFORMERS_OFFLINE"] == "1"


def test_system_connections_passive_audit(sovereignty_test_env):
    """Verify /api/system/connections performs passive audit and reports socket isolation status."""
    client = sovereignty_test_env["client"]
    token = sovereignty_test_env["tokens"]["auditor"]

    res = client.get(
        "/api/system/connections",
        headers={"X-Requested-With": "XMLHttpRequest"},
        cookies={SESSION_COOKIE_NAME: token},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] in {"CLEAN", "VIOLATION"}
    assert "non_loopback_count" in data
    assert "timestamp" in data
    assert isinstance(data["checked_processes"], list)

    # Test clean mocked scenario (all connections on 127.0.0.1)
    from collections import namedtuple
    Addr = namedtuple("Addr", ["ip", "port"])
    MockConn = namedtuple("MockConn", ["fd", "family", "type", "laddr", "raddr", "status"])

    clean_conn = MockConn(
        fd=10,
        family=2,
        type=1,
        laddr=Addr(ip="127.0.0.1", port=8000),
        raddr=Addr(ip="127.0.0.1", port=54321),
        status="ESTABLISHED",
    )

    with patch("psutil.Process.net_connections", return_value=[clean_conn]):
        res_clean = client.get(
            "/api/system/connections",
            headers={"X-Requested-With": "XMLHttpRequest"},
            cookies={SESSION_COOKIE_NAME: token},
        )
        assert res_clean.status_code == 200
        clean_data = res_clean.json()
        assert clean_data["status"] == "CLEAN"
        assert clean_data["non_loopback_count"] == 0

    # Test violation scenario (connection to external public IP)
    bad_conn = MockConn(
        fd=11,
        family=2,
        type=1,
        laddr=Addr(ip="10.0.0.5", port=44444),
        raddr=Addr(ip="93.184.216.34", port=443),
        status="ESTABLISHED",
    )
    with patch("psutil.Process.net_connections", return_value=[bad_conn]):
        res_bad = client.get(
            "/api/system/connections",
            headers={"X-Requested-With": "XMLHttpRequest"},
            cookies={SESSION_COOKIE_NAME: token},
        )
        assert res_bad.status_code == 200
        bad_data = res_bad.json()
        assert bad_data["status"] == "VIOLATION"
        assert bad_data["non_loopback_count"] >= 1
        assert len(bad_data["non_loopback_connections"]) >= 1


def test_active_egress_probe_authorization_and_confirmation(sovereignty_test_env):
    """Verify /api/system/probe requires confirm=true and forbids engineer role."""
    client = sovereignty_test_env["client"]
    eng_token = sovereignty_test_env["tokens"]["engineer"]
    admin_token = sovereignty_test_env["tokens"]["admin"]

    # 1. Calling as engineer -> forbidden
    res_eng = client.post(
        "/api/system/probe?confirm=true",
        headers={"X-Requested-With": "XMLHttpRequest"},
        cookies={SESSION_COOKIE_NAME: eng_token},
    )
    assert res_eng.status_code == 403

    # 2. Calling as admin without confirmation -> 400
    res_no_confirm = client.post(
        "/api/system/probe?confirm=false",
        headers={"X-Requested-With": "XMLHttpRequest"},
        cookies={SESSION_COOKIE_NAME: admin_token},
    )
    assert res_no_confirm.status_code == 400

    # 3. Calling as admin with confirm=true -> executes probe
    res_confirm = client.post(
        "/api/system/probe?confirm=true",
        headers={"X-Requested-With": "XMLHttpRequest"},
        cookies={SESSION_COOKIE_NAME: admin_token},
    )
    assert res_confirm.status_code == 200
    data = res_confirm.json()
    assert data["probe_status"] in {"BLOCKED", "CONNECTED"}
    assert "target" in data
    assert "message" in data


def test_startup_enforcement_valid():
    """Verify startup enforcement passes with default loopback settings."""
    enforce_startup_sovereignty()
    assert os.environ.get("HF_HUB_OFFLINE") == "1"
    assert os.environ.get("TRANSFORMERS_OFFLINE") == "1"
    assert os.environ.get("ANONYMIZED_TELEMETRY") == "False"
    assert os.environ.get("DO_NOT_TRACK") == "1"


def test_startup_enforcement_rejects_non_loopback_host():
    """Verify startup enforcement raises RuntimeError if APP_HOST is non-loopback without ALLOW_LAN."""
    mock_settings = MagicMock()
    mock_settings.APP_HOST = "192.168.1.50"
    mock_settings.ALLOW_LAN = False
    mock_settings.OLLAMA_BASE_URL = "http://127.0.0.1:11434"

    with patch("backend.main.get_settings", return_value=mock_settings):
        with pytest.raises(RuntimeError, match="SOVEREIGNTY VIOLATION: APP_HOST"):
            enforce_startup_sovereignty()


def test_startup_enforcement_rejects_external_ollama():
    """Verify startup enforcement raises RuntimeError if OLLAMA_BASE_URL is external."""
    mock_settings = MagicMock()
    mock_settings.APP_HOST = "127.0.0.1"
    mock_settings.ALLOW_LAN = False
    mock_settings.OLLAMA_BASE_URL = "https://api.openai.com/v1"

    with patch("backend.main.get_settings", return_value=mock_settings):
        with pytest.raises(RuntimeError, match="SOVEREIGNTY VIOLATION: OLLAMA_BASE_URL"):
            enforce_startup_sovereignty()


def test_startup_enforcement_rejects_cloud_models():
    """Verify startup enforcement raises RuntimeError if a model has :cloud tag."""
    mock_settings = MagicMock()
    mock_settings.APP_HOST = "127.0.0.1"
    mock_settings.ALLOW_LAN = False
    mock_settings.OLLAMA_BASE_URL = "http://127.0.0.1:11434"
    mock_settings.MODEL_REGISTRY_PATH = "models/registry.yaml"

    mock_model = MagicMock()
    mock_model.model = "qwen3.5:cloud"
    mock_model.provider = "ollama"

    mock_registry = MagicMock()
    mock_registry.models = {"cloud_model": mock_model}

    with patch("backend.main.get_settings", return_value=mock_settings):
        with patch("backend.main.get_registry", return_value=mock_registry):
            with pytest.raises(RuntimeError, match="contains ':cloud' tag"):
                enforce_startup_sovereignty()
