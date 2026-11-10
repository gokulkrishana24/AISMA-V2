from agents.base import ExecutionContext
from agents.registry import build_default_registry
from schemas.agent import AgentRunStatus
from schemas.task import Task

REQUIRED_AGENT_IDS = {
    "search_visibility", "market_radar", "content_engine", "creative_studio",
    "publishing_social", "reviews_reputation", "leads_conversations", "results_roi",
}


def test_registry_has_eight_agents(mock_provider):
    reg = build_default_registry(mock_provider)
    items = reg.list()
    assert len(items) == 8
    assert {i["agent_id"] for i in items} == REQUIRED_AGENT_IDS
    for i in items:
        assert i["agent_name"]
        assert i["supported_task_types"]
        assert "read_business_data" in i["required_permissions"] or i["agent_id"] == "orchestrator"


def test_agent_contract_methods(mock_provider, gov):
    reg = build_default_registry(mock_provider)
    ctx = ExecutionContext(business_id="biz1", **gov)
    for agent in [reg.get(aid) for aid in REQUIRED_AGENT_IDS]:
        assert agent.health_check()["ok"] is True
        assert hasattr(agent, "validate_task")
        assert hasattr(agent, "execute")
        assert hasattr(agent, "serialize_result")
        # simple execute path with supported task
        task_type = agent.supported_task_types[0]
        t = Task(task_id=f"t-{agent.agent_id}", business_id="biz1", agent_id=agent.agent_id, task_type=task_type, objective="test")
        if agent.agent_id == "results_roi":
            t = t.model_copy(update={"input_data": {"metrics": {"spend": 100, "revenue": 150, "leads": 10, "conversions": 2, "clicks": 50, "impressions": 1000}}})
        if agent.agent_id == "publishing_social":
            t = t.model_copy(update={"input_data": {"integration_configured": False}})
        res = agent.execute(t, ctx)
        assert res.task_id == t.task_id
        assert res.agent_id == agent.agent_id
        assert res.status in {AgentRunStatus.COMPLETED, AgentRunStatus.PENDING_APPROVAL, AgentRunStatus.BLOCKED, AgentRunStatus.FAILED}
        ser = agent.serialize_result(res)
        assert ser["agent_id"] == agent.agent_id
