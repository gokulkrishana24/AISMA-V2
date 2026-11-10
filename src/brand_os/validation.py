"""Validation logic for Brand OS templates and content.

Ensures that:
1. Required fields are present and non-empty.
2. Field validation rules (e.g., non_empty_string, min_items, max_chars) are satisfied.
3. [MISSING] and [VERIFY] markers are correctly extracted and tracked.
4. No unverified or fabricated claims bypass governance.
"""

from __future__ import annotations

import re
from typing import Any

from brand_os.schemas import MissingIndicator, TemplateID
from brand_os.templates import TEMPLATE_REGISTRY

_MISSING_PATTERN = re.compile(r"\[MISSING(?::\s*([^\]]+))?\]", re.IGNORECASE)
_VERIFY_PATTERN = re.compile(r"\[VERIFY(?::\s*([^\]]+))?\]", re.IGNORECASE)


def detect_markers(text: str) -> dict[str, list[str]]:
    """Scan text for [MISSING] and [VERIFY] tags and extract their descriptions."""
    missing: list[str] = []
    verify: list[str] = []

    for match in _MISSING_PATTERN.finditer(text):
        desc = match.group(1) or "unspecified missing field"
        missing.append(f"{MissingIndicator.MISSING.value} {desc.strip()}")

    for match in _VERIFY_PATTERN.finditer(text):
        desc = match.group(1) or "unverified claim requiring verification"
        verify.append(f"{MissingIndicator.VERIFY.value} {desc.strip()}")

    return {"missing": missing, "verify": verify}


def validate_field_value(field_spec: dict[str, Any], value: Any) -> tuple[bool, str | None]:
    """Validate an individual field against its schema specification."""
    field_type = field_spec.get("type", "optional")
    val_rule = field_spec.get("validation", "none")

    # Check existence
    if value is None or (isinstance(value, str) and not value.strip()):
        if field_type == "required":
            return False, "Required field is empty or missing"
        return True, None

    # String validations
    if isinstance(value, str):
        if val_rule == "non_empty_string" and not value.strip():
            return False, "Must be a non-empty string"
        if val_rule.startswith("max_chars("):
            try:
                max_len = int(val_rule[len("max_chars(") : -1])
                if len(value) > max_len:
                    return False, f"Exceeds maximum length of {max_len} characters"
            except ValueError:
                pass

    # List validations
    if isinstance(value, list):
        if val_rule.startswith("min_items("):
            try:
                min_count = int(val_rule[len("min_items(") : -1])
                if len(value) < min_count:
                    return False, f"Must contain at least {min_count} item(s)"
            except ValueError:
                pass

    return True, None


class ValidationReport(tuple):
    """Result from validate_template_data that behaves as both tuple and dict/object."""

    def __new__(cls, is_valid: bool, errors: list[str], markers: dict[str, Any]):
        return super().__new__(cls, (is_valid, errors, markers))

    def __init__(self, is_valid: bool, errors: list[str], markers: dict[str, Any]):
        self.is_valid = is_valid
        self.is_complete = is_valid
        self.errors = errors
        self.missing_fields = errors
        self.markers = markers

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            if item in {"is_valid", "is_complete"}:
                return self.is_valid
            if item in {"errors", "missing_fields"}:
                return self.errors
            if item == "markers":
                return self.markers
        return super().__getitem__(item)


def validate_template_data(template_id: TemplateID, data: dict[str, Any]) -> ValidationReport:
    """Validate a complete data dictionary against a registered Brand OS template."""
    spec = TEMPLATE_REGISTRY.get(template_id)
    if not spec:
        return ValidationReport(False, [f"Unknown template ID: {template_id}"], {"missing": [], "verify": []})

    errors: list[str] = []
    text_content: list[str] = []
    fields = spec.get("fields", {})

    for field_name, field_spec in fields.items():
        val = data.get(field_name)
        ok, err = validate_field_value(field_spec, val)
        if not ok and err:
            errors.append(f"{field_name}: {err}")
        if isinstance(val, str):
            text_content.append(val)
        elif isinstance(val, list):
            text_content.extend(str(item) for item in val)

    # Detect [MISSING] and [VERIFY] markers in the text content
    combined_text = "\n".join(text_content)
    markers = detect_markers(combined_text)

    is_valid = len(errors) == 0
    return ValidationReport(is_valid, errors, markers)


def validate_template_field(
    template_id: Any,
    field_name: str,
    value: Any,
) -> tuple[bool, str | None]:
    """Validate a single field within a template specification."""
    try:
        tid = TemplateID(template_id) if isinstance(template_id, str) else template_id
    except ValueError:
        return True, None
    spec = TEMPLATE_REGISTRY.get(tid, {})
    field_spec = spec.get("fields", {}).get(field_name, {"type": "optional", "validation": "none"})
    return validate_field_value(field_spec, value)

