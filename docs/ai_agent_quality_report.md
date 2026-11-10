# AISMA v2 — AI Agent & Brand OS RAG Quality Report

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Eight-Agent Orchestration Quality

All 8 specialized marketing agents (`search_visibility`, `market_radar`, `content_engine`, `creative_studio`, `publishing_social`, `reviews_reputation`, `leads_conversations`, `results_roi`) execute through `Orchestrator` (`src/orchestrator/orchestrator.py`) sharing one `LLMProvider` (`phi3.5:latest`).
- **Governance Enforcement:** Tested end-to-end in `tests/integration/test_end_to_end_workflow.py` — drafts require human approval (`requires_human_approval = True`), obey daily budgets, and fail closed when killswitch is engaged.
- **Live Ollama Tests vs Automated CI Mocks:** Automated unit/integration runs use deterministic mocks (`AISMA_TEST_MODE=true`), while optional real-hardware Ollama tests (`tests/ai/test_real_ollama_optional.py`, `tests/integration/test_real_ollama_phase3_optional.py`) are explicitly skipped in standard CI unless `AISMA_RUN_REAL_OLLAMA_TESTS=1` is set.

---

## 2. Brand OS & RAG Evaluation Measurements (`tests/ai/test_rag_eval_precision_recall.py`)

| Evaluation Check | Measured Outcome | Notes |
| :--- | :--- | :--- |
| **27 Brand OS Templates** | **27 / 27 Verified** | All `TemplateID` enum values present in `TEMPLATE_REGISTRY` with required validation rules. |
| **Approved-Only Retrieval Filtering** | **100% Enforced** | `KnowledgeStatus.DRAFT` documents strictly excluded from retrieval results. |
| **Cross-Tenant Isolation in RAG** | **0 Leaks** | Documents belonging to `biz_beta` excluded when querying as `biz_alpha`. |
| **Labelled Eval Precision / Recall** | **Precision = 1.0, Recall = 1.0** | Measured over deterministic labelled Brand OS corpus in `test_rag_labelled_evaluation_precision_recall`. |
| **Placeholder & Attribution Guardrails** | **Verified** | `[MISSING]` / `[VERIFY]` markers detected (`detect_missing_verify_markers`); claims validated against source chunks (`validate_source_support`). |

