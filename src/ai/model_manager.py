from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from governance.killswitch import KillSwitch

from .config import AIConfig
from .hardware import detect_hardware
from .ollama_client import OllamaClient, OllamaError
from .provider import LLMProvider, LLMResult
from .registry import ModelRegistry


@dataclass
class ModelSelection:
    requested: str
    selected: str
    fallback_used: bool
    reason: str
    hardware: dict[str, Any]


class ModelManager:
    """Manages local model selection and a shared inference service.

    Uses one shared provider/runtime; does not load eight separate LLMs.
    """

    def __init__(
        self,
        config: AIConfig | None = None,
        provider: LLMProvider | None = None,
        registry: ModelRegistry | None = None,
        kill_switch: KillSwitch | None = None,
        client: OllamaClient | None = None,
    ):
        self.config = config or AIConfig()
        self.registry = registry or ModelRegistry()
        self.kill_switch = kill_switch
        self._client = client
        self._provider = provider
        self._semaphore = threading.BoundedSemaphore(max(1, self.config.concurrency_limit))
        self._lock = threading.Lock()
        self._active_model = self.config.default_model
        self._fallback_model = self.config.fallback_model
        self._last_health: dict[str, Any] | None = None

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            # Lazy import to avoid circulars and keep extensibility.
            from .ollama_provider import OllamaProvider

            self._provider = OllamaProvider(
                config=self.config,
                client=self._client
                or OllamaClient(
                    base_url=self.config.ollama_endpoint,
                    timeout_seconds=self.config.request_timeout_seconds,
                ),
                kill_switch=self.kill_switch,
            )
        return self._provider

    @contextmanager
    def inference_slot(self) -> Iterator[None]:
        acquired = self._semaphore.acquire(timeout=self.config.request_timeout_seconds)
        if not acquired:
            raise TimeoutError("Timed out waiting for inference concurrency slot")
        try:
            yield
        finally:
            self._semaphore.release()

    def list_local_models(self) -> list[dict[str, Any]]:
        return self.provider.list_models()

    def list_registry(self) -> list[dict[str, Any]]:
        return self.registry.to_dict()

    def is_model_available(self, model: str) -> bool:
        try:
            models = self.list_local_models()
        except Exception:
            return False
        names = [str(m.get("name", "")) for m in models]
        if model in names:
            return True
        base = model.split(":")[0]
        return any(n == model or n.split(":")[0] == base for n in names)

    def hardware_snapshot(self) -> dict[str, Any]:
        return detect_hardware().to_dict()

    def select_model(self, requested: str | None = None) -> ModelSelection:
        hw = self.hardware_snapshot()
        requested_model = requested or self._active_model or self.config.default_model
        reason = "requested model selected"
        fallback_used = False
        selected = requested_model

        # Hardware-aware adjustment: on 4GB VRAM / low available RAM, prefer smaller/fallback.
        vram = hw.get("vram_total_mb") or 0
        ram_avail = hw.get("ram_available_mb") or 0
        constrained = (vram and vram <= 4096) or (ram_avail and ram_avail < 4096)
        if constrained and requested_model == self.config.default_model and "9b" in requested_model:
            candidate = self.config.fallback_model
            if self.is_model_available(candidate):
                selected = candidate
                fallback_used = True
                reason = "hardware constrained (4GB VRAM/low RAM); selected fallback model"

        if not self.is_model_available(selected):
            if self.config.cpu_fallback_enabled and self.is_model_available(self._fallback_model):
                selected = self._fallback_model
                fallback_used = selected != requested_model
                reason = f"requested model unavailable; fell back to {selected}"
            else:
                reason = f"requested model unavailable and no fallback available: {requested_model}"
                # Keep selected for error reporting; caller will see failure.
        return ModelSelection(requested_model, selected, fallback_used, reason, hw)

    def set_active_model(self, model: str) -> None:
        with self._lock:
            self._active_model = model

    def set_fallback_model(self, model: str) -> None:
        with self._lock:
            self._fallback_model = model

    def health(self) -> dict[str, Any]:
        try:
            h = self.provider.health_check()
        except Exception as exc:
            h = {"ok": False, "error": str(exc), "provider": "ollama"}
        h["hardware"] = self.hardware_snapshot()
        h["active_model"] = self._active_model
        h["fallback_model"] = self._fallback_model
        h["concurrency_limit"] = self.config.concurrency_limit
        self._last_health = h
        return h

    def run_with_fallback(
        self,
        operation: str,
        *,
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run a provider operation with hardware-aware selection and graceful fallback."""
        if self.kill_switch and self.kill_switch.is_engaged():
            raise PermissionError("Kill switch engaged; model operation blocked")
        selection = self.select_model(model)
        primary = selection.selected
        attempts = [(primary, selection.reason)]
        if self.config.cpu_fallback_enabled and self._fallback_model not in {primary}:
            attempts.append((self._fallback_model, "graceful fallback after primary error"))

        last_exc: Exception | None = None
        for candidate, reason in attempts:
            try:
                with self.inference_slot():
                    fn = getattr(self.provider, operation)
                    result = fn(**{**kwargs, "model": candidate})
                if isinstance(result, LLMResult):
                    result.raw.setdefault("_model_selection", selection.__dict__)
                    result.raw.setdefault("_attempt", {"model": candidate, "reason": reason})
                return result
            except Exception as exc:  # noqa: BLE001 - controlled fallback boundary
                last_exc = exc
                continue
        raise OllamaError(f"All model attempts failed: {attempts}") from last_exc

    def pull_model(self, model: str, *, explicit_authorization: bool = False) -> dict[str, Any]:
        if not explicit_authorization or not self.config.allow_model_pull:
            raise PermissionError(
                "Model pull requires explicit_authorization=True and AISMA_ALLOW_MODEL_PULL=true."
            )
        client = self._client or OllamaClient(self.config.ollama_endpoint, self.config.request_timeout_seconds)
        return client.pull_model(model, explicit_authorization=True)
