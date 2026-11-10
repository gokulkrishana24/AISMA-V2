# AISMA v2 — AI & Multi-Agent Reliability Report

**AI Systems Engineer:** Chief AI Engineer & Model Operations Architect  
**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Local AI Architecture & Hardware Topology

AISMA v2 is engineered specifically for local-first enterprise inference on realistic hardware:
- **Host GPU:** NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM)
- **Host CPU / RAM:** 16 logical cores, ~16 GB physical RAM
- **Local Inference Runtime:** Ollama Daemon (Port 11434)
- **Primary Model:** `phi3.5:latest` (3.8B parameters, verified sub-second response on 4GB VRAM)
- **Fallback / Secondary Models:** `qwen3.5:4b`
- **Memory Safety Guardrail:** 9B models properly flagged as `timed_out` on 4GB VRAM, preventing out-of-memory driver crashes.

---

## 2. Multi-Agent Orchestration & Reliability

The eight specialized marketing agents are coordinated through the central `Orchestrator` (`src/orchestrator/orchestrator.py`):

1. **Search Visibility Agent:** Keyword tracking, query intent classification, GSC index monitoring.
2. **Market Radar Agent:** Competitor narrative tracking, audience intent shifts.
3. **Content Engine Agent:** Brand OS compliant draft generation with alternative hooks.
4. **Creative Studio Agent:** Carousel breakdowns, visual framing prompts, multimedia guidelines.
5. **Publishing & Social Agent:** Channel-specific formatting, publishing scheduling, link optimization.
6. **Reviews & Reputation Agent:** Sentiment analysis, public response drafting, escalation warnings.
7. **Leads & Conversations Agent:** High-intent lead scoring, direct message outreach drafting.
8. **Results & ROI Agent:** Deterministic performance synthesis, ROAS calculation, executive summaries.

### Reliability Mechanisms Verified:
- **Lazy Dependency Loading:** Import time for neural network libraries (`torch`, `sentence_transformers`, `chromadb`) dropped from 35.5s to 1.66s.
- **OpenBLAS Single-Thread Guardrail:** Thread allocation contention resolved (`OPENBLAS_NUM_THREADS=1`), eliminating Windows memory allocation errors.
- **Fail-Closed Governance Sentinel:** Tasks cannot bypass permissions, killswitch status, or daily budget caps.
- **Automated Test Isolation:** `AISMA_TEST_MODE=true` mocks neural network downloads and Ollama generation during automated test suites, preventing GPU lock contention while preserving real inference paths in development and production.
