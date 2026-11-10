from __future__ import annotations

from typing import Any

from schemas.task import Task

from .base import BaseAgent, ExecutionContext


class MarketRadarAgent(BaseAgent):
    agent_id = "market_radar"
    agent_name = "Market Radar Agent"
    description = "Competitor and market signal analysis from supplied data."
    capabilities = ["competitor_analysis", "market_trends", "positioning", "opportunity_detection"]
    supported_task_types = ["competitor_analysis", "market_trend_analysis", "positioning_analysis"]
    required_permissions = ["read_business_data", "read_analytics", "write_draft"]

    def validate_task(self, task: Task, context: ExecutionContext) -> None:
        if task.task_type not in self.supported_task_types:
            raise ValueError(f"Unsupported task_type: {task.task_type}")
        if task.business_id != context.business_id:
            raise PermissionError("Business isolation violation")

    def _execute_impl(self, task: Task, context: ExecutionContext) -> dict[str, Any]:
        schema = {"type": "object", "properties": {"summary": {"type": "string"}, "confidence": {"type": "number"}}, "required": ["summary"]}
        prompt = (
            f"{self._build_system_prompt(task, context)}\n"
            "Analyze supplied competitor/market data only. NEVER fabricate competitor campaigns, prices, or promotions. "
            "If data is missing, mark unknown.\n"
            f"OBJECTIVE: {task.objective}\nINPUT: {task.input_data}\n"
            "Return JSON: summary, competitor_observations[], market_signals[], strategic_opportunities[], risks[], recommended_actions[], confidence, evidence[]."
        )
        data = self._llm_json(task, context, prompt, schema, retries=1)
        return {
            "summary": data.get("summary", "Market radar analysis complete"),
            "findings": [
                {"type": "competitor_observations", "items": data.get("competitor_observations", [])},
                {"type": "market_signals", "items": data.get("market_signals", [])},
                {"type": "strategic_opportunities", "items": data.get("strategic_opportunities", [])},
            ],
            "recommendations": data.get("recommended_actions", []),
            "evidence": data.get("evidence", [{"type": "data_source", "detail": "analysis_based_on_supplied_data"}]),
            "confidence": float(data.get("confidence") or 0.5),
            "risks": data.get("risks", []),
            "requires_human_approval": False,
            "output": data,
        }
