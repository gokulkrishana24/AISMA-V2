
from agents.registry import build_default_registry
from ai.model_manager import ModelManager
from ai.provider import LLMResult
from governance.audit import AuditLogger, verify_audit_chain
from governance.budget import BudgetEnforcer, BudgetLimits
from governance.killswitch import KillSwitch
from governance.permissions import PermissionManager
from governance.policy import PolicyEngine
from orchestrator.orchestrator import Orchestrator
from schemas.task import Task


class MgrProvider:
    provider_name = "mock"
    config = type("C", (), {"default_model": "phi3.5:latest", "ollama_endpoint": "http://x", "request_timeout_seconds": 5, "concurrency_limit": 1})()
    def extract_structured(self, text, schema, model=None, **k):
        # tailor simple payloads per agent cue in text
        if "ROI" in text or "CALCULATIONS" in text:
            return {"data": {"summary": "roi summary"}, "model": model or "m"}
        if "Publishing" in text or "publishing" in text:
            return {"data": {"summary": "prep", "status_detail": "ready_for_approval", "publishing_job": {}, "validation": {}, "confidence": 0.9}, "model": model or "m"}
        return {"data": {"summary": "ok", "confidence": 0.6, "findings": [], "recommendations": [], "evidence": [], "risks": []}, "model": model or "m"}
    def generate(self, *a, **k): return LLMResult(model="m", text="ok", provider="mock")
    def chat(self, *a, **k): return LLMResult(model="m", text="ok", provider="mock")
    def classify(self, *a, **k): return LLMResult(model="m", text="{}", provider="mock")
    def summarize(self, *a, **k): return LLMResult(model="m", text="ok", provider="mock")
    def health_check(self): return {"ok": True}
    def list_models(self): return [{"name": "phi3.5:latest"}]


def make_orchestrator(tmp_path, provider=None, permissions=None, kill_switch=None, budget=None, audit=True):
    provider = provider or MgrProvider()
    mm = ModelManager(provider=provider)
    reg = build_default_registry(provider)
    audit_logger = AuditLogger(tmp_path / "audit") if audit else None
    ks = kill_switch or KillSwitch(tmp_path / "ks")
    perm = permissions or PermissionManager()
    bud = budget or BudgetEnforcer(tmp_path / "budget", strict=True)
    try:
        bud.set_limits("biz1", BudgetLimits(100000, 1000, 1000.0))
    except Exception:
        pass
    return Orchestrator(registry=reg, model_manager=mm, permissions=perm, policy=PolicyEngine({"default_deny_publishing": True}), kill_switch=ks, budget=bud, audit=audit_logger), audit_logger


def test_orchestrator_dependency_planning_and_execution(tmp_path):
    orch, _ = make_orchestrator(tmp_path)
    tasks = [
        Task(task_id="a", business_id="biz1", agent_id="market_radar", task_type="competitor_analysis", objective="analyze"),
        Task(task_id="b", business_id="biz1", agent_id="content_engine", task_type="content_generation", objective="draft", dependencies=["a"]),
    ]
    report = orch.execute(business_id="biz1", objective="plan", tasks=tasks, strategy="dependency_based")
    assert report.task_count == 2
    assert report.metadata["schedule"]["strategy"] == "dependency_based"
    assert report.results
    # dependency respected: both completed/pending
    statuses = {r["task_id"]: r["status"] for r in report.results}
    assert statuses["a"] in {"completed", "pending_approval"}
    assert statuses["b"] in {"completed", "pending_approval"}


def test_orchestrator_sequential_strategy(tmp_path):
    orch, _ = make_orchestrator(tmp_path)
    tasks = [
        Task(task_id="1", business_id="biz1", agent_id="market_radar", task_type="competitor_analysis", objective="a"),
        Task(task_id="2", business_id="biz1", agent_id="search_visibility", task_type="seo_analysis", objective="b"),
    ]
    report = orch.execute(business_id="biz1", objective="seq", tasks=tasks, strategy="sequential")
    assert report.metadata["schedule"]["strategy"] == "sequential"
    assert len(report.metadata["schedule"]["ordered_task_ids"]) == 2


def test_orchestrator_kill_switch_blocks(tmp_path):
    ks = KillSwitch(tmp_path / "ks")
    ks.engage_business("biz1", reason="x", updated_by="t")
    orch, _ = make_orchestrator(tmp_path, kill_switch=ks)
    report = orch.execute(business_id="biz1", objective="x", tasks=[Task(task_id="1", business_id="biz1", agent_id="market_radar", task_type="competitor_analysis", objective="x")])
    assert report.status == "failed"
    assert any("Kill switch" in e for e in report.errors)


def test_orchestrator_business_isolation(tmp_path):
    orch, _ = make_orchestrator(tmp_path)
    report = orch.execute(business_id="biz1", objective="x", tasks=[Task(task_id="1", business_id="biz2", agent_id="market_radar", task_type="competitor_analysis", objective="x")])
    assert report.status == "failed"
    assert any("isolation" in e.lower() or "biz2" in e for e in report.errors)


def test_orchestrator_failure_recovery_and_partial(tmp_path):
    class Flaky(MgrProvider):
        def extract_structured(self, text, schema, model=None, **k):
            if "market" in text.lower() or "competitor" in text.lower():
                raise RuntimeError("llm boom")
            return super().extract_structured(text, schema, model=model, **k)
    orch, _ = make_orchestrator(tmp_path, provider=Flaky())
    tasks = [
        Task(task_id="bad", business_id="biz1", agent_id="market_radar", task_type="competitor_analysis", objective="x", max_retries=1),
        Task(task_id="ok", business_id="biz1", agent_id="search_visibility", task_type="seo_analysis", objective="y"),
    ]
    report = orch.execute(business_id="biz1", objective="x", tasks=tasks, strategy="priority_based")
    assert report.status in {"partially_completed", "failed"}
    statuses = {r["task_id"]: r["status"] for r in report.results}
    assert "ok" in statuses
    assert statuses["bad"] == "failed"


def test_orchestrator_idempotency(tmp_path):
    orch, _ = make_orchestrator(tmp_path)
    t = Task(task_id="1", business_id="biz1", agent_id="market_radar", task_type="competitor_analysis", objective="x", idempotency_key="same")
    orch.execute(business_id="biz1", objective="x", tasks=[t])
    orch.execute(business_id="biz1", objective="x", tasks=[Task(task_id="2", business_id="biz1", agent_id="market_radar", task_type="competitor_analysis", objective="x", idempotency_key="same")])
    # task manager inside orchestrator deduped add; at least no crash and first task remains
    assert orch.task_manager.get("1") is not None


def test_orchestrator_audit_events(tmp_path):
    orch, audit = make_orchestrator(tmp_path)
    orch.execute(business_id="biz1", objective="x", tasks=[Task(task_id="1", business_id="biz1", agent_id="market_radar", task_type="competitor_analysis", objective="x")])
    entries = audit.read_entries("biz1")
    assert len(entries) >= 1
    ok, msg = verify_audit_chain(entries)
    assert ok, msg
    assert any(e["action"] in {"orchestration_complete", "agent_execute_complete", "agent_execute_start"} for e in entries)
