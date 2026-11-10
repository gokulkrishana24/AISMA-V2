from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

GENESIS_HASH = "0" * 64

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
# Conservative long-number redaction (cards/ids) while avoiding small integers.
_LONG_NUMBER_RE = re.compile(r"(?<!\d)\d{13,19}(?!\d)")


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def redact_pii(value: Any) -> Any:
    """Recursively redact common PII patterns from audit details.

    Redaction is best-effort and fail-safe (it prefers masking over leakage).
    """
    if value is None:
        return None
    if isinstance(value, str):
        masked = _EMAIL_RE.sub("[REDACTED_EMAIL]", value)
        masked = _PHONE_RE.sub("[REDACTED_PHONE]", masked)
        masked = _LONG_NUMBER_RE.sub("[REDACTED_NUMBER]", masked)
        return masked
    if isinstance(value, list):
        return [redact_pii(v) for v in value]
    if isinstance(value, tuple):
        return [redact_pii(v) for v in value]
    if isinstance(value, dict):
        return {str(k): redact_pii(v) for k, v in value.items()}
    if isinstance(value, (int, float, bool)):
        return value
    return redact_pii(str(value))


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_entry_hash(entry_without_hash: dict[str, Any]) -> str:
    payload = canonical_json(entry_without_hash).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class AuditEntry:
    timestamp: str
    business_id: str
    actor: str
    action: str
    resource: str
    outcome: str
    details: dict[str, Any]
    prev_hash: str
    entry_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditLogger:
    """Append-only hash-chained audit logger.

    Each business gets its own log file to support isolation and simpler verification.
    """

    def __init__(self, log_dir: str | Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self, business_id: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", business_id)
        if not safe:
            raise ValueError("business_id must contain safe characters")
        return self.log_dir / f"{safe}.jsonl"

    def _read_last_hash(self, path: Path) -> str:
        if not path.exists():
            return GENESIS_HASH
        last_hash = GENESIS_HASH
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Corrupt audit log: {path}") from exc
                if not isinstance(obj, dict) or "entry_hash" not in obj:
                    raise ValueError(f"Invalid audit entry in: {path}")
                last_hash = str(obj["entry_hash"])
        return last_hash

    def log(
        self,
        *,
        business_id: str,
        actor: str,
        action: str,
        resource: str,
        outcome: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        if not business_id or not actor or not action:
            raise ValueError("business_id, actor, and action are required")
        path = self._log_path(business_id)
        prev_hash = self._read_last_hash(path)
        redacted_details = redact_pii(details or {})
        base: dict[str, Any] = {
            "timestamp": utc_now_iso(),
            "business_id": business_id,
            "actor": actor,
            "action": action,
            "resource": resource,
            "outcome": outcome,
            "details": redacted_details,
            "prev_hash": prev_hash,
        }
        entry_hash = compute_entry_hash(base)
        entry = AuditEntry(entry_hash=entry_hash, **base)  # type: ignore[arg-type]
        line = canonical_json(entry.to_dict())
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
            f.flush()
        return entry

    def read_entries(self, business_id: str) -> list[dict[str, Any]]:
        path = self._log_path(business_id)
        if not path.exists():
            return []
        entries: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries


def verify_audit_chain(entries: list[dict[str, Any]]) -> tuple[bool, str]:
    """Verify hash chain integrity for a list of audit entries."""
    prev_hash = GENESIS_HASH
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            return False, f"Entry {i} is not an object"
        expected_prev = str(entry.get("prev_hash", ""))
        if expected_prev != prev_hash:
            return False, f"Entry {i} has invalid prev_hash"
        actual_hash = str(entry.get("entry_hash", ""))
        base = {k: v for k, v in entry.items() if k != "entry_hash"}
        computed = compute_entry_hash(base)
        if actual_hash != computed:
            return False, f"Entry {i} has invalid entry_hash"
        prev_hash = actual_hash
    return True, "ok"
