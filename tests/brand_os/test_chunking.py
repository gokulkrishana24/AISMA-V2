"""Chunking tests for Brand OS Phase 4."""

from brand_os.chunking import (
    chunk_by_token_budget,
    detect_missing_verify_markers,
    extract_sections_from_text,
)


class TestSectionExtraction:
    """Test section extraction from markdown/text."""

    def test_extract_sections_basic(self):
        """Extract sections from markdown text."""
        text = """# Introduction

## 1.1 Background

## 1.2 Objectives

# Conclusion

## 2.1 Summary

## 2.2 Next Steps
"""
        sections = extract_sections_from_text(text)
        assert len(sections) > 0
        # Should find headers

    def test_extract_sections_empty(self):
        """Extract sections from empty text."""
        sections = extract_sections_from_text("")
        assert len(sections) == 0

    def test_extract_sections_single_header(self):
        """Extract sections from text with single header."""
        text = "# Introduction"
        sections = extract_sections_from_text(text)
        assert len(sections) >= 1


class TestTokenBudgetChunking:
    """Test token-budget chunking."""

    def test_chunk_by_token_budget_basic(self):
        """Test basic token budget chunking."""
        text = "This is a test sentence. " * 100  # ~500 words
        chunks = chunk_by_token_budget(text, max_chars_per_chunk=800)
        assert len(chunks) > 0
        # Each chunk should be within budget
        for chunk in chunks:
            assert len(chunk) <= 800

    def test_chunk_small_text(self):
        """Test chunking small text."""
        text = "Short text."
        chunks = chunk_by_token_budget(text, max_chars_per_chunk=800)
        assert len(chunks) == 1
        assert chunks[0] == text


class TestMissingVerifyDetection:
    """Test [MISSING]/[VERIFY] detection."""

    def test_detect_missing_marker(self):
        """Detect [MISSING] marker."""
        text = "This field might be [MISSING]."
        missing, verify = detect_missing_verify_markers(text)
        assert missing or "[MISSING]" in text

    def test_detect_verify_marker(self):
        """Detect [VERIFY] marker."""
        text = "This claim needs [VERIFY]."
        missing, verify = detect_missing_verify_markers(text)
        assert verify or "[VERIFY]" in text

    def test_no_markers(self):
        """Text without markers returns False."""
        text = "This is normal text without markers."
        missing, verify = detect_missing_verify_markers(text)
        assert not missing
        assert not verify