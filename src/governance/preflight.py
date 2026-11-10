from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class PreflightError(RuntimeError):
    """Raised when fail-closed preflight checks do not pass."""


@dataclass
class PreflightResult:
    ok: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "checks": self.checks, "errors": self.errors}


def _check(result: PreflightResult, name: str, ok: bool, detail: str) -> None:
    result.checks.append({"name": name, "ok": ok, "detail": detail})
    if not ok:
        result.errors.append(f"{name}: {detail}")
        result.ok = False


def run_preflight(
    *,
    required_paths: list[str | Path] | None = None,
    writable_paths: list[str | Path] | None = None,
    config_files: dict[str, str | Path] | None = None,
    fail_closed: bool = True,
) -> PreflightResult:
    """Run startup/governance preflight checks.

    In fail-closed mode, any error makes the result not ok and `require_ok` raises.
    """
    result = PreflightResult(ok=True)
    required_paths = required_paths or []
    writable_paths = writable_paths or []
    config_files = config_files or {}

    for raw in required_paths:
        path = Path(raw)
        _check(result, f"path_exists:{path}", path.exists(), "exists" if path.exists() else "missing")

    for raw in writable_paths:
        path = Path(raw)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".preflight_write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            _check(result, f"path_writable:{path}", True, "writable")
        except Exception as exc:
            _check(result, f"path_writable:{path}", False, f"not writable: {exc}")

    for label, raw in config_files.items():
        path = Path(raw)
        if not path.exists():
            _check(result, f"config:{label}", not fail_closed, f"missing config: {path}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".json":
                data = json.loads(text)
            elif path.suffix.lower() in {".yaml", ".yml"}:
                data = yaml.safe_load(text)
            else:
                data = text
            valid = data is not None or not fail_closed
            _check(result, f"config:{label}", bool(valid) or not fail_closed, f"loaded {path.name}")
        except Exception as exc:
            _check(result, f"config:{label}", False, f"invalid config {path}: {exc}")

    # Fail-closed sanity: preflight must have run checks when inputs provided? not mandatory.
    if fail_closed and result.errors:
        result.ok = False
    return result


def require_preflight_ok(result: PreflightResult) -> PreflightResult:
    if not result.ok:
        raise PreflightError("Preflight failed: " + "; ".join(result.errors))
    return result
