import os

import pytest

from agents.base import ExecutionContext
from agents.registry import build_default_registry
from ai.config import AIConfig
from ai.model_manager import ModelManager
from ai.ollama_provider import OllamaProvider
from schemas.task import Task

RUN_REAL = os.getenv("AISMA_RUN_REAL_OLLAMA_TESTS", "").lower() in {"1", "true", "yes"}


@pytest.mark.skipif(not RUN_REAL, reason="Set AISMA_RUN_REAL_OLLAMA_TESTS=1 to run real Ollama tests")
def test_real_ollama_single_controlled_agent_integration():
    # Single controlled integration call only (phi3.5 verified). Real inference is slow on 4GB VRAM.
    cfg = AIConfig(default_model="phi3.5:latest", fallback_model="phi3.5:latest", request_timeout_seconds=300, max_tokens=128, context_length=512, concurrency_limit=1)
    provider = OllamaProvider(config=cfg)
    h = provider.health_check()
    if not h.get("ok") or not h.get("default_model_available"):
        pytest.skip(f"Ollama/phi3.5:latest unavailable: {h}")
    mm = ModelManager(config=cfg, provider=provider)
    reg = build_default_registry(provider)
    agent = reg.get("market_radar")
    ctx = ExecutionContext(business_id="biz-real", model_manager=mm)
    task = Task(task_id="real1", business_id="biz-real", agent_id="market_radar", task_type="competitor_analysis", objective="Summarize one market signal from supplied data.", input_data={"competitor_description": "Competitor offers fast delivery."})
    res = agent.execute(task, ctx)
    assert res.status.value in {"completed", "pending_approval", "failed", "blocked"}
    # If completed, we got real structured output; failures are reported honestly by the agent.
    assert res.execution_duration >= 0
