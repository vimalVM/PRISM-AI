"""Tests for application configuration and loopback security validation."""

import pytest
from pydantic import ValidationError
from backend.core.config import Settings, get_settings


def test_default_settings_loopback():
    """Verify default settings are strictly bound to localhost."""
    settings = Settings()
    assert settings.APP_HOST in {"127.0.0.1", "localhost"}
    assert settings.APP_PORT == 8000
    assert "127.0.0.1" in settings.OLLAMA_BASE_URL
    assert settings.ALLOW_LAN is False


def test_reject_external_app_host_without_lan():
    """Verify non-loopback host is rejected when ALLOW_LAN is False."""
    with pytest.raises(ValidationError) as exc:
        Settings(APP_HOST="192.168.1.100", ALLOW_LAN=False)
    assert "air-gap protection" in str(exc.value)


def test_allow_external_app_host_when_explicitly_configured():
    """Verify non-loopback host is accepted only when ALLOW_LAN is True."""
    settings = Settings(APP_HOST="192.168.1.100", ALLOW_LAN=True)
    assert settings.APP_HOST == "192.168.1.100"


def test_reject_non_loopback_ollama_url():
    """Verify remote Ollama URLs are rejected unconditionally."""
    with pytest.raises(ValidationError) as exc:
        Settings(OLLAMA_BASE_URL="http://external-server.com:11434")
    assert "non-loopback host" in str(exc.value)


def test_get_settings_caching():
    """Verify get_settings returns singleton."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
