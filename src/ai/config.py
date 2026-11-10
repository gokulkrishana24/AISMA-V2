from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

GPU_PREFERENCES = {"auto", "prefer_gpu", "cpu_only"}


class AIConfigError(ValueError):
    """Raised when AI configuration is structurally invalid or out of range."""


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass
class AIConfig:
    """Centralized local AI configuration.

    Never hardcode secrets. Ollama is local by default; auth tokens (if any)
    should be supplied via environment-specific deployment config, not source.
    """

    ollama_endpoint: str = "http://localhost:11434"
    default_model: str = "qwen3.5:4b"
    fallback_model: str = "phi3.5:latest"
    request_timeout_seconds: float = 120.0
    max_tokens: int = 1024
    context_length: int = 4096
    temperature: float = 0.2
    concurrency_limit: int = 1  # shared inference service; safe for 4GB VRAM
    gpu_preference: str = "auto"  # auto|prefer_gpu|cpu_only
    gpu_memory_budget_mb: int = 3072  # conservative for 4GB laptop GPU
    cpu_fallback_enabled: bool = True
    allow_model_pull: bool = False  # explicit authorization required
    max_input_chars: int = 24000  # input-size limit before untrusted processing
    streaming_enabled: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ollama_endpoint": self.ollama_endpoint,
            "default_model": self.default_model,
            "fallback_model": self.fallback_model,
            "request_timeout_seconds": self.request_timeout_seconds,
            "max_tokens": self.max_tokens,
            "context_length": self.context_length,
            "temperature": self.temperature,
            "concurrency_limit": self.concurrency_limit,
            "gpu_preference": self.gpu_preference,
            "gpu_memory_budget_mb": self.gpu_memory_budget_mb,
            "cpu_fallback_enabled": self.cpu_fallback_enabled,
            "allow_model_pull": self.allow_model_pull,
            "max_input_chars": self.max_input_chars,
            "streaming_enabled": self.streaming_enabled,
        }


def validate_ai_config(config: AIConfig) -> AIConfig:
    """Validate an ``AIConfig`` and return it unchanged.

    Raises ``AIConfigError`` listing every problem found rather than failing on
    the first one, so misconfigured deployments are diagnosable at startup.
    """
    problems: list[str] = []

    if not isinstance(config.ollama_endpoint, str) or not config.ollama_endpoint.startswith(
        ("http://", "https://")
    ):
        problems.append("ollama_endpoint must be an http:// or https:// URL")
    if config.gpu_preference not in GPU_PREFERENCES:
        problems.append(f"gpu_preference must be one of {sorted(GPU_PREFERENCES)}")
    if config.request_timeout_seconds <= 0:
        problems.append("request_timeout_seconds must be greater than 0")
    if config.max_tokens < 1:
        problems.append("max_tokens must be at least 1")
    if config.context_length < 1:
        problems.append("context_length must be at least 1")
    if config.concurrency_limit < 1:
        problems.append("concurrency_limit must be at least 1")
    if not 0.0 <= config.temperature <= 2.0:
        problems.append("temperature must be between 0.0 and 2.0")
    if config.gpu_memory_budget_mb < 0:
        problems.append("gpu_memory_budget_mb must be zero or greater")
    if config.max_input_chars < 256:
        problems.append("max_input_chars must be at least 256")

    if problems:
        raise AIConfigError("Invalid AI configuration: " + "; ".join(problems))
    return config


