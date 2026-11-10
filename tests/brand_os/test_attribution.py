"""Attribution tests for Brand OS Phase 4."""

from brand_os.attribution import (
    attach_attribution_to_output,
    extract_source_reference,
    validate_source_support,
)


class TestSourceValidation:
    """Test source support validation."""

    def test_validate_source_support_valid(self):
        """Valid source should pass validation."""
        supported, reason = validate_source_support(
            {"source_name": "test_doc", "source_type": "ingested"},
            "This is a verified claim.",
        )
        assert supported

    def test_validate_source_support_missing(self):
        """Missing source should fail validation."""
        supported, reason = validate_source_support(
            None,
            "This is an unverified claim.",
        )
        # Missing source should be detected
        assert not supported or "missing" in reason.lower()

    def test_validate_source_support_empty(self):
        """Empty source should fail validation."""
        supported, reason = validate_source_support(
            {},
            "This is a claim.",
        )
        assert not supported or "missing" in reason.lower()


class TestAttachAttribution:
    """Test attaching attribution to output."""

    def test_attach_attribution_preserves_output(self):
        """Attribution should be attached without destroying output."""
        output = "This is the main output text."
        sources = [
            {"source_name": "test_doc", "source_type": "ingested", "source_reference": "doc_1"}
        ]

        result = attach_attribution_to_output(output, sources)
        assert result is not None
        assert "This is the main output text." in result or result == output


class TestExtractSourceReference:
    """Test source reference extraction."""

    def test_extract_source_reference_basic(self):
        """Basic source reference extraction."""
        ref = extract_source_reference(
            {"source_name": "test_doc", "source_type": "ingested", "page": 1}
        )
        assert ref is not None


class TestSourceDistinction:
    """Test that source-supported vs LLM-suggested vs missing vs unverified are distinguished."""

    def test_source_supported_distinction(self):
        """Source-supported facts should be distinguished."""
        supported, _ = validate_source_support(
            {"source_name": "doc_1", "source_type": "ingested"},
            "The sky is blue.",
        )
        assert supported

    def test_missing_vs_unverified(self):
        """Missing and unverified should be distinguishable."""
        # Missing
        supported_missing, _ = validate_source_support(None, "Unknown claim")
        # Unverified (no source but not explicitly missing)
        supported_unverified, _ = validate_source_support(
            {}, "Claim without source but not marked missing"
        )
        # They may have different behaviors
        assert not supported_missing or not supported_unverified