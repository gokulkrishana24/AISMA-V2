from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .task import utc_now_iso


class ExecutionBrief(BaseModel):
    brief_id: str
    business_id: str
    objective: str
    strategy: str
    summary: str
    planned_tasks: list[dict[str, Any]] = Field(default_factory=list)
    completed_task_ids: list[str] = Field(default_factory=list)
    failed_task_ids: list[str] = Field(default_factory=list)
    blocked_task_ids: list[str] = Field(default_factory=list)
    pending_approval_task_ids: list[str] = Field(default_factory=list)
    key_findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    risks: list[dict[str, Any]] = Field(default_factory=list)
    audit_event_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
