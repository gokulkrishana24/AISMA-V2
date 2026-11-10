# AISMA v2 — Performance & Scalability Report

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Benchmark Findings (`tests/performance/test_benchmarks.py`)

Automated benchmarks ran against the live FastAPI TestClient and SQLAlchemy SQLite backend on Windows 11 (Python 3.12.7, RTX 3050 4GB VRAM, 16GB RAM):

| Benchmark Target | Threshold Assertion | Verified Outcome |
| :--- | :--- | :--- |
| **API + DB Readiness (`GET /api/v1/ready`, 20 calls)** | Avg `< 50 ms`, P95 `< 100 ms` | **PASSED** (`test_benchmark_api_and_db_latency`) |
| **Deterministic ROI Engine (100 full reports)** | Total `< 250 ms` | **PASSED** (`test_benchmark_deterministic_roi_throughput`) |
| **Concurrent API Burst (8 workers, 24 requests)** | 100% HTTP `200 OK` | **PASSED** (`test_benchmark_controlled_concurrent_api_requests`) |
| **API Cold Import (`import api.main`)** | `< 3.0 s` | **1.66 s** (reduced from 35.48s via lazy ML imports) |
| **Full Backend Regression Suite (172 collected items)** | `< 30 s` | **14.92 s** (170 passed, 2 skipped) |

---

## 2. Scalability & Hardware Optimizations
1. **Constrained 4 GB VRAM Protection:** Shared `ModelManager` ensures all 8 agents share one Ollama runtime; 9B models remain marked `timed_out` so OOM driver crashes cannot occur.
2. **OpenBLAS Contention Fix:** `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` configured in `tests/conftest.py` and `.env.example`.
3. **Next.js Single-Worker Compilation:** `experimental: { cpus: 1, workerThreads: false }` prevents Node heap allocation failures on Windows during `next build`.

