from __future__ import annotations

import datetime
import uuid
from typing import Any

from pydantic import BaseModel, Field


class ScheduledPost(BaseModel):
    id: str
    business_id: str
    channel: str
    content: str
    scheduled_time: str
    status: str = "pending"  # "pending", "published", "cancelled"
    campaign_id: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class AutomationRule(BaseModel):
    id: str
    business_id: str
    name: str
    trigger_type: str  # "review_alert", "keyword_spike", "budget_threshold"
    condition: dict[str, Any]
    target_agent_id: str
    is_active: bool = True


class MarketingScheduler:
    def __init__(self) -> None:
        self._scheduled_posts: dict[str, list[ScheduledPost]] = {}
        self._automation_rules: dict[str, list[AutomationRule]] = {}

    def schedule_post(
        self,
        business_id: str,
        channel: str,
        content: str,
        scheduled_time: datetime.datetime,
        campaign_id: str | None = None,
    ) -> ScheduledPost:
        post = ScheduledPost(
            id=f"sched_{uuid.uuid4().hex[:10]}",
            business_id=business_id,
            channel=channel,
            content=content,
            scheduled_time=scheduled_time.isoformat(),
            status="pending",
            campaign_id=campaign_id,
        )
        if business_id not in self._scheduled_posts:
            self._scheduled_posts[business_id] = []
        self._scheduled_posts[business_id].append(post)
        return post

    def list_calendar(self, business_id: str) -> list[ScheduledPost]:
        return self._scheduled_posts.get(business_id, [])

    def add_automation_rule(
        self,
        business_id: str,
        name: str,
        trigger_type: str,
        condition: dict[str, Any],
        target_agent_id: str,
    ) -> AutomationRule:
        rule = AutomationRule(
            id=f"rule_{uuid.uuid4().hex[:10]}",
            business_id=business_id,
            name=name,
            trigger_type=trigger_type,
            condition=condition,
            target_agent_id=target_agent_id,
            is_active=True,
        )
        if business_id not in self._automation_rules:
            self._automation_rules[business_id] = []
        self._automation_rules[business_id].append(rule)
        return rule

    def evaluate_triggers(self, business_id: str, event_type: str, event_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Evaluate events against active rules and return triggered agent tasks."""
        triggered_actions: list[dict[str, Any]] = []
        rules = self._automation_rules.get(business_id, [])

        for rule in rules:
            if not rule.is_active or rule.trigger_type != event_type:
                continue

            if event_type == "review_alert":
                rating = event_data.get("rating", 5)
                max_rating = rule.condition.get("max_rating", 2)
                if rating <= max_rating:
                    triggered_actions.append(
                        {
                            "rule_id": rule.id,
                            "target_agent": rule.target_agent_id,
                            "action": "draft_reputation_escalation_reply",
                            "data": event_data,
                        }
                    )
            elif event_type == "keyword_spike":
                growth_pct = event_data.get("growth_pct", 0)
                min_growth = rule.condition.get("min_growth_pct", 20)
                if growth_pct >= min_growth:
                    triggered_actions.append(
                        {
                            "rule_id": rule.id,
                            "target_agent": rule.target_agent_id,
                            "action": "generate_reactive_content_brief",
                            "data": event_data,
                        }
                    )
            elif event_type == "budget_threshold":
                spend_pct = event_data.get("spend_pct", 0)
                limit_pct = rule.condition.get("limit_pct", 80)
                if spend_pct >= limit_pct:
                    triggered_actions.append(
                        {
                            "rule_id": rule.id,
                            "target_agent": rule.target_agent_id,
                            "action": "notify_budget_warning",
                            "data": event_data,
                        }
                    )

        return triggered_actions
