from __future__ import annotations

from agents.base import BaseAgent, ExecutionContext
from schemas.agent import AgentResult
from schemas.task import Task


class AgentExecutionService:
    """Thin execution wrapper. Governance remains in BaseAgent/orchestrator."""

    def execute(self, agent: BaseAgent, task: Task, context: ExecutionContext) -> AgentResult:
        return agent.execute(task, context)

    def execute_many(
        self, items: list[tuple[BaseAgent, Task, ExecutionContext]]
    ) -> list[AgentResult]:
        return [self.execute(a, t, c) for a, t, c in items]
