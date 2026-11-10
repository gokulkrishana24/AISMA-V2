from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.deps import get_kill_switch, require_tenant_access
from automation.scheduler import MarketingScheduler

router = APIRouter(prefix="/api/v1/scheduler", tags=["Marketing Calendar & Event Automation"])

_scheduler = MarketingScheduler()


def get_scheduler() -> MarketingScheduler:
    return _scheduler


class SchedulePostPayload(BaseModel):
    channel: str
    content: str
    scheduled_time: datetime.datetime
    campaign_id: str | None = None


class AutomationRulePayload(BaseModel):
    name: str
    trigger_type: str  # "review_alert", "keyword_spike", "budget_threshold"
    condition: dict[str, Any]
    target_agent_id: str


class EvaluateTriggerPayload(BaseModel):
    event_type: str
    event_data: dict[str, Any]


@router.get("/calendar")
def get_calendar_posts(
    business_id: str = Depends(require_tenant_access),
    sched: MarketingScheduler = Depends(get_scheduler),
) -> list[dict[str, Any]]:
    posts = sched.list_calendar(business_id)
    return [p.model_dump() for p in posts]


@router.post("/posts")
def schedule_post(
    payload: SchedulePostPayload,
    business_id: str = Depends(require_tenant_access),
    sched: MarketingScheduler = Depends(get_scheduler),
) -> dict[str, Any]:
    ks = get_kill_switch()
    if ks.is_engaged(business_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kill switch is engaged. Scheduling new posts is blocked.",
        )

    # Prevent exact duplicate scheduling on same channel + time
    existing = sched.list_calendar(business_id)
    target_iso = payload.scheduled_time.isoformat()
    for p in existing:
        if p.channel == payload.channel and p.scheduled_time == target_iso and p.content == payload.content:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate post detected at identical channel and scheduled timestamp.",
            )

    post = sched.schedule_post(
        business_id=business_id,
        channel=payload.channel,
        content=payload.content,
        scheduled_time=payload.scheduled_time,
        campaign_id=payload.campaign_id,
    )
    return post.model_dump()


@router.post("/rules")
def create_automation_rule(
    payload: AutomationRulePayload,
    business_id: str = Depends(require_tenant_access),
    sched: MarketingScheduler = Depends(get_scheduler),
) -> dict[str, Any]:
    rule = sched.add_automation_rule(
        business_id=business_id,
        name=payload.name,
        trigger_type=payload.trigger_type,
        condition=payload.condition,
        target_agent_id=payload.target_agent_id,
    )
    return rule.model_dump()


@router.post("/evaluate")
def evaluate_automation_triggers(
    payload: EvaluateTriggerPayload,
    business_id: str = Depends(require_tenant_access),
    sched: MarketingScheduler = Depends(get_scheduler),
) -> dict[str, Any]:
    actions = sched.evaluate_triggers(business_id, payload.event_type, payload.event_data)
    return {
        "business_id": business_id,
        "event_type": payload.event_type,
        "triggered_count": len(actions),
        "actions": actions,
    }

