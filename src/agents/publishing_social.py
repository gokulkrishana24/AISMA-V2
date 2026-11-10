from __future__ import annotations

from typing import Any

from schemas.task import Task

from .base import BaseAgent, ExecutionContext


class PublishingSocialAgent(BaseAgent):
    agent_id = "publishing_social"
    agent_name = "Publishing & Social Agent"
    description = "Prepares/validates publishing jobs; never bypasses approval or invents publication."
    capabilities = ["queue_preparation", "format_validation", "schedule_recommendation", "status_tracking"]
    supported_task_types = ["prepare_publishing_job", "validate_post", "recommend_schedule", "reconcile_status"]
    required_permissions = ["read_business_data", "request_publish", "schedule"]

    def validate_task(self, task: Task, context: ExecutionContext) -> None:
        if task.task_type not in self.supported_task_types:
            raise ValueError(f"Unsupported task_type: {task.task_type}")
        if task.business_id != context.business_id:
            raise PermissionError("Business isolation violation")

    def _execute_impl(self, task: Task, context: ExecutionContext) -> dict[str, Any]:
        integration = task.input_data.get("integration_configured", False)
        credentials = task.input_data.get("publishing_credentials_present", False)
        content_state = str(task.input_data.get("content_state") or "draft")
        # Deterministic checks (no LLM needed for core governance decisions)
        can_request_actual_publish = bool(
            integration and credentials and content_state == "approved" and context.has_human_approval
        )
        if task.task_type == "prepare_publishing_job" and not integration:
            result = {
                "summary": "Publishing integration not configured; prepared local draft job only.",
                "status_detail": "integration_not_configured",
                "publishing_job": {
                    "state": "pending_integration",
                    "requested_platform": task.input_data.get("platform"),
                    "content_state": content_state,
                },
                "validation": {"integration_configured": False, "human_approval_required": True},
                "confidence": 1.0,
                "risks": [{"type": "integration", "detail": "No platform integration configured; cannot publish."}],
                "requires_human_approval": True,
                "evidence": [{"type": "system", "detail": "No live publishing API call made."}],
            }
            return {**result, "findings": [{"type": "publishing_job", "item": result["publishing_job"]}], "recommendations": [{"type": "action", "detail": "Configure platform integration and obtain human approval before publishing."}]}
        schema = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}
        prompt = (
            f"{self._build_system_prompt(task, context)}\n"
            "Prepare/validate/schedule recommendation only. NEVER claim content was published. "
            "If asked to publish, return a pending approval job unless all governance/integration conditions are explicitly satisfied in input.\n"
            f"OBJECTIVE: {task.objective}\nINPUT: {task.input_data}\n"
            f"DETERMINISTIC: integration_configured={integration}, credentials_present={credentials}, content_state={content_state}, human_approval={context.has_human_approval}, can_request_actual_publish={can_request_actual_publish}\n"
            "Return JSON: summary, status_detail, publishing_job{}, validation{}, schedule_recommendation{}, confidence, risks[], evidence[]."
        )
        data = self._llm_json(task, context, prompt, schema, retries=1)
        data["status_detail"] = data.get("status_detail") or ("ready_for_approval" if not can_request_actual_publish else "approved_for_execution_path_not_implemented")
        # Safety override: never report published.
        if str(data.get("status_detail", "")).lower() in {"published", "success_published"}:
            data["status_detail"] = "blocked_requires_verified_integration"
        return {
            "summary": data.get("summary", "Publishing job prepared"),
            "findings": [{"type": "publishing_job", "item": data.get("publishing_job", {})}, {"type": "validation", "item": data.get("validation", {})}],
            "recommendations": [data.get("schedule_recommendation", {})] if data.get("schedule_recommendation") else [],
            "evidence": data.get("evidence", [{"type": "system", "detail": "No live publishing API call made."}]),
            "confidence": float(data.get("confidence") or 0.8),
            "risks": data.get("risks", []),
            "requires_human_approval": True,
            "output": data,
        }
