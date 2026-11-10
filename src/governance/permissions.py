from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


class PermissionDeniedError(PermissionError):
    """Raised when an agent action is not permitted by governance."""


class Action(StrEnum):
    READ_BUSINESS_DATA = "read_business_data"
    WRITE_DRAFT = "write_draft"
    REQUEST_APPROVAL = "request_approval"
    REQUEST_PUBLISH = "request_publish"
    PUBLISH = "publish"  # only via explicitly authorized, approved execution path
    SCHEDULE = "schedule"
    READ_ANALYTICS = "read_analytics"
    READ_REVIEWS = "read_reviews"
    DRAFT_REVIEW_RESPONSE = "draft_review_response"
    READ_LEADS = "read_leads"
    DRAFT_LEAD_RESPONSE = "draft_lead_response"
    MANAGE_BUDGET = "manage_budget"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_AUDIT = "view_audit"


# Default-deny: only explicitly granted actions are allowed.
# Publishing is never granted to agents by default; orchestration must pass human-approved flow.
AGENT_PERMISSIONS: dict[str, set[Action]] = {
    "search_visibility": {
        Action.READ_BUSINESS_DATA,
        Action.READ_ANALYTICS,
        Action.WRITE_DRAFT,
        Action.REQUEST_APPROVAL,
    },
    "market_radar": {
        Action.READ_BUSINESS_DATA,
        Action.READ_ANALYTICS,
        Action.WRITE_DRAFT,
        Action.REQUEST_APPROVAL,
    },
    "content_engine": {
        Action.READ_BUSINESS_DATA,
        Action.WRITE_DRAFT,
        Action.REQUEST_APPROVAL,
        Action.REQUEST_PUBLISH,
    },
    "creative_studio": {
        Action.READ_BUSINESS_DATA,
        Action.WRITE_DRAFT,
        Action.REQUEST_APPROVAL,
    },
    "publishing_social": {
        Action.READ_BUSINESS_DATA,
        Action.WRITE_DRAFT,
        Action.REQUEST_APPROVAL,
        Action.REQUEST_PUBLISH,
        Action.SCHEDULE,  # prepares/schedules only after approval checks elsewhere
    },
    "reviews_reputation": {
        Action.READ_BUSINESS_DATA,
        Action.READ_REVIEWS,
        Action.DRAFT_REVIEW_RESPONSE,
        Action.REQUEST_APPROVAL,
    },
    "leads_conversations": {
        Action.READ_BUSINESS_DATA,
        Action.READ_LEADS,
        Action.DRAFT_LEAD_RESPONSE,
        Action.REQUEST_APPROVAL,
    },
    "results_roi": {
        Action.READ_BUSINESS_DATA,
        Action.READ_ANALYTICS,
        Action.WRITE_DRAFT,
        Action.REQUEST_APPROVAL,
        Action.VIEW_AUDIT,
    },
    "orchestrator": {
        Action.READ_BUSINESS_DATA,
        Action.READ_ANALYTICS,
        Action.READ_REVIEWS,
        Action.READ_LEADS,
        Action.WRITE_DRAFT,
        Action.REQUEST_APPROVAL,
        Action.REQUEST_PUBLISH,
        Action.SCHEDULE,
        Action.VIEW_AUDIT,
    },
    # Human/system roles may be represented separately in API auth; keep explicit.
    "human_admin": set(Action),
}


@dataclass(frozen=True)
class PermissionContext:
    business_id: str
    actor: str
    actor_business_id: str | None = None  # if set, must match business_id


class PermissionManager:
    """Backend permission enforcement. Prompts are not a security boundary."""

    def __init__(self, permissions: dict[str, set[Action]] | None = None):
        self.permissions = permissions or AGENT_PERMISSIONS

    def allowed_actions(self, actor: str) -> set[Action]:
        return set(self.permissions.get(actor, set()))

    def is_allowed(self, actor: str, action: Action | str) -> bool:
        try:
            action_enum = Action(action)
        except ValueError:
            return False
        return action_enum in self.allowed_actions(actor)

    def require(self, ctx: PermissionContext, action: Action | str) -> None:
        # Business isolation: if an actor is bound to a business, they cannot act on another.
        if ctx.actor_business_id is not None and ctx.actor_business_id != ctx.business_id:
            raise PermissionDeniedError(
                f"Business isolation violation: actor bound to {ctx.actor_business_id} "
                f"cannot access {ctx.business_id}"
            )
        if not self.is_allowed(ctx.actor, action):
            raise PermissionDeniedError(
                f"Permission denied: actor={ctx.actor} action={action} business={ctx.business_id}"
            )

    def grant(self, actor: str, actions: Iterable[Action | str]) -> None:
        current = self.permissions.setdefault(actor, set())
        for action in actions:
            current.add(Action(action))

    def revoke(self, actor: str, actions: Iterable[Action | str]) -> None:
        current = self.permissions.setdefault(actor, set())
        for action in actions:
            current.discard(Action(action))
