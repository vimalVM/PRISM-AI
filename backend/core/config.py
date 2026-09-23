"""Application configuration for Sovereign AI Workbench.

Strictly enforces loopback binding, local endpoints, and offline security rules.
"""

from functools import lru_cache
from pathlib import Path
from typing import List
from urllib.parse import urlparse
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class Settings(BaseSettings):
    """Core application settings with sovereignty and air-gap safeguards."""

    # Server binding
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    ALLOW_LAN: bool = False

    # Ollama Local Service
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_HOST: str = "127.0.0.1:11434"

    # Paths
    MODEL_REGISTRY_PATH: str = "models/registry.yaml"
    DATA_DIR: str = "./data"
    DB_PATH: str = "data/db/workbench.db"
    LOG_DIR: str = "./logs"
    ALLOWED_INPUT_DIRS: str = "data/incoming,data/knowledge_base"
    ALLOWED_OUTPUT_DIRS: str = "data/outputs"
    SECRET_KEY_FILE: str = "data/secrets/session.key"

    # CORS
    CORS_ORIGINS: str = "http://127.0.0.1:8000,http://127.0.0.1:5173,http://localhost:8000,http://localhost:5173"

    # Limits and Timeouts
    MAX_UPLOAD_MB: int = 50
    MAX_PDF_PAGES: int = 200
    MAX_AGENT_RETRIES: int = 3
    MAX_TOOL_STEPS: int = 25
    MODEL_CALL_TIMEOUT_S: int = 180
    TOOL_TIMEOUT_S: int = 120
    SANDBOX_TIMEOUT_S: int = 30

    # Authentication & Session Security
    SESSION_TTL_MIN: int = 60
    LOGIN_MAX_FAILS: int = 5
    LOGIN_LOCK_MIN: int = 10

    # Sovereignty Controls
    ENABLE_ACTIVE_EGRESS_PROBE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_airgap_bindings(self) -> "Settings":
        if self.APP_HOST not in LOOPBACK_HOSTS and not self.ALLOW_LAN:
            raise ValueError(
                f"Binding APP_HOST to '{self.APP_HOST}' is forbidden by default for air-gap protection. "
                "Must be loopback (127.0.0.1 / localhost) unless ALLOW_LAN=true."
            )
        return self

    @field_validator("OLLAMA_BASE_URL")
    @classmethod
    def validate_ollama_base_url(cls, v: str) -> str:
        parsed = urlparse(v)
        hostname = parsed.hostname or ""
        if hostname not in LOOPBACK_HOSTS:
            raise ValueError(
                f"OLLAMA_BASE_URL '{v}' points to a non-loopback host ('{hostname}'). "
                "External AI service endpoints are strictly forbidden by sovereignty rules."
            )
        return v.rstrip("/")

    @property
    def input_dirs(self) -> List[Path]:
        return [Path(p.strip()) for p in self.ALLOWED_INPUT_DIRS.split(",") if p.strip()]

    @property
    def output_dirs(self) -> List[Path]:
        return [Path(p.strip()) for p in self.ALLOWED_OUTPUT_DIRS.split(",") if p.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
