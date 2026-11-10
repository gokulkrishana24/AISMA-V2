from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .frontmatter import FrontmatterError, parse_frontmatter, validate_frontmatter


@dataclass(frozen=True)
class LintFinding:
    code: str
    severity: str
    message: str
    location: str = ""


# Heuristics: agents must not invent pricing/delivery/availability. We flag assertive patterns.
_PRICING_RE = re.compile(
    r"\b(\$\s?\d[\d,]*(?:\.\d+)?|\d[\d,]*(?:\.\d+)?\s?(?:usd|eur|gbp|egp|aed|sar)|price is|costs? only|starting at)\b",
    re.I,
)
_DELIVERY_RE = re.compile(
    r"\b(deliver(?:y|ed)? in \d+|arrives? in \d+|same[- ]day delivery|guaranteed delivery|ships? (?:today|tomorrow|in \d+))\b",
    re.I,
)
_AVAILABILITY_RE = re.compile(
    r"\b(in stock|out of stock|available now|only \d+ left|unlimited availability|guaranteed availability)\b",
    re.I,
)
_EVIDENCE_CLAIM_RE = re.compile(
    r"\b(according to (?:our|the) data|studies show|proven to|guarantees?|roi of \d+%|increased by \d+%)\b",
    re.I,
)


def lint_text(text: str, *, allow_factual_claims_without_evidence: bool = False) -> list[LintFinding]:
    findings: list[LintFinding] = []
    if not isinstance(text, str):
        text = str(text)
    if _PRICING_RE.search(text):
        findings.append(
            LintFinding(
                "LINT_INVENTED_PRICING_RISK",
                "high",
                "Potential pricing claim detected; pricing must come from approved business data.",
                "body",
            )
        )
    if _DELIVERY_RE.search(text):
        findings.append(
            LintFinding(
                "LINT_INVENTED_DELIVERY_RISK",
                "high",
                "Potential delivery/date claim detected; never invent delivery dates.",
                "body",
            )
        )
    if _AVAILABILITY_RE.search(text):
        findings.append(
            LintFinding(
                "LINT_INVENTED_AVAILABILITY_RISK",
                "high",
                "Potential availability claim detected; availability must be verified.",
                "body",
            )
        )
    if not allow_factual_claims_without_evidence and _EVIDENCE_CLAIM_RE.search(text):
        findings.append(
            LintFinding(
                "LINT_UNSUPPORTED_CLAIM_RISK",
                "medium",
                "Potential factual/performance claim detected; ensure supporting evidence exists.",
                "body",
            )
        )
    return findings


def lint_artifact(markdown_text: str, *, strict_frontmatter: bool = True) -> dict[str, Any]:
    findings: list[LintFinding] = []
    frontmatter: dict[str, Any] | None = None
    body = markdown_text
    try:
        parsed = parse_frontmatter(markdown_text)
        frontmatter = parsed.frontmatter
        body = parsed.body
        if strict_frontmatter:
            validate_frontmatter(frontmatter)
    except FrontmatterError as exc:
        findings.append(LintFinding("LINT_FRONTMATTER_INVALID", "critical", str(exc), "frontmatter"))

    findings.extend(lint_text(body))
    # Negative reviews/responses should be marked for approval in content workflows.
    if frontmatter:
        ctype = str(frontmatter.get("content_type", ""))
        if ctype in {"review_response", "complaint_response"}:
            if not frontmatter.get("requires_human_approval", True):
                findings.append(
                    LintFinding(
                        "LINT_REVIEW_APPROVAL_REQUIRED",
                        "critical",
                        "Review/complaint responses must require human approval.",
                        "frontmatter",
                    )
                )
    return {
        "ok": not any(f.severity in {"high", "critical"} for f in findings),
        "frontmatter": frontmatter,
        "findings": [f.__dict__ for f in findings],
    }
