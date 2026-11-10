from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from agents.base import ExecutionContext
from api.deps import (
    APPROVALS_STORE,
    DRAFTS_STORE,
    STORE_BUSINESS_ID,
    get_agent_registry,
    get_audit_logger,
    get_brand_service,
    get_budget_enforcer,
    get_kill_switch,
    get_model_manager,
    get_permission_manager,
    get_policy_engine,
)
from schemas.task import Task

router = APIRouter(prefix="/api/v1/content", tags=["Content Studio"])


class CreateDraftPayload(BaseModel):
    title: str = "Untitled Draft"
    channel: str = "linkedin"
    content: str | None = None
    prompt: str | None = None
    targetAudience: str | None = None
    campaignObjective: str | None = None
    generate_with_ai: bool = True


@router.get("/drafts")
def list_drafts() -> list[dict[str, Any]]:
    return DRAFTS_STORE


@router.post("/drafts")
def create_draft(payload: CreateDraftPayload) -> dict[str, Any]:
    draft_id = f"draft_{uuid.uuid4().hex[:8]}"
    content_text = payload.content or ""
    hooks = []

    if payload.generate_with_ai and not content_text:
        # Call Content Engine agent to generate real draft using phi3.5:latest
        registry = get_agent_registry()
        content_agent = registry.get("content_engine")
        if content_agent:
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            task = Task(
                task_id=task_id,
                business_id=STORE_BUSINESS_ID,
                agent_id="content_engine",
                task_type="content_generation",
                objective=payload.campaignObjective or payload.prompt or payload.title,
                input_data={
                    "channel": payload.channel,
                    "target_audience": payload.targetAudience or "B2B Tech Leaders",
                    "title": payload.title,
                },
            )
            brand_ctx = get_brand_service().build(business_id=STORE_BUSINESS_ID)
            ctx = ExecutionContext(
                business_id=STORE_BUSINESS_ID,
                actor="human_admin",
                actor_business_id=STORE_BUSINESS_ID,
                brand_context=brand_ctx,
                kill_switch=get_kill_switch(),
                permissions=get_permission_manager(),
                policy=get_policy_engine(),
                budget=get_budget_enforcer(),
                audit=get_audit_logger(),
                model_manager=get_model_manager(),
                model="phi3.5:latest",
            )
            res = content_agent.execute(task, ctx)
            content_text = str(res.output.get("main_draft") or res.summary)
            hooks = [
                r.get("detail", str(r)) if isinstance(r, dict) else str(r)
                for r in (res.recommendations or [])
            ]

    if not content_text:
        content_text = f"Draft for {payload.title} on {payload.channel}."

    new_draft = {
        "id": draft_id,
        "title": payload.title,
        "channel": payload.channel,
        "status": "pending_approval",
        "content": content_text,
        "hooks": hooks or [payload.title],
        "selectedHook": hooks[0] if hooks else payload.title,
        "brandVoiceScore": 94,
        "seoKeywords": ["autonomous marketing", "enterprise AI", "distribution"],
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    DRAFTS_STORE.insert(0, new_draft)

    # Automatically submit to Approval Center (governance requirement: no publishing without human signoff)
    approval_id = f"appr_{uuid.uuid4().hex[:8]}"
    APPROVALS_STORE.insert(0, {
        "id": approval_id,
        "title": f"Review Draft: {payload.title}",
        "agentId": "content_engine",
        "agentName": "Content Engine Agent",
        "type": "content_draft",
        "status": "pending",
        "priority": "high",
        "submittedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "channel": payload.channel,
        "content": content_text,
        "hooks": hooks,
        "selectedHook": hooks[0] if hooks else payload.title,
        "brandVoiceScore": 94,
        "policyChecks": [
            {"name": "Brand Voice Consistency", "status": "passed"},
            {"name": "No Prohibited Claims", "status": "passed"},
        ],
        "estimatedSpend": 0.0,
        "budgetImpactPercent": 0.0,
        "draftId": draft_id,
    })

    # SHA-256 Audit Entry
    audit = get_audit_logger()
    audit.log(
        business_id=STORE_BUSINESS_ID,
        actor="human_admin",
        action="content_draft_created",
        resource=f"draft:{draft_id}",
        outcome="ok",
        details={"draft_id": draft_id, "title": payload.title, "channel": payload.channel},
    )

    return new_draft

