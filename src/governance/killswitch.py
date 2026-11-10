from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class KillSwitchEngagedError(RuntimeError):
    """Raised when an operation is blocked by an engaged kill switch."""


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class KillSwitchState:
    engaged: bool
    scope: str
    reason: str
    updated_at: str
    updated_by: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "engaged": self.engaged,
            "scope": self.scope,
            "reason": self.reason,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
        }


class KillSwitch:
    """Kill switch controller.

    Fail-closed design: unreadable/corrupt state is treated as engaged.
    """

    def __init__(self, state_dir: str | Path):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _global_path(self) -> Path:
        return self.state_dir / "global.json"

    def _business_path(self, business_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in business_id)
        if not safe:
            raise ValueError("business_id must be non-empty")
        return self.state_dir / f"business_{safe}.json"

    def _read_state(self, path: Path, scope: str) -> KillSwitchState:
        if not path.exists():
            return KillSwitchState(
                engaged=False,
                scope=scope,
                reason="default_disengaged",
                updated_at=_utc_now_iso(),
                updated_by="system",
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("state must be an object")
            return KillSwitchState(
                engaged=bool(data.get("engaged", True)),
                scope=scope,
                reason=str(data.get("reason", "unspecified")),
                updated_at=str(data.get("updated_at", _utc_now_iso())),
                updated_by=str(data.get("updated_by", "unknown")),
            )
        except Exception:
            # Fail closed.
            return KillSwitchState(
                engaged=True,
                scope=scope,
                reason="fail_closed_unreadable_state",
                updated_at=_utc_now_iso(),
                updated_by="system",
            )

    def _write_state(self, path: Path, state: KillSwitchState) -> None:
        path.write_text(
            json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def engage_global(self, *, reason: str, updated_by: str) -> KillSwitchState:
        state = KillSwitchState(True, "global", reason, _utc_now_iso(), updated_by)
        self._write_state(self._global_path(), state)
        return state

    def disengage_global(self, *, reason: str, updated_by: str) -> KillSwitchState:
        state = KillSwitchState(False, "global", reason, _utc_now_iso(), updated_by)
        self._write_state(self._global_path(), state)
        return state

    def engage_business(self, business_id: str, *, reason: str, updated_by: str) -> KillSwitchState:
        state = KillSwitchState(True, f"business:{business_id}", reason, _utc_now_iso(), updated_by)
        self._write_state(self._business_path(business_id), state)
        return state

    def disengage_business(
        self, business_id: str, *, reason: str, updated_by: str
    ) -> KillSwitchState:
        state = KillSwitchState(
            False, f"business:{business_id}", reason, _utc_now_iso(), updated_by
        )
        self._write_state(self._business_path(business_id), state)
        return state

    def get_global_state(self) -> KillSwitchState:
        return self._read_state(self._global_path(), "global")

    def get_business_state(self, business_id: str) -> KillSwitchState:
        return self._read_state(self._business_path(business_id), f"business:{business_id}")

    def is_engaged(self, business_id: str | None = None) -> bool:
        if self.get_global_state().engaged:
            return True
        if business_id is not None and self.get_business_state(business_id).engaged:
            return True
        return False

    def assert_not_engaged(self, business_id: str | None = None) -> None:
        global_state = self.get_global_state()
        if global_state.engaged:
            raise KillSwitchEngagedError(f"Global kill switch engaged: {global_state.reason}")
        if business_id is not None:
            biz_state = self.get_business_state(business_id)
            if biz_state.engaged:
                raise KillSwitchEngagedError(
                    f"Business kill switch engaged for {business_id}: {biz_state.reason}"
                )
