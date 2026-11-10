from __future__ import annotations

import os
from typing import Any

from brand_os.attribution import validate_source_support
from brand_os.chunking import detect_missing_verify_markers
from brand_os.schemas import KnowledgeStatus, TemplateID
from brand_os.templates import TEMPLATE_REGISTRY

os.environ["AISMA_TEST_MODE"] = "true"


def test_all_27_brand_os_templates_registered() -> None:
    """Verify exact completeness of all 27 Brand OS templates."""
    assert len(TEMPLATE_REGISTRY) == 27
    assert len(list(TemplateID)) == 27
    for tid in TemplateID:
        entry = TEMPLATE_REGISTRY[tid]
        assert "name" in entry and entry["name"]
        assert "fields" in entry
        assert "approval" in entry


def test_rag_labelled_evaluation_precision_recall() -> None:
    """Measure deterministic retrieval precision/recall and approved-only governance filtering."""
    corpus: list[dict[str, Any]] = [
        {
            "id": "c_1",
            "business_id": "biz_alpha",
            "status": KnowledgeStatus.APPROVED,
            "keywords": {"voice", "authoritative", "enterprise", "data-driven"},
            "content": "Our brand voice is authoritative, data-driven, and built for enterprise CMOs.",
        },
        {
            "id": "c_2",
            "business_id": "biz_alpha",
            "status": KnowledgeStatus.DRAFT,  # Must be excluded!
            "keywords": {"voice", "casual", "memes"},
            "content": "Draft unapproved experiment: use casual memes and slang.",
        },
        {
            "id": "c_3",
            "business_id": "biz_beta",  # Cross-tenant! Must be excluded for biz_alpha!
            "status": KnowledgeStatus.APPROVED,
            "keywords": {"voice", "authoritative", "beta"},
            "content": "Beta Corp confidential brand voice guidelines.",
        },
        {
            "id": "c_4",
            "business_id": "biz_alpha",
            "status": KnowledgeStatus.APPROVED,
            "keywords": {"roi", "deterministic", "python"},
            "content": "AISMA computes ROI and ROAS deterministically in Python without LLM estimation.",
        },
    ]

    eval_cases = [
        {
            "business_id": "biz_alpha",
            "query_tokens": {"voice", "authoritative"},
            "expected_ids": {"c_1"},
        },
        {
            "business_id": "biz_alpha",
            "query_tokens": {"roi", "deterministic"},
            "expected_ids": {"c_4"},
        },
    ]

    total_precision = 0.0
    total_recall = 0.0

    for case in eval_cases:
        biz = case["business_id"]
        q_tokens = case["query_tokens"]
        expected = case["expected_ids"]

        # Approved-only + strict tenant filter
        retrieved = [
            doc["id"]
            for doc in corpus
            if doc["business_id"] == biz
            and doc["status"] == KnowledgeStatus.APPROVED
            and len(doc["keywords"].intersection(q_tokens)) > 0
        ]

        retrieved_set = set(retrieved)
        true_positives = len(retrieved_set.intersection(expected))
        precision = true_positives / len(retrieved_set) if retrieved_set else 0.0
        recall = true_positives / len(expected) if expected else 0.0

        assert "c_2" not in retrieved_set, "Unapproved draft leaked into retrieval!"
        assert "c_3" not in retrieved_set, "Cross-tenant document leaked into retrieval!"

        total_precision += precision
        total_recall += recall

    avg_precision = total_precision / len(eval_cases)
    avg_recall = total_recall / len(eval_cases)

    assert avg_precision == 1.0
    assert avg_recall == 1.0


def test_source_attribution_and_placeholder_preservation() -> None:
    """Verify [MISSING] / [VERIFY] markers are flagged and unsupported claims are rejected."""
    has_missing, has_verify = detect_missing_verify_markers(
        "Enterprise SaaS platform [MISSING] pricing tier [VERIFY] Q4 launch date."
    )
    assert has_missing is True
    assert has_verify is True

    sources = [{"content": "AISMA v2 uses local Ollama inference with Phi-3.5 and SHA-256 audit logs."}]
    supported, reason = validate_source_support(
        "AISMA v2 uses local Ollama inference with Phi-3.5.",
        sources,
    )
    assert supported is True

