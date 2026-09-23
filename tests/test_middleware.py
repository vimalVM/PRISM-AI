"""Tests for security middleware: CORS enforcement, CSP, CSRF, and rate limiting (SEC-17)."""

import pytest
from fastapi.testclient import TestClient

from backend.core.middleware import _login_rate_limiter
from backend.main import create_app


@pytest.fixture
def client():
    """Create test client with fresh app instance."""
    app = create_app()
    _login_rate_limiter.records.clear()
    return TestClient(app)


def test_cors_allowed_origins_sec17(client):
    """SEC-17: Valid local origins receive Access-Control-Allow-Origin header."""
    for origin in ["http://127.0.0.1:8000", "http://127.0.0.1:5173", "http://localhost:8000", "http://localhost:5173"]:
        res = client.get(
            "/api/health",
            headers={"Origin": origin},
        )
        assert res.status_code == 200
        assert res.headers.get("access-control-allow-origin") == origin


def test_cors_rejected_external_origin_sec17(client):
    """SEC-17: Untrusted external origin is blocked from CORS allowance."""
    untrusted_origins = [
        "http://evil.local",
        "https://attacker.com",
        "http://192.168.1.100:8000",
    ]
    for origin in untrusted_origins:
        res = client.get(
            "/api/health",
            headers={"Origin": origin},
        )
        assert res.status_code == 200
        # Untrusted origin must NOT receive access-control-allow-origin
        assert res.headers.get("access-control-allow-origin") is None


def test_csp_header_present(client):
    """Content-Security-Policy header is present on responses with default-src 'self'."""
    res = client.get("/api/health")
    assert res.status_code == 200
    csp = res.headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_security_headers_present(client):
    """X-Content-Type-Options, Referrer-Policy, and X-Frame-Options are present."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("referrer-policy") == "no-referrer"
    assert res.headers.get("x-frame-options") == "DENY"
    # Cache-control for API endpoints
    cache_ctrl = res.headers.get("cache-control", "")
    assert "no-store" in cache_ctrl


def test_csrf_middleware_blocks_missing_header(client):
    """State-changing POST request to /api/ without CSRF custom header is rejected."""
    res = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "AnyPassword123!"},
        # Deliberately omitting X-Requested-With header
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "CSRF_DETECTED"


def test_csrf_middleware_permits_custom_header(client):
    """State-changing POST request with X-Requested-With header passes CSRF check."""
    res = client.post(
        "/api/auth/login",
        json={"username": "nonexistent", "password": "AnyPassword123!"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    # Passed CSRF check and reached auth logic (401 invalid credentials)
    assert res.status_code in (401, 200)


def test_rate_limiting_login_endpoint(client):
    """Exceeding rate limit on login endpoint returns 429 Too Many Requests."""
    # Our login limit is 20 requests per minute
    hit_rate_limit = False
    for _ in range(25):
        res = client.post(
            "/api/auth/login",
            json={"username": "test", "password": "WrongPassword!"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        if res.status_code == 429:
            hit_rate_limit = True
            assert res.json()["error"]["code"] == "RATE_LIMITED"
            break

    assert hit_rate_limit is True
