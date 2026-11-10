from __future__ import annotations

import json
import time
from collections.abc import Iterator
from typing import Any

from governance.injection import InjectionScanError, scan_untrusted_text
from governance.killswitch import KillSwitch

from .config import AIConfig
from .hardware import recommend_runtime_options
from .ollama_client import OllamaClient, OllamaError, OllamaResponse
from .provider import LLMProvider, LLMResult


class OllamaProvider(LLMProvider):
    provider_name = "ollama"

    def __init__(
        self,
        config: AIConfig | None = None,
        client: OllamaClient | None = None,
        kill_switch: KillSwitch | None = None,
    ):
        self.config = config or AIConfig()
        self.client = client or OllamaClient(
            base_url=self.config.ollama_endpoint,
            timeout_seconds=self.config.request_timeout_seconds,
        )
        self.kill_switch = kill_switch

    def _model(self, model: str | None) -> str:
        return model or self.config.default_model

    def _options(self, model: str | None = None, **overrides: Any) -> dict[str, Any]:
        opts = recommend_runtime_options(
            gpu_preference=self.config.gpu_preference,
            gpu_memory_budget_mb=self.config.gpu_memory_budget_mb,
            context_length=int(overrides.pop("num_ctx", self.config.context_length)),
            num_predict=int(overrides.pop("num_predict", self.config.max_tokens)),
        )
        opts.pop("_hardware_snapshot", None)
        opts.pop("_gpu_memory_budget_mb", None)
        opts["temperature"] = float(overrides.pop("temperature", self.config.temperature))
        opts.update(overrides)
        return opts

    def _guard_untrusted(self, text: str, *, source: str, allow_untrusted: bool) -> str:
        if self.kill_switch and self.kill_switch.is_engaged():
            raise PermissionError("Kill switch engaged; LLM operation blocked")
        if not isinstance(text, str):
            text = str(text)
        if len(text) > self.config.max_input_chars:
            text = text[: self.config.max_input_chars] + "\n[TRUNCATED_BY_INPUT_LIMIT]"
        if allow_untrusted:
            return text
        scan = scan_untrusted_text(text, strict=True, source=source)
        return scan["isolated_text"]

    def _to_result(self, resp: OllamaResponse, started: float) -> LLMResult:
        latency = (time.perf_counter() - started) * 1000
        return LLMResult(
            model=resp.model,
            text=resp.content,
            provider=self.provider_name,
            raw=resp.raw,
            usage={
                "eval_count": resp.eval_count,
                "prompt_eval_count": resp.prompt_eval_count,
                "total_duration_ns": resp.total_duration_ns,
            },
            latency_ms=latency,
        )

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system: str | None = None,
        stream: bool = False,
        untrusted: bool = False,
        source: str = "user",
        **kwargs: Any,
    ) -> LLMResult | Iterator[dict[str, Any]]:
        safe_prompt = self._guard_untrusted(prompt, source=source, allow_untrusted=not untrusted)
        safe_system = (
            self._guard_untrusted(system, source=f"{source}:system", allow_untrusted=not untrusted)
            if system
            else None
        )
        started = time.perf_counter()
        opts = self._options(model, **kwargs)
        result = self.client.generate(
            model=self._model(model),
            prompt=safe_prompt,
            system=safe_system,
            stream=stream,
            options=opts,
        )
        if stream:
            return result  # type: ignore[return-value]
        return self._to_result(result, started)  # type: ignore[arg-type]

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        stream: bool = False,
        untrusted: bool = False,
        source: str = "user",
        **kwargs: Any,
    ) -> LLMResult | Iterator[dict[str, Any]]:
        if self.kill_switch and self.kill_switch.is_engaged():
            raise PermissionError("Kill switch engaged; LLM operation blocked")
        safe_messages: list[dict[str, Any]] = []
        for m in messages:
            role = str(m.get("role", "user"))
            content = str(m.get("content", ""))
            # Treat user/external content as untrusted by default in chat.
            is_external = role in {"user", "tool"} or untrusted
            if is_external and untrusted:
                try:
                    scan = scan_untrusted_text(content, strict=True, source=source)
                    content = scan["isolated_text"]
                except InjectionScanError:
                    raise
            elif is_external and not untrusted:
                # still apply size limit
                if len(content) > self.config.max_input_chars:
                    content = content[: self.config.max_input_chars] + "\n[TRUNCATED_BY_INPUT_LIMIT]"
            safe_messages.append({**m, "role": role, "content": content})
        started = time.perf_counter()
        opts = self._options(model, **kwargs)
        result = self.client.chat(model=self._model(model), messages=safe_messages, stream=stream, options=opts)
        if stream:
            return result  # type: ignore[return-value]
        return self._to_result(result, started)  # type: ignore[arg-type]

    def classify(self, text: str, labels: list[str], *, model: str | None = None, **kwargs: Any) -> LLMResult:
        label_list = ", ".join(labels)
        prompt = (
            "Classify the text into exactly one label.\n"
            f"Allowed labels: {label_list}\n"
            "Return JSON with keys: label, confidence (0-1), rationale.\n\n"
            f"TEXT:\n{text}"
        )
        started = time.perf_counter()
        resp = self.client.generate(
            model=self._model(model),
            prompt=self._guard_untrusted(prompt, source="classify", allow_untrusted=False),
            format="json",
            options=self._options(model, **kwargs),
        )
        assert isinstance(resp, OllamaResponse)
        return self._to_result(resp, started)

    def summarize(self, text: str, *, model: str | None = None, max_points: int = 5, **kwargs: Any) -> LLMResult:
        prompt = (
            f"Summarize the following text in at most {max_points} concise bullet points. "
            "Do not invent facts not present in the text.\n\n"
            f"TEXT:\n{text}"
        )
        started = time.perf_counter()
        resp = self.client.generate(
            model=self._model(model),
            prompt=self._guard_untrusted(prompt, source="summarize", allow_untrusted=False),
            options=self._options(model, **kwargs),
        )
        assert isinstance(resp, OllamaResponse)
        return self._to_result(resp, started)

    def extract_structured(self, text: str, schema: dict[str, Any], *, model: str | None = None, **kwargs: Any) -> dict[str, Any]:
        prompt = (
            "Extract structured data from the text. Return ONLY valid JSON matching this schema description.\n"
            f"SCHEMA:\n{json.dumps(schema, indent=2)}\n\n"
            f"TEXT:\n{text}"
        )
        resp = self.client.generate(
            model=self._model(model),
            prompt=self._guard_untrusted(prompt, source="extract", allow_untrusted=False),
            format="json",
            options=self._options(model, **kwargs),
        )
        assert isinstance(resp, OllamaResponse)
        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError as exc:
            raise OllamaError(f"Model did not return valid JSON: {resp.content[:300]}") from exc
        if not isinstance(data, dict):
            raise OllamaError("Structured output must be a JSON object")
        return {"data": data, "model": resp.model, "raw": resp.raw}

    def health_check(self) -> dict[str, Any]:
        status = self.client.health_check()
        status["provider"] = self.provider_name
        status["default_model"] = self.config.default_model
        status["fallback_model"] = self.config.fallback_model
        if status.get("ok"):
            try:
                status["default_model_available"] = self.client.has_model(self.config.default_model)
                status["fallback_model_available"] = self.client.has_model(self.config.fallback_model)
            except Exception as exc:
                status["model_availability_error"] = str(exc)
        return status

    def list_models(self) -> list[dict[str, Any]]:
        return self.client.list_models()
