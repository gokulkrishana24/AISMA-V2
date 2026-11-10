from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import yaml

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)

ALLOWED_STATUSES = {
    "draft",
    "pending_approval",
    "approved",
    "scheduled",
    "published",
    "rejected",
    "archived",
}

# Legal transitions: current -> allowed next statuses.
LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"pending_approval", "archived", "rejected"},
    "pending_approval": {"approved", "rejected", "draft"},
    "approved": {"scheduled", "published", "rejected", "archived"},
    "scheduled": {"published", "rejected", "archived", "draft"},
    "published": {"archived"},
    "rejected": {"draft", "archived"},
    "archived": {"draft"},
}

REQUIRED_FIELDS = {"id", "business_id", "agent", "content_type", "status", "created_at"}


class FrontmatterError(ValueError):
    """Raised when frontmatter is missing, invalid, or violates governance rules."""


@dataclass(frozen=True)
class ParsedArtifact:
    frontmatter: dict[str, Any]
    body: str
    raw_frontmatter: str


def parse_frontmatter(text: str) -> ParsedArtifact:
    if not isinstance(text, str) or not text:
        raise FrontmatterError("Artifact text is required")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise FrontmatterError("Missing or invalid YAML frontmatter block")
    raw = match.group(1)
    body = match.group(2)
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"Invalid YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise FrontmatterError("Frontmatter must be a YAML mapping")
    return ParsedArtifact(frontmatter=data, body=body, raw_frontmatter=raw)


def validate_frontmatter(data: dict[str, Any]) -> None:
    missing = [k for k in sorted(REQUIRED_FIELDS) if not data.get(k)]
    if missing:
        raise FrontmatterError(f"Missing required frontmatter fields: {', '.join(missing)}")
    status = str(data.get("status", "")).strip()
    if status not in ALLOWED_STATUSES:
        raise FrontmatterError(f"Invalid status '{status}'")
    # Approval-required statuses should carry approval metadata when approved/scheduled/published.
    if status in {"approved", "scheduled", "published"} and not data.get("approved_by"):
        raise FrontmatterError(f"Status '{status}' requires 'approved_by'")
    if status == "scheduled" and not data.get("scheduled_for"):
        raise FrontmatterError("Status 'scheduled' requires 'scheduled_for'")


def assert_legal_transition(current_status: str, next_status: str) -> None:
    current = str(current_status or "").strip()
    nxt = str(next_status or "").strip()
    if current not in ALLOWED_STATUSES:
        raise FrontmatterError(f"Unknown current status '{current}'")
    if nxt not in ALLOWED_STATUSES:
        raise FrontmatterError(f"Unknown next status '{nxt}'")
    allowed = LEGAL_TRANSITIONS.get(current, set())
    if nxt not in allowed:
        raise FrontmatterError(f"Illegal status transition: {current} -> {nxt}")


def apply_transition(
    data: dict[str, Any],
    next_status: str,
    *,
    approved_by: str | None = None,
    scheduled_for: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    current = str(data.get("status", ""))
    assert_legal_transition(current, next_status)
    updated = dict(data)
    updated["status"] = next_status
    if reason:
        updated["status_reason"] = reason
    if next_status in {"approved", "scheduled", "published"}:
        if not approved_by and not updated.get("approved_by"):
            raise FrontmatterError(f"Transition to '{next_status}' requires approved_by")
        if approved_by:
            updated["approved_by"] = approved_by
    if next_status == "scheduled":
        if not scheduled_for and not updated.get("scheduled_for"):
            raise FrontmatterError("Transition to 'scheduled' requires scheduled_for")
        if scheduled_for:
            updated["scheduled_for"] = scheduled_for
    if next_status == "rejected":
        updated.pop("approved_by", None)
        updated.pop("scheduled_for", None)
    validate_frontmatter(updated)
    return updated
