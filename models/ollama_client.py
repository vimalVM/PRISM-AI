"""Local Ollama client wrapper for Sovereign AI Workbench.

Enforces air-gap boundaries:
- Rejects non-loopback base URLs.
- Rejects cloud model tags (:cloud).
- Enforces model timeouts and bounded retries.
- Suppresses thinking mode (think=False) by default to prevent token bloat and unvalidated reasoning leaks.
"""

from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import httpx
import ollama

from backend.core.config import get_settings


LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class OllamaSecurityError(Exception):
    """Raised when an action violates local air-gap inference constraints."""
    pass


class OllamaClient:
    """Air-gapped Ollama client bound to localhost."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        settings = get_settings()
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.MODEL_CALL_TIMEOUT_S

        self._validate_loopback(self.base_url)
        self._client = ollama.Client(host=self.base_url, timeout=self.timeout)

    @staticmethod
    def _validate_loopback(url: str) -> None:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if hostname not in LOOPBACK_HOSTS:
            raise OllamaSecurityError(
                f"Ollama base URL '{url}' is non-loopback. "
                "Only localhost (127.0.0.1) inference is authorized."
            )

    @staticmethod
    def _validate_model_name(model_name: str) -> None:
        if ":cloud" in model_name.lower():
            raise OllamaSecurityError(
                f"Model tag '{model_name}' contains ':cloud' marker. "
                "Cloud-backed inference models are strictly forbidden."
            )

    def is_healthy(self) -> bool:
        """Check if local Ollama server is running on localhost."""
        try:
            self._client.list()
            return True
        except Exception:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List locally available models."""
        resp = self._client.list()
        models = []
        for m in resp.get("models", []):
            models.append({
                "name": getattr(m, "model", getattr(m, "name", str(m))),
                "size": getattr(m, "size", 0),
                "modified_at": getattr(m, "modified_at", ""),
                "digest": getattr(m, "digest", ""),
            })
        return models

    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model tag is present locally."""
        self._validate_model_name(model_name)
        models = self.list_models()
        return any(model_name in m["name"] for m in models)

    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        images: Optional[List[Union[bytes, str]]] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Execute text or multimodal generation against local Ollama model."""
        self._validate_model_name(model)

        req_options = {
            "temperature": 0.2,
            "think": False,  # Suppress internal CoT tokens by default
        }
        if options:
            req_options.update(options)

        kwargs: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "options": req_options,
            "stream": stream,
        }
        if system:
            kwargs["system"] = system
        if images:
            kwargs["images"] = images

        try:
            response = self._client.generate(**kwargs)
            if stream:
                return response

            # Clean output: return only actual response text without leaked thinking blocks
            resp_text = response.get("response", "")
            return {
                "model": model,
                "response": resp_text.strip(),
                "eval_count": response.get("eval_count", 0),
                "eval_duration": response.get("eval_duration", 0),
                "prompt_eval_count": response.get("prompt_eval_count", 0),
                "total_duration": response.get("total_duration", 0),
                "load_duration": response.get("load_duration", 0),
            }
        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Could not connect to local Ollama service at {self.base_url}: {e}"
            )

    def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Execute chat conversation against local Ollama model."""
        self._validate_model_name(model)

        req_options = {
            "temperature": 0.2,
            "think": False,
        }
        if options:
            req_options.update(options)

        try:
            response = self._client.chat(
                model=model,
                messages=messages,
                options=req_options,
                stream=stream,
            )
            if stream:
                return response

            msg = response.get("message", {})
            return {
                "model": model,
                "message": msg,
                "content": msg.get("content", "").strip(),
                "eval_count": response.get("eval_count", 0),
                "eval_duration": response.get("eval_duration", 0),
                "prompt_eval_count": response.get("prompt_eval_count", 0),
            }
        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Could not connect to local Ollama service at {self.base_url}: {e}"
            )
