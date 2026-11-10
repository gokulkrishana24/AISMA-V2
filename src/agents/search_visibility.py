from __future__ import annotations

from typing import Any

from schemas.task import Task

from .base import BaseAgent, ExecutionContext


class SearchVisibilityAgent(BaseAgent):
    agent_id = "search_visibility"
    agent_name = "Search Visibility Agent"
    description = "SEO opportunity discovery and search visibility analysis from supplied data."
    capabilities = ["keyword_analysis", "search_intent", "content_gaps", "optimization_recommendations"]
    supported_task_types = ["seo_analysis", "keyword_research", "search_visibility", "content_gap_analysis"]
    required_permissions = ["read_business_data", "read_analytics", "write_draft"]

    def validate_task(self, task: Task, context: ExecutionContext) -> None:
        if task.task_type not in self.supported_task_types:
            raise ValueError(f"Unsupported task_type for {self.agent_id}: {task.task_type}")
        if task.business_id != context.business_id:
            raise PermissionError("Business isolation violation")

    def _execute_impl(self, task: Task, context: ExecutionContext) -> dict[str, Any]:
        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "keyword_opportunities": {"type": "array"},
                "search_intent": {"type": "array"},
                "content_gaps": {"type": "array"},
                "suggested_topics": {"type": "array"},
                "optimization_recommendations": {"type": "array"},
                "confidence": {"type": "number"},
                "evidence": {"type": "array"},
                "risks": {"type": "array"},
            },
            "required": ["summary"],
        }
        prompt = (
            f"{self._build_system_prompt(task, context)}\n"
            "Task: analyze supplied search/SEO data only. Do NOT invent live rankings or search-volume data. "
            "Mark findings as 'analysis_based_on_supplied_data' when no real integration exists.\n"
            f"OBJECTIVE: {task.objective}\nINPUT: {task.input_data}\n"
            "Return JSON with summary, keyword_opportunities, search_intent, content_gaps, suggested_topics, "
            "optimization_recommendations, confidence (0-1), evidence, risks."
        )
        data = self._llm_json(task, context, prompt, schema, retries=1)
        data.setdefault("evidence", []).append({"type": "data_source", "detail": "analysis_based_on_supplied_data; no live SEO integration"})
        return {
            "summary": data.get("summary", "Search visibility analysis complete"),
            "findings": [
                {"type": "keyword_opportunities", "items": data.get("keyword_opportunities", [])},
                {"type": "search_intent", "items": data.get("search_intent", [])},
                {"type": "content_gaps", "items": data.get("content_gaps", [])},
            ],
            "recommendations": data.get("optimization_recommendations", []) + [{"type": "suggested_topics", "items": data.get("suggested_topics", [])}],
            "evidence": data.get("evidence", []),
            "confidence": float(data.get("confidence") or 0.5),
            "risks": data.get("risks", []),
            "requires_human_approval": False,
            "output": data,
        }
