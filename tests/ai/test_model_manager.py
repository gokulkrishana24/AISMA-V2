import json
import threading
import time

import httpx
import pytest

from ai.config import AIConfig
from ai.model_manager import ModelManager
from ai.ollama_client import OllamaClient
from ai.ollama_provider import OllamaProvider
from ai.provider import LLMResult


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/api/tags":
        return httpx.Response(200, json={"models": [{"name": "qwen3.5:4b"}, {"name": "phi3.5:latest"}]})
    if path == "/api/generate":
        body = json.loads(request.content.decode()) if request.content else {}
        if body.get("model") == "qwen3.5:4b" and body.get("prompt") == "fail-primary":
            return httpx.Response(500, json={"error": "boom"})
        return httpx.Response(200, json={"model": body.get("model"), "response": f"ok:{body.get('model')}", "done": True})
    return httpx.Response(404)


def make_manager(tmp_path, **cfg_kwargs) -> ModelManager:
    cfg = AIConfig(
        default_model="qwen3.5:4b",
        fallback_model="phi3.5:latest",
        concurrency_limit=cfg_kwargs.pop("concurrency_limit", 2),
        **cfg_kwargs,
    )
    client = OllamaClient(base_url="http://test", transport=httpx.MockTransport(_handler))
    provider = OllamaProvider(config=cfg, client=client)
    return ModelManager(config=cfg, provider=provider, client=client)


def test_model_selection_and_availability(tmp_path) -> None:
    mm = make_manager(tmp_path)
    assert mm.is_model_available("qwen3.5:4b") is True
    sel = mm.select_model("qwen3.5:4b")
    assert sel.selected == "qwen3.5:4b"
    missing = mm.select_model("nope:model")
    assert missing.selected == "phi3.5:latest"
    assert missing.fallback_used is True


def test_run_with_fallback(tmp_path) -> None:
    mm = make_manager(tmp_path)
    out = mm.run_with_fallback("generate", prompt="fail-primary")
    assert isinstance(out, LLMResult)
    assert "phi3.5:latest" in out.text


def test_concurrency_limit(tmp_path) -> None:
    # slow handler
    lock = threading.Lock()
    active = 0
    max_active = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal active, max_active
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3.5:4b"}, {"name": "phi3.5:latest"}]})
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.05)
        with lock:
            active -= 1
        body = json.loads(request.content.decode())
        return httpx.Response(200, json={"model": body["model"], "response": "ok", "done": True})

    cfg = AIConfig(default_model="qwen3.5:4b", fallback_model="phi3.5:latest", concurrency_limit=1)
    client = OllamaClient(base_url="http://test", transport=httpx.MockTransport(handler))
    provider = OllamaProvider(config=cfg, client=client)
    mm = ModelManager(config=cfg, provider=provider, client=client)

    results = []
    errors = []
    def run():
        try:
            results.append(mm.run_with_fallback("generate", prompt="hi"))
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=run) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert not errors
    assert len(results) == 3
    assert max_active <= 1


def test_pull_requires_authorization(tmp_path) -> None:
    mm = make_manager(tmp_path, allow_model_pull=False)
    with pytest.raises(PermissionError):
        mm.pull_model("qwen3.5:4b", explicit_authorization=True)
    mm.config.allow_model_pull = True
    with pytest.raises(PermissionError):
        mm.pull_model("qwen3.5:4b", explicit_authorization=False)
