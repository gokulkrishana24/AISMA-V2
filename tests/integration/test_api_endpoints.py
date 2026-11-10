from __future__ import annotations

import os

os.environ["AISMA_TEST_MODE"] = "true"

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoints(client):
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "ok"

    r2 = client.get("/api/v1/health")
    assert r2.status_code == 200
    assert r2.json()["service"] == "aisma_backend"


def test_ai_hardware_and_health(client):
    r_hw = client.get("/api/v1/ai/hardware")
    assert r_hw.status_code == 200
    hw = r_hw.json()
    assert "cpu_count" in hw
    assert "ram_total_mb" in hw
    assert "nvidia_smi_available" in hw

    r_health = client.get("/api/v1/ai/health")
    assert r_health.status_code == 200
    h = r_health.json()
    assert h["provider"] == "ollama"
    assert "active_model" in h


def test_ai_models_and_benchmarks(client):
    r_models = client.get("/api/v1/ai/models")
    assert r_models.status_code == 200
    models = r_models.json()
    assert isinstance(models, list)

    r_bench = client.get("/api/v1/ai/benchmarks")
    assert r_bench.status_code == 200
    bench = r_bench.json()
    assert isinstance(bench, list)
    # Check 9B model provenance reflects timeout on 4GB VRAM
    qwen_9b = next((b for b in bench if "9b" in b["model_tag"]), None)
    if qwen_9b:
        assert qwen_9b["provenance"]["status"] == "timed_out"
        assert qwen_9b["tokens_per_second"] is None


def test_agents_fleet(client):
    r = client.get("/api/v1/agents")
    assert r.status_code == 200
    agents = r.json()
    assert len(agents) == 8
    agent_ids = {a["id"] for a in agents}
    assert "content_engine" in agent_ids
    assert "publishing_social" in agent_ids
    assert "results_roi" in agent_ids


def test_governance_killswitch_and_audit(client):
    # Status
    r_ks = client.get("/api/v1/governance/killswitch")
    assert r_ks.status_code == 200
    assert "engaged" in r_ks.json()

    # Toggle
    r_toggle = client.post(
        "/api/v1/governance/killswitch",
        json={"engaged": False, "reason": "Test clearance", "actor": "human_admin"},
    )
    assert r_toggle.status_code == 200
    assert r_toggle.json()["engaged"] is False

    # Audit list and verify
    r_audit = client.get("/api/v1/governance/audit")
    assert r_audit.status_code == 200
    assert "chainValid" in r_audit.json()

    r_verify = client.post("/api/v1/governance/audit/verify")
    assert r_verify.status_code == 200
    assert r_verify.json()["valid"] is True


def test_brand_os_and_budget(client):
    r_brand = client.get("/api/v1/brand-os")
    assert r_brand.status_code == 200
    assert "brand_voice" in r_brand.json()

    r_budget = client.get("/api/v1/budget")
    assert r_budget.status_code == 200
    assert "monthlyBudget" in r_budget.json()

