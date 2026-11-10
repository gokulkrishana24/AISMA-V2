from __future__ import annotations

from typing import Any

from schemas.task import Task

from .base import BaseAgent, ExecutionContext


class ReviewsReputationAgent(BaseAgent):
    agent_id = "reviews_reputation"
    agent_name = "Reviews & Reputation Agent"
    description = "Review classification/sentiment and response drafting with strict approval rules."
    capabilities = ["review_classification", "sentiment_analysis", "complaint_detection", "response_drafting"]
    supported_task_types = ["review_analysis", "review_response_draft", "reputation_summary"]
    required_permissions = ["read_business_data", "read_reviews", "draft_review_response"]

    def validate_task(self, task: Task, context: ExecutionContext) -> None:
        if task.task_type not in self.supported_task_types:
            raise ValueError(f"Unsupported task_type: {task.task_type}")
        if task.business_id != context.business_id:
            raise PermissionError("Business isolation violation")

    def _execute_impl(self, task: Task, context: ExecutionContext) -> dict[str, Any]:
        schema = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}
        prompt = (
            f"{self._build_system_prompt(task, context)}\n"
            "Analyze reviews and draft responses only. Never auto-publish replies. "
            "Flag negative reviews, complaints, refunds, compensation, legal or sensitive claims for human review.\n"
            f"OBJECTIVE: {task.objective}\nINPUT: {task.input_data}\n"
            "Return JSON: summary, classifications[], sentiment{}, complaints[], response_drafts[], escalation_required (bool), escalation_reasons[], confidence, risks[], evidence[]."
        )
        data = self._llm_json(task, context, prompt, schema, retries=1)
        sentiment = str((data.get("sentiment") or {}).get("label", "")).lower()
        has_complaint = bool(data.get("complaints")) or bool(data.get("escalation_required"))
        sensitive = sentiment in {"negative", "very_negative"} or has_complaint
        # deterministic override
        requires_approval = True if sensitive or task.task_type == "review_response_draft" else bool(data.get("escalation_required"))
        data["requires_human_approval"] = requires_approval
        return {
            "summary": data.get("summary", "Review analysis complete"),
            "findings": [{"type": "classifications", "items": data.get("classifications", [])}, {"type": "sentiment", "item": data.get("sentiment", {})}],
            "recommendations": data.get("response_drafts", []),
            "evidence": data.get("evidence", [{"type": "safety", "detail": "Responses are drafts only; no auto-publish."}]),
            "confidence": float(data.get("confidence") or 0.6),
            "risks": data.get("risks", []) + ([{"type": "approval", "detail": "Negative/complaint/sensitive responses require human approval."}] if requires_approval else []),
            "requires_human_approval": requires_approval,
            "output": data,
        }
