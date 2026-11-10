from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import httpx


class OllamaError(RuntimeError):
    pass


class OllamaUnavailableError(OllamaError):
    pass


class OllamaModelNotFoundError(OllamaError):
    pass


class OllamaTimeoutError(OllamaError):
    pass


@dataclass
class OllamaResponse:
    model: str
    content: str
    raw: dict[str, Any]
    done: bool = True
    total_duration_ns: int | None = None
    eval_count: int | None = None
    prompt_eval_count: int | None = None


class OllamaClient:
    """HTTP client for a local Ollama server.

    No model downloads are performed unless `pull_model` is called with
    explicit_authorization=True and configuration permits it.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_seconds),
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> OllamaClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            resp = self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(f"Ollama request timed out: {path}") from exc
        except httpx.HTTPError as exc:
            raise OllamaUnavailableError(f"Ollama unavailable: {exc}") from exc
        if resp.status_code == 404:
            raise OllamaModelNotFoundError(f"Ollama resource not found: {path}")
        if resp.status_code >= 400:
            detail = resp.text[:500]
            raise OllamaError(f"Ollama error {resp.status_code} for {path}: {detail}")
        return resp

    def health_check(self) -> dict[str, Any]:
        try:
            # /api/tags is a lightweight local check; use short timeout so health checks don't block
            resp = self._client.request("GET", "/api/tags", timeout=3.0)
            if resp.status_code >= 400:
                return {"ok": False, "endpoint": self.base_url, "error": f"HTTP {resp.status_code}"}
            data = resp.json()
            return {"ok": True, "endpoint": self.base_url, "models_count": len(data.get("models", []))}
        except Exception as exc:
            return {"ok": False, "endpoint": self.base_url, "error": str(exc)}

    def list_models(self) -> list[dict[str, Any]]:
        resp = self._request("GET", "/api/tags")
        data = resp.json()
        models = data.get("models", [])
        if not isinstance(models, list):
            raise OllamaError("Invalid /api/tags response: models is not a list")
        return models

    def has_model(self, model: str) -> bool:
        models = self.list_models()
        target = model.strip()
        for m in models:
            name = str(m.get("name", ""))
            if name == target or name.startswith(target + ":") or target.startswith(name + ":"):
                return True
            # tolerate missing tag on either side
            if name.split(":")[0] == target.split(":")[0] and (":" not in target or ":" not in name):
                return True
        return any(str(m.get("name", "")) == target for m in models)

    def pull_model(self, model: str, *, explicit_authorization: bool = False) -> dict[str, Any]:
        if not explicit_authorization:
            raise PermissionError(
                "Model pull requires explicit authorization (explicit_authorization=True)."
            )
        resp = self._request("POST", "/api/pull", json={"name": model, "stream": False})
        return resp.json()

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        system: str | None = None,
        stream: bool = False,
        format: str | dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> OllamaResponse | Iterator[dict[str, Any]]:
        payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": stream}
        if model.lower().startswith("qwen3"):
            payload["think"] = False
        if system:
            payload["system"] = system
        if format is not None:
            payload["format"] = format
        if options:
            payload["options"] = options
        if stream:
            return self._stream("POST", "/api/generate", json=payload)
        resp = self._request("POST", "/api/generate", json=payload)
        data = resp.json()
        return OllamaResponse(
            model=str(data.get("model", model)),
            content=str(data.get("response", "")),
            raw=data,
            done=bool(data.get("done", True)),
            total_duration_ns=data.get("total_duration"),
            eval_count=data.get("eval_count"),
            prompt_eval_count=data.get("prompt_eval_count"),
        )

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        format: str | dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> OllamaResponse | Iterator[dict[str, Any]]:
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": stream}
        if model.lower().startswith("qwen3"):
            payload["think"] = False
        if format is not None:
            payload["format"] = format
        if options:
            payload["options"] = options
        if stream:
            return self._stream("POST", "/api/chat", json=payload)
        resp = self._request("POST", "/api/chat", json=payload)
        data = resp.json()
        msg = data.get("message") or {}
        content = msg.get("content", "") if isinstance(msg, dict) else ""
        return OllamaResponse(
            model=str(data.get("model", model)),
            content=str(content),
            raw=data,
            done=bool(data.get("done", True)),
            total_duration_ns=data.get("total_duration"),
            eval_count=data.get("eval_count"),
            prompt_eval_count=data.get("prompt_eval_count"),
        )

    def _stream(self, method: str, path: str, **kwargs: Any) -> Iterator[dict[str, Any]]:
        try:
            with self._client.stream(method, path, timeout=httpx.Timeout(self.timeout_seconds), **kwargs) as resp:
                if resp.status_code >= 400:
                    body = resp.read().decode("utf-8", errors="replace")[:500]
                    raise OllamaError(f"Ollama stream error {resp.status_code}: {body}")
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        yield {"raw": line}
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(f"Ollama stream timed out: {path}") from exc
        except httpx.HTTPError as exc:
            raise OllamaUnavailableError(f"Ollama stream unavailable: {exc}") from exc
