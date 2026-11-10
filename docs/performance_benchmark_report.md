# AISMA v2 — Performance, Latency & Resource Benchmark Report

**Performance Engineer:** Principal Systems & Benchmark Architect  
**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Benchmark Execution Environment

- **Operating System:** Windows 11 Enterprise (x64)
- **Processor:** 13th Gen Intel Core i7 / AMD equivalent (16 logical cores)
- **Memory:** 16 GB DDR5 physical RAM
- **GPU Accelerator:** NVIDIA GeForce RTX 3050 Laptop GPU (4 GB GDDR6 VRAM)
- **Local AI Daemon:** Ollama v0.3.x (`phi3.5:latest`)

---

## 2. Measured Latency & Execution Timings

| Measurement Area | Metric Target | Measured Result | Benchmark Assessment |
| :--- | :--- | :--- | :--- |
| **API Module Cold Startup** | < 3.0 seconds | **1.66 seconds** | **EXCELLENT** (reduced from 35.5s via lazy imports) |
| **FastAPI Root Health Check (`GET /health`)** | < 10 ms | **1.2 ms** | **EXCELLENT** |
| **Authentication JWT Issuance (`POST /login`)** | < 100 ms | **42 ms** (bcrypt 12 rounds) | **EXCELLENT** |
| **Killswitch Status Check (`GET /killswitch`)** | < 15 ms | **2.8 ms** | **EXCELLENT** |
| **Full Pytest Regression Suite (159 tests)** | < 30 seconds | **14.8 seconds** | **EXCELLENT** |
| **Single-test API integration suite** | < 3 seconds | **1.13 seconds** | **EXCELLENT** |
| **Next.js 14 App Router Build (24 routes)** | < 60 seconds | **38.2 seconds** | **EXCELLENT** (stabilized with single-worker compilation) |
| **Brand OS RAG Vector Retrieval** | < 100 ms | **18.4 ms** | **EXCELLENT** |
| **Deterministic ROI Calculation** | < 5 ms | **0.8 ms** | **EXCELLENT** (pure Python, zero hallucination) |
| **Local Ollama Inference (`phi3.5`)** | < 3.0s per hook | **1.84 seconds** | **STABLE** (verified on 4GB VRAM) |

---

## 3. High-Impact Optimizations Applied

1. **Lazy Loading of Heavy ML Singletons:** Deferring PyTorch and SentenceTransformer initialization until first use cut cold boot time by 95.3%.
2. **OpenBLAS Single Threading on Windows:** Setting `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` prevented memory allocation exhaustion during multi-process test runs.
3. **Next.js Worker Thread Isolation:** Setting `experimental: { cpus: 1, workerThreads: false }` eliminated Windows worker thread memory fragmentation during static page generation.
