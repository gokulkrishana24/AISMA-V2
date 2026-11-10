from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


class InjectionScanError(ValueError):
    """Raised when untrusted text fails injection scanning in strict mode."""


@dataclass(frozen=True)
class InjectionFinding:
    code: str
    severity: str  # low|medium|high|critical
    message: str
    excerpt: str


_PATTERNS: list[tuple[str, str, str, re.Pattern[str]]] = [
    (
        "INJ_IGNORE_INSTRUCTIONS",
        "critical",
        "Attempts to override or ignore prior instructions",
        re.compile(r"\b(ignore|disregard|forget)\b.{0,80}\b(instructions|rules|system|prompt)\b", re.I | re.S),
    ),
    (
        "INJ_SYSTEM_PROMPT",
        "high",
        "Attempts to access or reveal system/developer prompts",
        re.compile(r"\b(system prompt|developer message|hidden instructions|reveal.*prompt)\b", re.I),
    ),
    (
        "INJ_ROLE_ESCAPE",
        "high",
        "Attempts role/persona escape or jailbreak framing",
        re.compile(r"\b(you are now|act as|pretend to be|jailbreak|do anything now|dan)\b", re.I),
    ),
    (
        "INJ_TOOL_MISUSE",
        "high",
        "Attempts to coerce tool execution or privilege escalation",
        re.compile(r"\b(run shell|execute command|call tool|bypass|override policy|disable safety)\b", re.I),
    ),
    (
        "INJ_DATA_EXFIL",
        "critical",
        "Attempts to exfiltrate secrets or private data",
        re.compile(r"\b(api key|token|password|secret|private key|show.*env|print.*credentials)\b", re.I),
    ),
]


def scan_untrusted_text(text: str, *, strict: bool = True, source: str = "external") -> dict[str, Any]:
    """Scan untrusted text for prompt-injection indicators.

    External/user-imported/web/review text must never be treated as trusted instructions.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        text = str(text)
    findings: list[InjectionFinding] = []
    for code, severity, message, pattern in _PATTERNS:
        m = pattern.search(text)
        if m:
            excerpt = m.group(0)
            excerpt = excerpt[:160].replace("\n", " ")
            findings.append(InjectionFinding(code, severity, message, excerpt))
    risk = "none"
    if any(f.severity == "critical" for f in findings):
        risk = "critical"
    elif any(f.severity == "high" for f in findings):
        risk = "high"
    elif findings:
        risk = "medium"
    result = {
        "source": source,
        "is_safe": len(findings) == 0,
        "risk": risk,
        "findings": [f.__dict__ for f in findings],
        "isolated_text": wrap_untrusted_text(text, source=source),
    }
    if strict and findings:
        raise InjectionScanError(
            f"Injection scan failed for {source}: {[f.code for f in findings]}"
        )
    return result


def wrap_untrusted_text(text: str, *, source: str = "external") -> str:
    """Wrap untrusted text in explicit delimiters to reduce instruction confusion.

    This is defense-in-depth only; backend enforcement remains mandatory.
    """
    safe_source = re.sub(r"[^A-Za-z0-9_-]", "_", source)
    body = text if isinstance(text, str) else str(text)
    # Neutralize delimiter collisions.
    body = body.replace("</UNTRUSTED_TEXT>", "<\\/UNTRUSTED_TEXT>")
    return (
        f"<UNTRUSTED_TEXT source=\"{safe_source}\">\n"
        f"{body}\n"
        "</UNTRUSTED_TEXT>"
    )
