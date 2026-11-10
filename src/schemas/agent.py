from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AgentRunStatus(StrEnum):
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    PENDING_APPROVAL = "pending_approval"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AgentResult(BaseModel):
    task_id: str
    agent_id: str
    status: AgentRunStatus
    summary: str
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    risks: list[dict[str, Any]] = Field(default_factory=list)
    requires_human_approval: bool = False
    created_at: str = Field(default_factory=utc_now_iso)
    execution_duration: float = 0.0
    model_used: str | None = None
    errors: list[str] = Field(default_factory=list)
    output: dict[str, Any] = Field(default_factory=dict)

    model_config = {"use_enum_values": False}


class AgentCapability(BaseModel):
    name: str
    description: str = ""
    task_types: list[str] = Field(default_factory=list)
