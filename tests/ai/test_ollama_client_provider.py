import json

import httpx
import pytest

from ai.config import AIConfig
from ai.ollama_client import OllamaClient, OllamaTimeoutError, OllamaUnavailableError
from ai.ollama_provider import OllamaProvider
from governance.killswitch import KillSwitch


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/api/tags":
        return httpx.Response(
            200,
            json={
                "models": [
                    {"name": "qwen3.5:4b", "model": "qwen3.5:4b"},
                    {"name": "phi3.5:latest", "model": "phi3.5:latest"},
                ]
            },
        )
    if path == "/api/generate":
        body = json.loads(request.content.decode()) if request.content else {}
        if body.get("model") == "missing:model":
            return httpx.Response(404, json={"error": "model not found"})
        if body.get("stream"):
            chunks = [
                json.dumps({"response": "Hel", "done": False}) + "\n",
                json.dumps({"response": "lo", "done": True, "eval_count": 2}) + "\n",
            ]
            return httpx.Response(200, content="".join(chunks).encode())
        if body.get("format") == "json":
            return httpx.Response(
                200, json={"model": body["model"], "response": '{"label":"positive","confidence":0.9}', "done": True}
            )
        return httpx.Response(200, json={"model": body["model"], "response": "ok-response", "done": True, "eval_count": 3})
    if path == "/api/chat":
        body = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={"model": body["model"], "message": {"role": "assistant", "content": "chat-ok"}, "done": True},
        )
    return httpx.Response(404, json={"error": "not found"})


def make_client() -> OllamaClient:
    return OllamaClient(base_url="http://test", transport=httpx.MockTransport(_handler))


def test_client_health_list_availability() -> None:
    c = make_client()
    h = c.health_check()
    assert h["ok"] is True
    assert h["models_count"] == 2
    models = c.list_models()
    assert len(models) == 2
    assert c.has_model("qwen3.5:4b") is True
    assert c.has_model("missing:model") is False


def test_client_generate_chat_structured() -> None:
    c = make_client()
    r = c.generate(model="qwen3.5:4b", prompt="hi")
    assert r.content == "ok-response"
    chat = c.chat(model="qwen3.5:4b", messages=[{"role": "user", "content": "hi"}])
    assert chat.content == "chat-ok"
    js = c.generate(model="qwen3.5:4b", prompt="classify", format="json")
    assert json.loads(js.content)["label"] == "positive"


def test_client_streaming() -> None:
    c = make_client()
    chunks = list(c.generate(model="qwen3.5:4b", prompt="hi", stream=True))
    assert any(c.get("response") == "Hel" for c in chunks)
    assert any(c.get("done") is True for c in chunks)


def test_client_timeout_and_unavailable() -> None:
    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout")

    c = OllamaClient(base_url="http://test", transport=httpx.MockTransport(timeout_handler))
    with pytest.raises(OllamaTimeoutError):
        c.list_models()

    def connect_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    c2 = OllamaClient(base_url="http://test", transport=httpx.MockTransport(connect_handler))
    with pytest.raises(OllamaUnavailableError):
        c2.list_models()


def test_provider_interface_methods(tmp_path) -> None:
    cfg = AIConfig(default_model="qwen3.5:4b", fallback_model="phi3.5:latest")
    provider = OllamaProvider(config=cfg, client=make_client())
    h = provider.health_check()
    assert h["ok"] is True
    assert provider.list_models()
    g = provider.generate("hello")
    assert g.text == "ok-response"
    ch = provider.chat([{"role": "user", "content": "hello"}])
    assert ch.text == "chat-ok"
    cl = provider.classify("great product", ["positive", "negative"])
    assert json.loads(cl.text)["label"] == "positive"
    su = provider.summarize("This is a long text about a product launch.")
    assert "ok-response" in su.text or su.text
    ex = provider.extract_structured("John from Cairo", {"type": "object", "properties": {"name": {"type": "string"}}})
    assert ex["data"]["label"] == "positive"


def test_provider_killswitch_blocks(tmp_path) -> None:
    ks = KillSwitch(tmp_path / "ks")
    ks.engage_global(reason="test", updated_by="test")
    provider = OllamaProvider(config=AIConfig(), client=make_client(), kill_switch=ks)
    with pytest.raises(PermissionError, match="Kill switch"):
        provider.generate("hello")
