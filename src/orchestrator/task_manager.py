from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from schemas.task import Task, TaskStatus, utc_now_iso


@dataclass
class TaskRecord:
    task: Task
    attempts: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    updated_at: str = field(default_factory=utc_now_iso)


class TaskManager:
    """In-memory task manager for Phase 3 orchestration.

    Deterministic transitions, idempotency-key deduplication, and retry tracking.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._idempotency: dict[str, str] = {}  # key -> task_id

    def add(self, task: Task) -> Task:
        if task.idempotency_key:
            existing_id = self._idempotency.get(task.idempotency_key)
            if existing_id and existing_id in self._tasks:
                return self._tasks[existing_id].task
            self._idempotency[task.idempotency_key] = task.task_id
        self._tasks[task.task_id] = TaskRecord(task=task)
        return task

    def get(self, task_id: str) -> Task | None:
        rec = self._tasks.get(task_id)
        return rec.task if rec else None

    def set_status(self, task_id: str, status: TaskStatus, reason: str = "") -> Task:
        rec = self._tasks[task_id]
        rec.task = rec.task.transition_to(status, reason=reason)
        rec.updated_at = utc_now_iso()
        return rec.task

    def mark_result(self, task_id: str, result: dict[str, Any], status: TaskStatus, error: str | None = None) -> Task:
        rec = self._tasks[task_id]
        rec.result = result
        rec.error = error
        rec.updated_at = utc_now_iso()
        if rec.task.status != status:
            try:
                rec.task = rec.task.transition_to(status, reason=error or "result")
            except ValueError:
                # allow terminal overwrite only in controlled cases? keep strict: set via model_copy
                rec.task = rec.task.model_copy(update={"status": status})
        return rec.task

    def can_retry(self, task_id: str) -> bool:
        rec = self._tasks[task_id]
        return rec.attempts < rec.task.max_retries and rec.task.status in {TaskStatus.FAILED, TaskStatus.BLOCKED}

    def increment_attempt(self, task_id: str) -> int:
        rec = self._tasks[task_id]
        rec.attempts += 1
        return rec.attempts

    def all(self) -> list[Task]:
        return [r.task for r in self._tasks.values()]
