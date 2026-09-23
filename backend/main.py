"""FastAPI backend application factory for Sovereign AI Workbench.

Bound exclusively to localhost (127.0.0.1) with strictly local inference routes,
security headers, strict CORS, CSRF protection, and role-based access control.
"""

from contextlib import asynccontextmanager
import logging
from typing import Any, Dict
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.api import auth, audit_api, files, kb, tasks, users
from backend.core.audit import log_event
from backend.core.config import get_settings
from backend.core.db import User, init_db
from backend.core.middleware import (
    CSRFProtectionMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from backend.core.rbac import Role, require_role
from backend.core.selfcheck import run_startup_self_checks
from models.ollama_client import OllamaClient
from models.registry import get_registry, reload_registry


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sovereign-workbench")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager running DB initialization and startup pre-flight checks."""
    logger.info("Initializing Sovereign AI Workbench database and backend...")
    init_db()

    all_passed, checks = run_startup_self_checks()
    for c in checks:
        lvl = logging.INFO if c["status"] == "pass" else logging.WARNING
        logger.log(lvl, f"Self-check [{c['check']}]: {c['status']} — {c['detail']}")

    if not all_passed:
        logger.warning("One or more non-critical startup self-checks failed. Review Sovereignty / Models panel.")
    yield
    logger.info("Shutting down Sovereign AI Workbench backend.")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Sovereign AI Workbench",
        description="Air-gapped, self-hosted agentic AI workbench.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware order in Starlette/FastAPI:
    # Outer-most executes first on request, last on response.
    # We want: Security Headers -> CORS -> CSRF -> RateLimiter -> App Routers
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CSRFProtectionMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Include API Routers
    app.include_router(auth.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(audit_api.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(kb.router, prefix="/api")
    app.include_router(files.router, prefix="/api")

    @app.get("/api/health")
    async def health_check() -> Dict[str, Any]:
        """Liveness check for Sovereign AI Workbench."""
        return {
            "status": "ok",
            "app": "Sovereign AI Workbench",
            "offline": True,
            "host": settings.APP_HOST,
            "port": settings.APP_PORT,
        }

    @app.get("/api/models")
    async def list_models() -> Dict[str, Any]:
        """List configured registry models and active local Ollama service status."""
        registry = get_registry(settings.MODEL_REGISTRY_PATH)
        client = OllamaClient()

        ollama_healthy = client.is_healthy()
        local_models = client.list_models() if ollama_healthy else []

        models_status = {}
        for key, entry in registry.models.items():
            is_present = any(entry.model in m["name"] for m in local_models) if entry.enabled else False
            models_status[key] = {
                "model": entry.model,
                "provider": entry.provider,
                "enabled": entry.enabled,
                "capabilities": entry.capabilities,
                "present_locally": is_present,
            }

        from agent.router import get_model_swap_manager
        swap_mgr = get_model_swap_manager()

        return {
            "ollama_connected": ollama_healthy,
            "ollama_base_url": settings.OLLAMA_BASE_URL,
            "current_loaded_model": swap_mgr.get_current_model(),
            "swap_status": swap_mgr.get_status(),
            "models": models_status,
            "embeddings": registry.embeddings.model_dump(),
            "ocr": registry.ocr.model_dump(),
            "routing_rules": [r.name for r in registry.routing.rules],
        }

    @app.post("/api/models/reload")
    async def reload_model_registry(
        admin: User = Depends(require_role(Role.ADMIN)),
    ) -> Dict[str, Any]:
        """Reload models/registry.yaml from disk. Requires admin role."""
        try:
            registry = reload_registry(settings.MODEL_REGISTRY_PATH)
            log_event(
                event_type="registry_reloaded",
                status="ok",
                user_id=admin.id,
                role=admin.role,
                details={"model_count": len(registry.models)},
            )
            return {"status": "ok", "message": "Registry reloaded", "model_count": len(registry.models)}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to reload registry: {e}")

    return app


app = create_app()
