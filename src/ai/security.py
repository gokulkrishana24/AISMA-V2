from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.injection import InjectionScanError, scan_untrusted_text
from governance.killswitch import KillSwitch


@dataclass
class SanitizedInput:
    original_length: int
    sanitized_text: str
    truncated: bool
    scan: dict[str, Any] | None


class AISecurityGuard:
    """Applies Phase 1 governance checks before LLM processing.

    LLM outputs must never directly execute privileged actions; callers must
    route sensitive operations through PolicyEngine/PermissionManager/KillSwitch.
    """

    def __init__(self, kill_switch: KillSwitch | None = None, max_input_chars: int = 24000):
        self.kill_switch = kill_switch
        self.max_input_chars = max_input_chars

    def assert_runtime_allowed(self, business_id: str | None = None) -> None:
        if self.kill_switch and self.kill_switch.is_engaged(business_id):
            raise PermissionError("Kill switch engaged; AI runtime blocked")

    def sanitize_untrusted(
        self,
        text: str,
        *,
        source: str,
        strict_injection: bool = True,
    ) -> SanitizedInput:
        if text is None:
            text = ""
        if not isinstance(text, str):
            text = str(text)
        original_length = len(text)
        truncated = False
        if original_length > self.max_input_chars:
            text = text[: self.max_input_chars] + "\n[TRUNCATED_BY_INPUT_LIMIT]"
            truncated = True
        scan = scan_untrusted_text(text, strict=strict_injection, source=source)
        return SanitizedInput(
            original_length=original_length,
            sanitized_text=scan["isolated_text"],
            truncated=truncated,
            scan=scan,
        )

    def scan_only(self, text: str, *, source: str, strict: bool = False) -> dict[str, Any]:
        try:
            return scan_untrusted_text(text, strict=strict, source=source)
        except InjectionScanError as exc:
            return {"is_safe": False, "error": str(exc), "source": source}