def _coerce_yaml_value(key: str, value: Any, expected: type, source: Path) -> Any:
    """Coerce a YAML scalar to the dataclass field type or raise ``AIConfigError``."""
    if expected is bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        if isinstance(value, int):
            return bool(value)
        raise AIConfigError(f"'{key}' in {source} must be a boolean")
    if expected is int:
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise AIConfigError(f"'{key}' in {source} must be an integer")
        try:
            return int(value)
        except ValueError as err:
            raise AIConfigError(f"'{key}' in {source} must be an integer") from err
    if expected is float:
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise AIConfigError(f"'{key}' in {source} must be a number")
        try:
            return float(value)
        except ValueError as err:
            raise AIConfigError(f"'{key}' in {source} must be a number") from err
    if expected is str:
        if not isinstance(value, (str, int, float)) or isinstance(value, bool):
            raise AIConfigError(f"'{key}' in {source} must be a string")
        return str(value)
    raise AIConfigError(f"'{key}' in {source} has an unsupported configuration type")


def load_ai_config_file(
    path: str | Path,
    environ: os._Environ[str] | dict[str, str] | None = None,
) -> AIConfig:
    """Load optional YAML AI configuration layered over environment values.

    The file is optional: a missing path is not an error and yields exactly the
    environment-derived configuration. For keys the file specifies, YAML overrides
    the environment; unspecified keys keep their environment/default values.
    Unknown YAML keys are preserved in ``AIConfig.extra`` instead of being
    silently dropped.
    """
    source = Path(path)
    if not source.exists():
        return load_ai_config(environ)

    try:
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as err:
        raise AIConfigError(f"Unable to read AI config file '{source}': {err}") from err

    if raw is None:
        return load_ai_config(environ)
    if not isinstance(raw, dict):
        raise AIConfigError(f"AI config file '{source}' must contain a YAML mapping")

    config = load_ai_config(environ)
    known = {f.name for f in fields(AIConfig)} - {"extra"}
    for key, value in raw.items():
        name = str(key)
        if name not in known:
            config.extra[name] = value
            continue
        current = getattr(config, name)
        setattr(config, name, _coerce_yaml_value(name, value, type(current), source))

    return validate_ai_config(config)


def load_ai_config(environ: os._Environ[str] | dict[str, str] | None = None) -> AIConfig:
    env = os.environ if environ is None else environ
    # Accept both standard and prefixed env vars.
    def g(name: str, default: str) -> str:
        return env.get(f"AISMA_{name}", env.get(name, default))

    return validate_ai_config(
        AIConfig(
            ollama_endpoint=g("OLLAMA_ENDPOINT", "http://localhost:11434").rstrip("/"),
            default_model=g("DEFAULT_MODEL", "qwen3.5:4b"),
            fallback_model=g("FALLBACK_MODEL", "phi3.5:latest"),
            request_timeout_seconds=_env_float("AISMA_REQUEST_TIMEOUT_SECONDS", 120.0)
            if "AISMA_REQUEST_TIMEOUT_SECONDS" in env
            else float(g("REQUEST_TIMEOUT_SECONDS", "120")),
            max_tokens=_env_int("AISMA_MAX_TOKENS", int(g("MAX_TOKENS", "1024"))),
            context_length=_env_int("AISMA_CONTEXT_LENGTH", int(g("CONTEXT_LENGTH", "4096"))),
            temperature=_env_float("AISMA_TEMPERATURE", float(g("TEMPERATURE", "0.2"))),
            concurrency_limit=max(
                1, _env_int("AISMA_CONCURRENCY_LIMIT", int(g("CONCURRENCY_LIMIT", "1")))
            ),
            gpu_preference=g("GPU_PREFERENCE", "auto"),
            gpu_memory_budget_mb=_env_int(
                "AISMA_GPU_MEMORY_BUDGET_MB", int(g("GPU_MEMORY_BUDGET_MB", "3072"))
            ),
            cpu_fallback_enabled=_env_bool("AISMA_CPU_FALLBACK_ENABLED", True),
            allow_model_pull=_env_bool("AISMA_ALLOW_MODEL_PULL", False),
            max_input_chars=max(
                256, _env_int("AISMA_MAX_INPUT_CHARS", int(g("MAX_INPUT_CHARS", "24000")))
            ),
            streaming_enabled=_env_bool("AISMA_STREAMING_ENABLED", True),
        )
    )
