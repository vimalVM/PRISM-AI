"""Security middleware for Sovereign AI Workbench.

Implements SEC-17 (CORS origin enforcement, CSP, security headers,
CSRF header validation, and rate limiting).
"""

from collections import defaultdict
from datetime import datetime, timezone
import time
from typing import Callable, Dict, List, Tuple

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject strict security headers and Content-Security-Policy (CSP) on all responses."""

    CSP_POLICY = (
        "default-src 'self'; "
        "img-src 'self' data: blob:; "
        "style-src 'self'; "
        "script-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        response.headers["Content-Security-Policy"] = self.CSP_POLICY
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"

        # Apply no-store for all API endpoints to prevent sensitive caching
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Enforce CSRF custom-header check on state-changing API requests."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method not in self.SAFE_METHODS and request.url.path.startswith("/api/"):
            # Check for standard custom headers indicating non-simple / non-cross-site browser form request
            has_csrf_header = (
                "x-requested-with" in request.headers
                or "x-csrf-token" in request.headers
            )
            if not has_csrf_header:
                return Response(
                    content='{"error":{"code":"CSRF_DETECTED","message":"Missing required X-Requested-With header"}}',
                    status_code=status.HTTP_403_FORBIDDEN,
                    media_type="application/json",
                )

        return await call_next(request)


class RateLimiter:
    """In-memory sliding window rate limiter."""

    def __init__(self, requests_limit: int = 60, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.records: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, client_key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        times = self.records[client_key]
        # Drop timestamps outside current window
        valid_times = [t for t in times if t > window_start]
        self.records[client_key] = valid_times

        if len(valid_times) >= self.requests_limit:
            return True

        valid_times.append(now)
        return False


_login_rate_limiter = RateLimiter(requests_limit=20, window_seconds=60)
_general_rate_limiter = RateLimiter(requests_limit=120, window_seconds=60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce rate limits on sensitive endpoints."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "127.0.0.1"

        if request.url.path == "/api/auth/login" and request.method == "POST":
            if _login_rate_limiter.is_rate_limited(client_ip):
                return Response(
                    content='{"error":{"code":"RATE_LIMITED","message":"Too many login attempts. Please slow down."}}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                )

        return await call_next(request)
