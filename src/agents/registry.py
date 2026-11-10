from __future__ import annotations

from typing import Any

from ai.provider import LLMProvider

from .base import BaseAgent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> BaseAgent | None:
        return self._agents.get(agent_id)

    def list(self) -> list[dict[str, Any]]:
        return [
            {
                "agent_id": a.agent_id,
                "agent_name": a.agent_name,
                "description": a.description,
                "capabilities": a.capabilities,
                "supported_task_types": a.supported_task_types,
                "required_permissions": a.required_permissions,
            }
            for a in self._agents.values()
        ]

    def capabilities(self) -> dict[str, list[str]]:
        return {a.agent_id: list(a.supported_task_types) for a in self._agents.values()}


def build_default_registry(llm_provider: LLMProvider) -> AgentRegistry:
    # Lazy imports to keep module load light and avoid cycles.
    from .content_engine import ContentEngineAgent
    from .creative_studio import CreativeStudioAgent
    from .leads_conversations import LeadsConversationsAgent
    from .market_radar import MarketRadarAgent
    from .publishing_social import PublishingSocialAgent
    from .results_roi import ResultsROIAgent
    from .reviews_reputation import ReviewsReputationAgent
    from .search_visibility import SearchVisibilityAgent

    reg = AgentRegistry()
    for cls in [
        SearchVisibilityAgent,
        MarketRadarAgent,
        ContentEngineAgent,
        CreativeStudioAgent,
        PublishingSocialAgent,
        ReviewsReputationAgent,
        LeadsConversationsAgent,
        ResultsROIAgent,
    ]:
        reg.register(cls(llm_provider))
    return reg
