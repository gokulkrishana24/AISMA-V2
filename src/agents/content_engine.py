from __future__ import annotations

from typing import Any

from schemas.task import Task

from .base import BaseAgent, ExecutionContext


class ContentEngineAgent(BaseAgent):
    agent_id = "content_engine"
    agent_name = "Content Engine Agent"
    description = "Brand-compliant social/content drafting across channels."
    capabilities = ["social_copy", "captions", "content_calendar", "hooks", "cta", "channel_variants"]
    supported_task_types = ["content_generation", "caption_generation", "content_calendar", "copy_repurpose"]
    required_permissions = ["read_business_data", "write_draft"]

    def validate_task(self, task: Task, context: ExecutionContext) -> None:
        if task.task_type not in self.supported_task_types:
            raise ValueError(f"Unsupported task_type: {task.task_type}")
        if task.business_id != context.business_id:
            raise PermissionError("Business isolation violation")

    def _execute_impl(self, task: Task, context: ExecutionContext) -> dict[str, Any]:
        schema = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}
        restrictions = []
        if context.brand_context:
            restrictions = context.brand_context.prohibited_claims + context.brand_context.content_restrictions
        prompt = (
            f"{self._build_system_prompt(task, context)}\n"
            "Generate content drafts only. Do NOT invent testimonials, statistics, awards, or company claims. "
            "Follow brand restrictions/prohibited claims. Mark unverified claims in verification_flags.\n"
            f"PROHIBITED/RESTRICTIONS: {restrictions}\n"
            f"OBJECTIVE: {task.objective}\nINPUT: {task.input_data}\n"
            "Return JSON: summary, main_draft, alternative_hooks[], cta, hashtags[], seo_keywords[], channel_variants{}, verification_flags[], confidence, risks[]."
        )
        data = self._llm_json(task, context, prompt, schema, retries=1)
        return {
            "summary": data.get("summary", "Content draft generated"),
            "findings": [{"type": "main_draft", "item": data.get("main_draft", "")}, {"type": "channel_variants", "items": data.get("channel_variants", {})}],
            "recommendations": data.get("alternative_hooks", []),
            "evidence": [{"type": "brand_context", "detail": "used_if_provided", "missing": (context.brand_context.missing_information if context.brand_context else ["brand_context"])}],
            "confidence": float(data.get("confidence") or 0.6),
            "risks": data.get("risks", []) + [{"type": "verification", "detail": "Human review required before publishing; verify claims."}],
            "requires_human_approval": True,  # drafts intended for external use require approval before publish
            "output": data,
        }
