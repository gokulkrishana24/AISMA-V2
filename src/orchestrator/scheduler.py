from __future__ import annotations

from typing import Any

from schemas.task import utc_now_iso


class Scheduler:
    """Phase 3 scheduler: deterministic ordering metadata; no autonomous browser/OS loop."""

    def schedule(self, plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "scheduled_at": utc_now_iso(),
            "strategy": plan.get("strategy"),
            "batch_count": len(plan.get("batches") or []),
            "ordered_task_ids": plan.get("ordered_task_ids") or [],
        }
