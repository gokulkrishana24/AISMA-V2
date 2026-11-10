from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .frontmatter import ALLOWED_STATUSES, assert_legal_transition


class PolicyViolationError(PermissionError):
    """Raised when an action violates governance policy."""


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    action: str
    reason: str
    requires_human_approval: bool = False
    constraints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "reason": self.reason,
            "requires_human_approval": self.requires_human_approval,
            "constraints": self.constraints,
        }


# Actions that must never execute without explicit human approval.
HUMAN_APPROVAL_ACTIONS = {
    "publish",
    "schedule_publish",
    "send_external_message",
    "respond_negative_review",
    "respond_complaint",
    "modify_budget",
    "change_permissions",
    "disable_killswitch",
}


class PolicyEngine:
    """Backend policy enforcement. Fail-closed for sensitive actions."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.default_deny_publishing = bool(self.config.get("default_deny_publishing", True))

    def evaluate(
        self,
        action: str,
        *,
        actor: str,
        business_id: str,
        resource: dict[str, Any] | None = None,
        has_human_approval: bool = False,
        kill_switch_engaged: bool = False,
        injection_scan_passed: bool = True,
        lint_passed: bool = True,
    ) -> PolicyDecision:
        resource = resource or {}
        if kill_switch_engaged:
            return PolicyDecision(False, action, "Kill switch is engaged", False)
        if not injection_scan_passed:
            return PolicyDecision(False, action, "Untrusted input failed injection scan", False)

        # Publishing is default-deny.
        if action in {"publish", "schedule_publish"}:
            if self.default_deny_publishing and not has_human_approval:
                return PolicyDecision(
                    False,
                    action,
                    "Default-deny publishing: explicit human approval required",
                    True,
                    {"required": "human_approval"},
                )
            if not lint_passed:
                return PolicyDecision(False, action, "Content failed governance lint checks", False)
            status = str(resource.get("status", ""))
            if status and status not in ALLOWED_STATUSES:
                return PolicyDecision(False, action, f"Invalid content status '{status}'", False)
            if action == "publish" and status not in {"approved", "scheduled"} and not has_human_approval:
                return PolicyDecision(
                    False, action, "Publish requires approved/scheduled state and approval", True
                )
            if action == "schedule_publish" and status not in {"approved", "draft", "pending_approval"}:
                # allow transition path but still require approval for execution
                pass
            if has_human_approval and lint_passed:
                return PolicyDecision(True, action, "Allowed with human approval", False)
            return PolicyDecision(False, action, "Publishing requires approval and passing checks", True)

        # Negative review/complaint responses always require approval.
        if action in {"respond_negative_review", "respond_complaint"} or (
            action == "send_external_message" and resource.get("sentiment") in {"negative", "very_negative"}
        ):
            if not has_human_approval:
                return PolicyDecision(
                    False,
                    action,
                    "Negative review/complaint responses require human approval",
                    True,
                )
            if not lint_passed:
                return PolicyDecision(False, action, "Response failed governance lint checks", False)
            return PolicyDecision(True, action, "Allowed with human approval", False)

        if action in HUMAN_APPROVAL_ACTIONS and not has_human_approval:
            return PolicyDecision(
                False, action, f"Action '{action}' requires human approval", True
            )

        if not lint_passed and action in {"generate_content", "draft_response", "send_external_message"}:
            return PolicyDecision(False, action, "Output failed governance lint checks", False)

        # Default allow for low-risk internal actions only when explicitly modeled; fail closed otherwise.
        low_risk = {
            "read_data",
            "analyze",
            "generate_draft",
            "score_opportunity",
            "queue_for_approval",
        }
        if action in low_risk:
            return PolicyDecision(True, action, "Low-risk action allowed by policy", False)

        return PolicyDecision(
            False,
            action,
            f"Fail-closed: action '{action}' is not explicitly allowed",
            False,
        )

    def require(self, *args: Any, **kwargs: Any) -> PolicyDecision:
        decision = self.evaluate(*args, **kwargs)
        if not decision.allowed:
            raise PolicyViolationError(decision.reason)
        return decision

    def validate_status_transition(self, current_status: str, next_status: str) -> None:
        assert_legal_transition(current_status, next_status)
