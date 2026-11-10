from __future__ import annotations

from typing import Any

from schemas.task import Task

from .base import BaseAgent, ExecutionContext


class CreativeStudioAgent(BaseAgent):
    agent_id = "creative_studio"
    agent_name = "Creative Studio Agent"
    description = "Creative briefs, prompts, and storyboards (no unconfirmed asset generation)."
    capabilities = ["creative_brief", "image_prompts", "video_storyboard", "visual_direction"]
    supported_task_types = ["creative_brief", "image_prompt_generation", "video_storyboard", "visual_campaign_plan"]
    required_permissions = ["read_business_data", "write_draft"]

    def validate_task(self, task: Task, context: ExecutionContext) -> None:
        if task.task_type not in self.supported_task_types:
            raise ValueError(f"Unsupported task_type: {task.task_type}")
        if task.business_id != context.business_id:
            raise PermissionError("Business isolation violation")

    def _execute_impl(self, task: Task, context: ExecutionContext) -> dict[str, Any]:
        schema = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}
        prompt = (
            f"{self._build_system_prompt(task, context)}\n"
            "Produce creative planning artifacts only. Do NOT claim an image/video was generated unless a real service confirmed it.\n"
            f"OBJECTIVE: {task.objective}\nINPUT: {task.input_data}\n"
            "Return JSON: summary, creative_brief{}, visual_direction{}, image_prompts[], video_scripts[], scene_breakdown[], asset_requirements[], suggested_aspect_ratios[], confidence, risks[]."
        )
        data = self._llm_json(task, context, prompt, schema, retries=1)
        data.setdefault("evidence", []).append({"type": "generation_status", "detail": "no_image_or_video_generation_service_confirmed"})
        return {
            "summary": data.get("summary", "Creative brief prepared"),
            "findings": [{"type": "creative_brief", "item": data.get("creative_brief", {})}, {"type": "image_prompts", "items": data.get("image_prompts", [])}],
            "recommendations": data.get("asset_requirements", []),
            "evidence": data.get("evidence", []),
            "confidence": float(data.get("confidence") or 0.6),
            "risks": data.get("risks", []),
            "requires_human_approval": False,
            "output": data,
        }
