import os

import pytest

from ai.config import AIConfig
from ai.ollama_client import OllamaClient
from ai.ollama_provider import OllamaProvider

RUN_REAL = os.getenv("AISMA_RUN_REAL_OLLAMA_TESTS", "").lower() in {"1", "true", "yes"}


def _ollama_ready(model: str = "qwen3.5:4b") -> bool:
    try:
        c = OllamaClient(timeout_seconds=5)
        h = c.health_check()
        return bool(h.get("ok")) and c.has_model(model)
    except Exception:
        return False


@pytest.mark.skipif(not RUN_REAL, reason="Set AISMA_RUN_REAL_OLLAMA_TESTS=1 to run real Ollama tests")
@pytest.mark.skipif(not _ollama_ready(), reason="Local Ollama/model qwen3.5:4b not available")
def test_real_ollama_generate_smoke() -> None:
    cfg = AIConfig(default_model="qwen3.5:4b", request_timeout_seconds=60, max_tokens=32)
    provider = OllamaProvider(config=cfg)
    res = provider.generate("Reply with the word: READY", untrusted=False)
    assert isinstance(res.text, str) and len(res.text) > 0
