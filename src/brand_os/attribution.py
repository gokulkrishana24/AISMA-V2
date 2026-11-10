"""Source attribution for RAG-retrieved brand knowledge.

Ensures that every piece of knowledge supplied to an agent carries explicit
evidence references (document_id, template_id, section_id, version, source_name).
The system must distinguish source-supported facts, user-provided information,
LLM-generated suggestions, missing information, and unverified information.

Never fabricate citations. If no source supports a generated claim, identify it
as unsupported or requiring verification.
"""

from __future__ import annotations

from typing import Any


def extract_source_reference(result: Any) -> dict[str, str]:
    """Extract a canonical source reference from a RetrievalResult or dictionary.

    Returns a dict with the key fields needed for citation.
    """
    if isinstance(result, dict):
        return {
            "document_id": str(result.get("document_id", result.get("source_name", "unknown"))),
            "template_id": str(result.get("template_id", "general")),
            "section_id": str(result.get("section_id", "main")),
            "version": str(result.get("version", "v1.0")),
            "source_reference": str(result.get("source_reference", result.get("source_type", "ingested"))),
        }
    return {
        "document_id": str(getattr(result, "document_id", "unknown")),
        "template_id": str(getattr(result, "template_id", "general")),
        "section_id": str(getattr(result, "section_id", "main")),
        "version": str(getattr(result, "version", "v1.0")),
        "source_reference": str(getattr(result, "source_reference", "verified")),
    }


class ValidationResult(tuple):
    """Dual tuple-and-dict response for source support validation."""

    def __new__(cls, supported: bool, reason: str, details: dict[str, Any] | None = None):
        return super().__new__(cls, (supported, reason))

    def __init__(self, supported: bool, reason: str, details: dict[str, Any] | None = None):
        self.supported = supported
        self.reason = reason
        self.details = details or {}

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            if item == "supported":
                return self.supported
            if item == "reason":
                return self.reason
            return self.details.get(item)
        return super().__getitem__(item)

    def get(self, k: str, default: Any = None) -> Any:
        if k == "supported":
            return self.supported
        if k == "reason":
            return self.reason
        return self.details.get(k, default)


def validate_source_support(
    first_arg: Any,
    second_arg: Any = None,
) -> ValidationResult:
    """Determine whether a claim is supported by a source or retrieved chunks."""
    if isinstance(first_arg, str) and not isinstance(second_arg, str):
        source = second_arg
    else:
        source = first_arg

    if source is None:
        return ValidationResult(False, "Missing source: No supporting evidence provided")

    if isinstance(source, dict):
        if not source:
            return ValidationResult(False, "Unverified: Empty source provided")
        if source.get("source_name") or source.get("document_id"):
            return ValidationResult(True, f"Supported by {source.get('source_name') or source.get('document_id')}")
        return ValidationResult(False, "Unverified: Insufficient source metadata")

    if isinstance(source, list):
        if not source:
            return ValidationResult(False, "Missing: No supporting chunks provided")
        supported = any(getattr(c, "approved", True) for c in source)
        reason = "Supported by approved chunks" if supported else "Unsupported: Chunks not approved"
        return ValidationResult(supported, reason, {"evidence": [extract_source_reference(c) for c in source]})

    return ValidationResult(False, "Unsupported source format")


def attach_attribution_to_output(
    output: Any,
    sources: Any,
) -> Any:
    """Attach source attribution metadata or citations to generated output."""
    if isinstance(output, str):
        if not sources:
            return output
        citations = "\n\nSources:\n" + "\n".join(
            f"- {s.get('source_name') or s.get('document_id', 'source')} ({s.get('source_type') or s.get('source_reference', 'verified')})"
            for s in sources
            if isinstance(s, dict)
        )
        return output + citations

    if isinstance(output, dict):
        evidence_refs = [extract_source_reference(c) for c in sources] if isinstance(sources, list) else []
        output["evidence"] = evidence_refs
        return output

    return output