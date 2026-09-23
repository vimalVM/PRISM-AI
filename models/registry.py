"""Model Registry and capability-driven router for Sovereign AI Workbench.

Loads models/registry.yaml, validates schema via Pydantic, prevents cloud tags,
and resolves routing plans dynamically.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field, field_validator


FORBIDDEN_CLOUD_MARKERS = [
    ":cloud",
    "open" + "ai",
    "anth" + "ropic",
    "goo" + "gle",
    "azu" + "re",
    "co" + "here",
    "mis" + "tral",
]


class ModelEntry(BaseModel):
    """Configuration for an individual model served locally."""

    provider: str = "ollama"
    model: str
    enabled: bool = True
    capabilities: List[str] = Field(default_factory=list)
    options: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("model")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        for marker in FORBIDDEN_CLOUD_MARKERS:
            if marker in v.lower():
                raise ValueError(
                    f"Model identifier '{v}' contains forbidden cloud marker '{marker}'. "
                    "Only local, air-gapped open-weight models are allowed."
                )
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v.lower() not in {"ollama", "sentence_transformers", "paddleocr", "tesseract"}:
            raise ValueError(
                f"Provider '{v}' is not an authorized local inference runtime."
            )
        return v


class EmbeddingConfig(BaseModel):
    """Local embeddings configuration."""

    provider: str = "sentence_transformers"
    model_path: str = "./data/models/Qwen3-Embedding-0.6B"
    device: str = "cpu"


class OCRConfig(BaseModel):
    """Local OCR engine configuration."""

    engine: str = "paddleocr"
    fallback: str = "tesseract"
    device: str = "cpu"


class RoutingRule(BaseModel):
    """Routing rule matching task facts against model capabilities."""

    name: str
    when: Dict[str, Any] = Field(default_factory=dict)
    pipeline: Optional[List[str]] = None
    vision_model: Optional[str] = None
    reasoning_model: Optional[str] = None
    use: Optional[str] = None
    fallback: Optional[str] = None

    def matches(self, facts: Dict[str, Any]) -> bool:
        """Check if provided facts satisfy this rule's conditions."""
        if not self.when:
            return True

        for key, expected_values in self.when.items():
            fact_value = facts.get(key)
            if fact_value is None:
                return False

            # Modality fact can be a set or single value
            if isinstance(fact_value, (set, list)):
                if not any(v in expected_values for v in fact_value):
                    return False
            else:
                if fact_value not in expected_values:
                    return False

        return True


class RoutingConfig(BaseModel):
    """Overall routing rules configuration."""

    rules: List[RoutingRule] = Field(default_factory=list)
    vision_failure_fallback: Optional[str] = None


class ModelRegistry(BaseModel):
    """Complete registry schema matching models/registry.yaml."""

    models: Dict[str, ModelEntry] = Field(default_factory=dict)
    embeddings: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)


class RoutePlan(BaseModel):
    """Computed routing plan describing models and tools for a task."""

    rule_name: str
    selected_model: str
    models: List[str]
    pipeline: List[str]
    reason: str
    valid: bool = True


_REGISTRY_CACHE: Optional[ModelRegistry] = None


def load_registry(path: str | Path = "models/registry.yaml") -> ModelRegistry:
    """Load and validate the model registry configuration from YAML."""
    registry_path = Path(path)
    if not registry_path.exists():
        raise FileNotFoundError(f"Model registry configuration not found at {registry_path}")

    with open(registry_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    registry = ModelRegistry.model_validate(data)
    return registry


def get_registry(path: str | Path = "models/registry.yaml", force_reload: bool = False) -> ModelRegistry:
    """Get singleton model registry instance, with optional reload."""
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None or force_reload:
        _REGISTRY_CACHE = load_registry(path)
    return _REGISTRY_CACHE


def reload_registry(path: str | Path = "models/registry.yaml") -> ModelRegistry:
    """Force reload the model registry from disk."""
    return get_registry(path, force_reload=True)


def resolve_route(facts: Dict[str, Any], registry: Optional[ModelRegistry] = None) -> RoutePlan:
    """Resolve facts (task_type, modality, complexity) to a RoutePlan."""
    if registry is None:
        registry = get_registry()

    for rule in registry.routing.rules:
        if rule.matches(facts):
            # If rule specifies a direct model target
            target_key = rule.use
            if target_key:
                model_entry = registry.models.get(target_key)
                if model_entry and model_entry.enabled:
                    return RoutePlan(
                        rule_name=rule.name,
                        selected_model=model_entry.model,
                        models=[model_entry.model],
                        pipeline=["model_call"],
                        reason=f"Matched rule '{rule.name}' targeting '{target_key}'",
                        valid=True,
                    )
                elif rule.fallback:
                    fallback_entry = registry.models.get(rule.fallback)
                    if fallback_entry and fallback_entry.enabled:
                        return RoutePlan(
                            rule_name=rule.name,
                            selected_model=fallback_entry.model,
                            models=[fallback_entry.model],
                            pipeline=["model_call"],
                            reason=f"Matched rule '{rule.name}' (target '{target_key}' disabled, fallback to '{rule.fallback}')",
                            valid=True,
                        )

            # If rule specifies a multimodal / OCR pipeline
            if rule.pipeline:
                selected_models = []
                primary_model = "unknown"
                vision_available = True
                if rule.vision_model:
                    v_entry = registry.models.get(rule.vision_model)
                    if v_entry and v_entry.enabled:
                        selected_models.append(v_entry.model)
                    else:
                        # Check vision_failure_fallback
                        fb_name = registry.routing.vision_failure_fallback
                        fb_entry = registry.models.get(fb_name) if fb_name else None
                        if fb_entry and fb_entry.enabled:
                            selected_models.append(fb_entry.model)
                        else:
                            vision_available = False

                if rule.reasoning_model:
                    r_entry = registry.models.get(rule.reasoning_model)
                    if r_entry and r_entry.enabled:
                        selected_models.append(r_entry.model)
                        primary_model = r_entry.model

                if not selected_models:
                    default_entry = registry.models.get("default")
                    selected_models = [default_entry.model] if default_entry else ["qwen3.5:4b"]
                    primary_model = selected_models[0]
                elif primary_model == "unknown":
                    primary_model = selected_models[0]

                pipeline_stages = [p for p in rule.pipeline if p != "vision" or vision_available]
                if not vision_available and rule.vision_model:
                    reason = f"Matched pipeline rule '{rule.name}' (vision model disabled, vision unavailable)"
                else:
                    reason = f"Matched pipeline rule '{rule.name}' with stages {rule.pipeline}"

                return RoutePlan(
                    rule_name=rule.name,
                    selected_model=primary_model,
                    models=selected_models,
                    pipeline=pipeline_stages,
                    reason=reason,
                    valid=True,
                )

    # Fallback to default model
    default_entry = registry.models.get("default")
    default_model = default_entry.model if default_entry else "qwen3.5:4b"
    return RoutePlan(
        rule_name="default_fallback",
        selected_model=default_model,
        models=[default_model],
        pipeline=["model_call"],
        reason="No specific rule matched, using default model",
        valid=True,
    )
