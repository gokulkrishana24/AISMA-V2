from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from schemas.task import Task


def topological_batches(tasks: list[Task]) -> list[list[Task]]:
    by_id = {t.task_id: t for t in tasks}
    indeg: dict[str, int] = {t.task_id: 0 for t in tasks}
    children: dict[str, list[str]] = defaultdict(list)
    for t in tasks:
        for dep in t.dependencies:
            if dep in by_id:
                indeg[t.task_id] += 1
                children[dep].append(t.task_id)
    # stable order
    ready = deque(sorted([tid for tid, d in indeg.items() if d == 0], key=lambda tid: (-by_id[tid].priority, tid)))
    batches: list[list[Task]] = []
    seen = 0
    while ready:
        batch_ids = list(ready)
        ready.clear()
        batch = [by_id[tid] for tid in sorted(batch_ids, key=lambda tid: (-by_id[tid].priority, tid))]
        batches.append(batch)
        for tid in batch_ids:
            seen += 1
            for ch in children.get(tid, []):
                indeg[ch] -= 1
                if indeg[ch] == 0:
                    ready.append(ch)
        if ready:
            # keep deterministic
            ready = deque(sorted(list(ready), key=lambda tid: (-by_id[tid].priority, tid)))
    if seen != len(tasks):
        # cycle fallback: append remaining in priority order
        remaining = [t for t in tasks if t.task_id not in {x.task_id for b in batches for x in b}]
        if remaining:
            batches.append(sorted(remaining, key=lambda t: (-t.priority, t.task_id)))
    return batches


class TaskPlanner:
    def plan(self, tasks: list[Task], strategy: str = "dependency_based") -> dict[str, Any]:
        strategy = strategy or "dependency_based"
        if strategy == "sequential":
            ordered = sorted(tasks, key=lambda t: (-t.priority, t.task_id))
            return {"strategy": strategy, "batches": [[t.model_dump() for t in ordered]], "ordered_task_ids": [t.task_id for t in ordered]}
        if strategy == "priority_based":
            ordered = sorted(tasks, key=lambda t: (-t.priority, t.task_id))
            return {"strategy": strategy, "batches": [[t.model_dump()] for t in ordered], "ordered_task_ids": [t.task_id for t in ordered]}
        # dependency_based default
        batches = topological_batches(tasks)
        ordered_ids = [t.task_id for b in batches for t in b]
        return {"strategy": "dependency_based", "batches": [[t.model_dump() for t in b] for b in batches], "ordered_task_ids": ordered_ids}
