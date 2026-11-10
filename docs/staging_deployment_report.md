# AISMA v2 — Local Staging Deployment Validation Report

**Date:** November 10, 2026  
**Environment:** Local Development Workstation (Windows 11, Python 3.12.7, Node 24.13.0 / Next.js 14.2.15, Ollama local runtime)  
**Restriction:** Local development mode strictly enforced — zero public exposure, zero cloud deployment.  

---

## 1. Local Service & Infrastructure Inventory

| Service | Configuration / Artifact | Local Test Status | Actual Observed Evidence |
| :--- | :--- | :--- | :--- |
| **FastAPI Backend (`127.0.0.1:8000`)** | `src/api/main.py` | **PASSED (Live HTTP)** | Booted locally on loopback `127.0.0.1:8000`; `/api/v1/ready` returned `200 OK`; all 17 API journey steps succeeded. |
| **Next.js Frontend (`127.0.0.1:3000`)** | `frontend/` (`npm run start`) | **PASSED (Live HTTP)** | Booted locally on `127.0.0.1:3000`; 8 core routes (`/`, `/dashboard`, `/agents`, `/approvals`, `/analytics`, `/infrastructure`, `/onboarding`, `/login`) returned `200 OK` (3.75ms–51.65ms). |
| **Local Ollama Runtime (`127.0.0.1:11434`)** | `src/ai/ollama_client.py` | **PASSED (Live Inference)** | Reachable on `127.0.0.1:11434`; models detected (`phi3.5:latest`, `qwen3.5:4b`, `qwen3.5:9b`, `qwen2.5-coder:1.5b-base`). Both real Ollama tests passed (`2 passed in 36.07s`). |
| **Docker Engine** | `docker-compose.yml`, `Dockerfile.*` | **Blocked (Daemon Not Running)** | `Docker version 29.6.2` CLI installed, but Docker Desktop engine pipe (`dockerDesktopLinuxEngine`) was inactive on this host. |
| **PostgreSQL 16** | `src/db/database.py`, `migrations/` | **Blocked (No Live Daemon)** | `psql` not installed locally and Docker Desktop daemon offline; live PostgreSQL 16 execution awaits Docker Desktop startup. |

---

## 2. Live Defect Discovered & Fixed During Staging Validation
- **Defect:** Real Ollama inference test `test_real_ollama_generate_smoke` failed on `qwen3.5:4b` with empty output (`text=''`) when `max_tokens=32` because `qwen3.5` consumed all tokens inside internal `thinking` mode.
- **Fix Applied (`src/ai/ollama_client.py`):** Added `"think": False` for `qwen3*` models in `generate()` and `chat()`.
- **Verification:** Re-ran `AISMA_TEST_MODE="false" AISMA_RUN_REAL_OLLAMA_TESTS="1" pytest tests/ai/test_real_ollama_optional.py tests/integration/test_real_ollama_phase3_optional.py` -> **2 passed in 36.07s**.

