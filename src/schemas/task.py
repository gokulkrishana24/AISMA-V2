from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    QUEUED = "queued"
    VALIDATED = "validated"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    PENDING_APPROVAL = "pending_approval"
    CANCELLED = "cancelled"


# Deterministic, validated transitions.
LEGAL_TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.QUEUED: {TaskStatus.VALIDATED, TaskStatus.BLOCKED, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.VALIDATED: {TaskStatus.RUNNING, TaskStatus.BLOCKED, TaskStatus.CANCELLED, TaskStatus.FAILED, TaskStatus.PENDING_APPROVAL},
    TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.PARTIALLY_COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.PENDING_APPROVAL},
    TaskStatus.PENDING_APPROVAL: {TaskStatus.VALIDATED, TaskStatus.RUNNING, TaskStatus.CANCELLED, TaskStatus.BLOCKED},
    TaskStatus.BLOCKED: {TaskStatus.QUEUED, TaskStatus.VALIDATED, TaskStatus.CANCELLED},
    TaskStatus.FAILED: {TaskStatus.QUEUED, TaskStatus.CANCELLED},
    TaskStatus.PARTIALLY_COMPLETED: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.PENDING_APPROVAL},
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Task(BaseModel):
    task_id: str
    business_id: str
    agent_id: str
    task_type: str
    objective: str
    priority: int = Field(default=5, ge=1, le=10)
    dependencies: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.QUEUED
    input_data: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    idempotency_key: str | None = None
    approval_required: bool = False
    retries: int = 0
    max_retries: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"use_enum_values": False, "extra": "forbid"}

    def transition_to(self, next_status: TaskStatus, reason: str = "") -> Task:
        current = self.status if isinstance(self.status, TaskStatus) else TaskStatus(str(self.status))
        allowed = LEGAL_TASK_TRANSITIONS.get(current, set())
        if next_status not in allowed:
            raise ValueError(f"Illegal task transition: {current.value} -> {next_status.value}")
        data = self.model_dump()
        data["status"] = next_status
        if reason:
            meta = dict(data.get("metadata") or {})
            meta.setdefault("status_history", []).append(
                {"from": current.value, "to": next_status.value, "reason": reason, "at": utc_now_iso()}
            )
            data["metadata"] = meta
        return Task.model_validate(data)
