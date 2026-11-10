import pytest

from governance.frontmatter import (
    FrontmatterError,
    apply_transition,
    assert_legal_transition,
    parse_frontmatter,
    validate_frontmatter,
)

VALID = """---
id: art1
business_id: biz1
agent: content_engine
content_type: social_post
status: draft
created_at: 2026-01-01T00:00:00Z
---
Hello world
"""


def test_parse_and_validate() -> None:
    parsed = parse_frontmatter(VALID)
    assert parsed.frontmatter["id"] == "art1"
    assert parsed.body.strip() == "Hello world"
    validate_frontmatter(parsed.frontmatter)


def test_missing_frontmatter() -> None:
    with pytest.raises(FrontmatterError):
        parse_frontmatter("no frontmatter")


def test_legal_transitions() -> None:
    assert_legal_transition("draft", "pending_approval")
    assert_legal_transition("approved", "scheduled")
    with pytest.raises(FrontmatterError):
        assert_legal_transition("published", "draft")
    with pytest.raises(FrontmatterError):
        assert_legal_transition("draft", "published")


def test_apply_transition_requires_approval_metadata() -> None:
    parsed = parse_frontmatter(VALID)
    pending = apply_transition(parsed.frontmatter, "pending_approval")
    approved = apply_transition(pending, "approved", approved_by="human:alice")
    assert approved["approved_by"] == "human:alice"
    with pytest.raises(FrontmatterError):
        apply_transition(pending, "approved")
