from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class BudgetExceededError(PermissionError):
    """Raised when an action would exceed an enforced budget."""


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class BudgetLimits:
    max_tokens_per_day: int = 0  # 0 means unlimited in config? no: fail-safe -> treat 0 as unset invalid in strict mode
    max_actions_per_day: int = 0
    max_cost_units_per_day: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, strict: bool = True) -> BudgetLimits:
        limits = cls(
            max_tokens_per_day=int(data.get("max_tokens_per_day", 0)),
            max_actions_per_day=int(data.get("max_actions_per_day", 0)),
            max_cost_units_per_day=float(data.get("max_cost_units_per_day", 0.0)),
        )
        if strict and (
            limits.max_tokens_per_day <= 0
            or limits.max_actions_per_day <= 0
            or limits.max_cost_units_per_day <= 0
        ):
            raise ValueError("Budget limits must be positive in strict/fail-closed mode")
        return limits


class BudgetEnforcer:
    """Tracks and enforces per-business daily budgets.

    Storage is file-based for Phase 1; Phase 5 can move to PostgreSQL.
    """

    def __init__(self, state_dir: str | Path, *, strict: bool = True):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.strict = strict

    def _safe_business(self, business_id: str) -> str:
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in business_id)
        if not safe:
            raise ValueError("business_id is required")
        return safe

    def _config_path(self, business_id: str) -> Path:
        return self.state_dir / f"{self._safe_business(business_id)}.budget.json"

    def _usage_path(self, business_id: str) -> Path:
        day = datetime.now(UTC).strftime("%Y-%m-%d")
        return self.state_dir / f"{self._safe_business(business_id)}.usage.{day}.json"

    def set_limits(self, business_id: str, limits: BudgetLimits | dict[str, Any]) -> None:
        if isinstance(limits, dict):
            limits = BudgetLimits.from_dict(limits, strict=self.strict)
        path = self._config_path(business_id)
        path.write_text(
            json.dumps(
                {
                    "business_id": business_id,
                    "max_tokens_per_day": limits.max_tokens_per_day,
                    "max_actions_per_day": limits.max_actions_per_day,
                    "max_cost_units_per_day": limits.max_cost_units_per_day,
                    "updated_at": _utc_now_iso(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def get_limits(self, business_id: str) -> BudgetLimits:
        path = self._config_path(business_id)
        if not path.exists():
            if self.strict:
                raise ValueError(f"Missing budget config for business '{business_id}'")
            return BudgetLimits(10**9, 10**9, 10**9)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            if self.strict:
                raise ValueError(f"Invalid budget config for '{business_id}'") from exc
            return BudgetLimits(10**9, 10**9, 10**9)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid budget config for '{business_id}'")
        return BudgetLimits.from_dict(data, strict=self.strict)

    def get_usage(self, business_id: str) -> dict[str, Any]:
        path = self._usage_path(business_id)
        if not path.exists():
            return {
                "business_id": business_id,
                "date": datetime.now(UTC).strftime("%Y-%m-%d"),
                "tokens_used": 0,
                "actions_used": 0,
                "cost_units_used": 0.0,
            }
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception as exc:
            if self.strict:
                raise ValueError(f"Corrupt budget usage state for '{business_id}'") from exc
        if self.strict:
            raise ValueError(f"Invalid budget usage state for '{business_id}'")
        return {"tokens_used": 0, "actions_used": 0, "cost_units_used": 0.0}

    def _save_usage(self, business_id: str, usage: dict[str, Any]) -> None:
        path = self._usage_path(business_id)
        usage["updated_at"] = _utc_now_iso()
        path.write_text(json.dumps(usage, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def check_and_reserve(
        self,
        business_id: str,
        *,
        tokens: int = 0,
        actions: int = 1,
        cost_units: float = 0.0,
        actor: str = "system",
    ) -> dict[str, Any]:
        limits = self.get_limits(business_id)
        usage = self.get_usage(business_id)
        next_tokens = int(usage.get("tokens_used", 0)) + max(0, int(tokens))
        next_actions = int(usage.get("actions_used", 0)) + max(0, int(actions))
        next_cost = float(usage.get("cost_units_used", 0.0)) + max(0.0, float(cost_units))

        violations: list[str] = []
        if next_tokens > limits.max_tokens_per_day:
            violations.append("max_tokens_per_day")
        if next_actions > limits.max_actions_per_day:
            violations.append("max_actions_per_day")
        if next_cost > limits.max_cost_units_per_day:
            violations.append("max_cost_units_per_day")
        if violations:
            raise BudgetExceededError(
                f"Budget exceeded for {business_id} ({', '.join(violations)}) by actor={actor}"
            )

        usage["tokens_used"] = next_tokens
        usage["actions_used"] = next_actions
        usage["cost_units_used"] = next_cost
        usage["last_actor"] = actor
        self._save_usage(business_id, usage)
        return usage
