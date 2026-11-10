from __future__ import annotations

from typing import Any

from schemas.task import Task

from .base import BaseAgent, ExecutionContext

INTENTS = {"high_intent", "support", "pricing_inquiry", "general_inquiry", "complaint", "spam", "unknown"}


class LeadsConversationsAgent(BaseAgent):
    agent_id = "leads_conversations"
    agent_name = "Leads & Conversations Agent"
    description = "Lead classification, intent detection, and follow-up drafting with deterministic escalation."
    capabilities = ["lead_classification", "intent_detection", "conversation_summary", "follow_up_recommendations"]
    supported_task_types = ["lead_classification", "conversation_summary", "follow_up_draft"]
    required_permissions = ["read_business_data", "read_leads", "draft_lead_response"]

    def validate_task(self, task: Task, context: ExecutionContext) -> None:
        if task.task_type not in self.supported_task_types:
            raise ValueError(f"Unsupported task_type: {task.task_type}")
        if task.business_id != context.business_id:
            raise PermissionError("Business isolation violation")

    @staticmethod
    def _deterministic_escalation(intent: str, score: float, text: str) -> bool:
        t = (text or "").lower()
        if intent == "complaint":
            return True
        if intent == "high_intent" or score >= 0.75:
            return True
        if any(w in t for w in ["buy", "purchase", "quote", "demo", "pricing", "contract", "urgent"]):
            return score >= 0.5
        return False

    def _execute_impl(self, task: Task, context: ExecutionContext) -> dict[str, Any]:
        schema = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}
        prompt = (
            f"{self._build_system_prompt(task, context)}\n"
            "Classify lead intent and draft suggested replies. Never invent pricing, availability, delivery timelines, or contractual commitments. "
            f"Allowed intents: {sorted(INTENTS)}.\n"
            f"OBJECTIVE: {task.objective}\nINPUT: {task.input_data}\n"
            "Return JSON: summary, intent, intent_score (0-1), category, lead_priority, conversation_summary, suggested_reply, follow_up_recommendations[], escalation_required, confidence, risks[], evidence[]."
        )
        data = self._llm_json(task, context, prompt, schema, retries=1)
        intent = str(data.get("intent") or "unknown")
        if intent not in INTENTS:
            intent = "unknown"
            data["intent"] = intent
        score = float(data.get("intent_score") or 0.0)
        text = str(task.input_data.get("message") or task.input_data.get("text") or "")
        escalate = self._deterministic_escalation(intent, score, text) or bool(data.get("escalation_required"))
        data["escalation_required"] = escalate
        return {
            "summary": data.get("summary", "Lead/conversation processed"),
            "findings": [{"type": "intent", "item": {"intent": intent, "score": score, "category": data.get("category", "unknown")}}],
            "recommendations": data.get("follow_up_recommendations", []) + ([{"type": "suggested_reply", "text": data.get("suggested_reply", "")}] if data.get("suggested_reply") else []),
            "evidence": data.get("evidence", []),
            "confidence": float(data.get("confidence") or 0.6),
            "risks": data.get("risks", []) + [{"type": "commitments", "detail": "No pricing/availability/delivery/contract commitments invented."}],
            "requires_human_approval": escalate and intent in {"complaint", "high_intent", "pricing_inquiry"},
            "output": data,
        }
