from agents.base import ExecutionContext
from agents.registry import build_default_registry
from schemas.task import Task


def test_results_roi_deterministic_python_calculations(mock_provider, gov):
    # provider may be called for narrative; calculations must be correct regardless
    agent = build_default_registry(mock_provider).get("results_roi")
    ctx = ExecutionContext(business_id="biz1", **gov)
    t = Task(task_id="r1", business_id="biz1", agent_id="results_roi", task_type="roi_analysis", objective="roi",
             input_data={"metrics": {"spend": 200, "revenue": 500, "leads": 20, "conversions": 5, "clicks": 100, "impressions": 2000}})
    res = agent.execute(t, ctx)
    calcs = res.output["calculations"]
    assert calcs["roi"] == 1.5
    assert calcs["roas"] == 2.5
    assert calcs["cost_per_lead"] == 10.0
    assert calcs["conversion_rate"] == 0.05
    assert calcs["ctr"] == 0.05
    assert res.output["missing_values"] == []


def test_results_roi_missing_values_explicit(mock_provider, gov):
    agent = build_default_registry(mock_provider).get("results_roi")
    ctx = ExecutionContext(business_id="biz1", **gov)
    t = Task(task_id="r2", business_id="biz1", agent_id="results_roi", task_type="roi_analysis", objective="roi",
             input_data={"metrics": {"spend": 100}})
    res = agent.execute(t, ctx)
    assert res.output["calculations"]["roi"] is None
    assert "roi_requires_revenue_and_spend" in res.output["missing_values"]
    assert res.output["calculations"]["inputs"]["revenue"] is None
