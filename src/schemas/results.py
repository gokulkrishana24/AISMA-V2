from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .brief import ExecutionBrief
from .task import utc_now_iso


class OrchestrationReport(BaseModel):
    report_id: str
    business_id: str
    objective: str
    status: str
    strategy: str
    task_count: int
    results: list[dict[str, Any]] = Field(default_factory=list)
    brief: ExecutionBrief | None = None
    errors: list[str] = Field(default_factory=list)
    audit_event_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = Field(default_factory=dict)
