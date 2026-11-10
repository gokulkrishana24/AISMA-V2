from __future__ import annotations

from typing import Any

import pytest

from ai.provider import LLMResult
from governance.audit import AuditLogger
from governance.budget import BudgetEnforcer, BudgetLimits
from governance.killswitch import KillSwitch
from governance.permissions import PermissionManager
from governance.policy import PolicyEngine


class MockProvider:
    provider_name = "mock"
    config = type("Cfg", (), {"default_model": "phi3.5:latest"})()

    def __init__(self, payload: dict[str, Any] | None = None, fail: Exception | None = None):
        self.payload = payload or {"summary": "ok", "confidence": 0.7}
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def extract_structured(self, text: str, schema: dict[str, Any], *, model: str | None = None, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"method": "extract_structured", "model": model, "text": text[:200]})
        if self.fail:
            raise self.fail
        return {"data": self.payload, "model": model or "mock", "raw": {}}

    def generate(self, prompt: str, **kwargs: Any) -> LLMResult:
        self.calls.append({"method": "generate", **kwargs})
        if self.fail:
            raise self.fail
        return LLMResult(model="mock", text="ok", provider="mock", raw={})

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> LLMResult:
        if self.fail:
            raise self.fail
        return LLMResult(model="mock", text="ok", provider="mock", raw={})

    def classify(self, text: str, labels: list[str], **kwargs: Any) -> LLMResult:
        if self.fail:
            raise self.fail
        return LLMResult(model="mock", text='{"label":"positive"}', provider="mock", raw={})

    def summarize(self, text: str, **kwargs: Any) -> LLMResult:
        if self.fail:
            raise self.fail
        return LLMResult(model="mock", text="summary", provider="mock", raw={})

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": "mock"}

    def list_models(self) -> list[dict[str, Any]]:
        return [{"name": "phi3.5:latest"}]


@pytest.fixture
def mock_provider() -> MockProvider:
    return MockProvider()


@pytest.fixture
def gov(tmp_path):
    audit = AuditLogger(tmp_path / "audit")
    ks = KillSwitch(tmp_path / "ks")
    perm = PermissionManager()
    pol = PolicyEngine({"default_deny_publishing": True})
    budget = BudgetEnforcer(tmp_path / "budget", strict=True)
    budget.set_limits("biz1", BudgetLimits(max_tokens_per_day=100000, max_actions_per_day=1000, max_cost_units_per_day=1000.0))
    return {"audit": audit, "kill_switch": ks, "permissions": perm, "policy": pol, "budget": budget}
