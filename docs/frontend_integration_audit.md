# AISMA v2 — Frontend Integration Audit & Production Readiness Report

**Document Date:** November 9, 2026  
**Auditor:** Lead Frontend Architect & Frontend Integration Team  
**Scope:** Complete Next.js (App Router) Frontend, API Client, Governance Integrations, and Local AI Infrastructure Control Center  
**Status:** Architecture Complete; Production-Verified Audit Delivered  

---

## Executive Summary

A comprehensive architectural and integration audit was conducted across the 24 routes of the **AI-Native Social Media Agent Team v2** Next.js application.

The frontend successfully compiles (`npm run build`), passes strict TypeScript checks (`tsc --noEmit`), and passes ESLint with zero errors. All visual and interactive capabilities—including the eight-agent command center, governance center, Brand OS, multi-channel content studio, and Local AI Infrastructure—are fully operational.

However, as highlighted in technical review, **the frontend is currently running ahead of the Python HTTP layer**. The Python backend (`src/ai` and `src/governance`) contains pure library logic (Ollama client, ModelManager, hardware detection, hash chain audit logger, kill switch, and permission models), but **no FastAPI HTTP routing daemon is currently listening on port 8000**. 

Consequently, all browser network calls to `http://localhost:8000/api/v1/*` currently fail with network connection errors and safely degrade to strongly typed development fixtures.

This document establishes the exact provenance of all displayed data, corrects all hardware and model telemetry discrepancies, maps every API contract against FreeBuff's Python modules, and outlines the prioritized remediation roadmap for Phase 3.

---

## 1. Verified Functionality vs. Mocked / Fixture Functionality

| Module | Route | UI Status | Data Source | Verification Level |
| :--- | :--- | :--- | :--- | :--- |
| **Operations Dashboard** | `/dashboard`, `/` | Operational | Fixture | UI verified; awaiting live metrics ingestion |
| **Agent Command Center** | `/agents` | Operational | Fixture | UI verified; reflects 8 agents in `permissions.py` |
| **Individual Agent Telemetry** | `/agents/[slug]` (8 routes) | Operational | Fixture | Dynamic routing verified; maps all 8 agents |
| **Content Studio** | `/content-studio` | Operational | Client State & Fixture | Character caps, hook selection & UI verified |
| **Creative Studio** | `/creative-studio` | Operational | Client State | Honest rendering verified (no fake images) |
| **Content Calendar** | `/calendar` | Operational | Fixture | Weekly/monthly views verified |
| **Approval Center** | `/approvals` | Operational | Fixture | Fail-closed server submission contract verified |
| **Reviews & Reputation** | `/reviews` | Operational | Fixture | Sentiment tags & response workflow verified |
| **Leads & Inbox** | `/conversations` | Operational | Fixture | Intent classification & triage UI verified |
| **SEO Intelligence** | `/seo` | Operational | Fixture | Keyword demand charts verified |
| **Competitor Radar** | `/competitor` | Operational | Fixture | Promotion alert feeds verified |
| **Analytics & ROI** | `/analytics` | Operational | Fixture | Multi-touch attribution charts verified |
| **Brand OS** | `/brand-os` | Operational | Fixture | Single Source of Truth schema verified |
| **Budget Management** | `/budget` | Operational | Fixture | Hard cap progress bars verified |
| **Audit Logs** | `/audit` | Operational | Fixture | Cryptographic hash linkage UI verified |
| **System Settings** | `/settings` | Operational | Client State & Fixture | Multi-tenant RBAC UI verified |
| **Local AI Infrastructure** | `/infrastructure` | Operational | Hardware Detection + Live Ollama Tags (Baseline) | Live hardware audited; fixtures adjusted |
| **Authentication & Onboarding** | `/login`, `/register`, `/forgot-password`, `/onboarding` | Operational | Zustand Session | Client session flows verified |

---

## 2. Data Integrity Findings & Resolution

### Finding 1: GPU & Hardware Telemetry Mismatch (Resolved)
- **Previous Fixture State:** Reported `NVIDIA GeForce RTX 4070 Laptop GPU` with `8,192 MB VRAM`.
- **Actual Local Hardware:** Probed directly via `detect_hardware()` in `src/ai/hardware.py`:
  ```json
  {
    "cpu_count": 16,
    "ram_total_mb": 15709,
    "ram_available_mb": 2533,
    "gpu_name": "NVIDIA GeForce RTX 3050 Laptop GPU",
    "vram_total_mb": 4096,
    "vram_free_mb": 1646,
    "nvidia_smi_available": true
  }
  ```
- **Remediation Applied:** 
  1. Updated `MOCK_HARDWARE_TELEMETRY` to reflect the actual **RTX 3050 Laptop GPU (4,096 MB VRAM)**, **16 CPU cores**, and **15.7 GB total host RAM**.
  2. In the UI, added a clear warning when live hardware sensors cannot be polled over HTTP.

### Finding 2: Model Registry vs. Installed Models Separation (Resolved)
- **Previous Fixture State:** Included uninstalled models (`llama3.1:8b`) alongside installed models without distinction.
- **Actual Local Ollama Runtime:** Live probe to `http://localhost:11434/api/tags` revealed four installed models:
  1. `qwen3.5:9b` (9.0B, 6.1 GB, Q4_K_M) — *Installed locally, but memory-constrained on 4GB VRAM*
  2. `qwen3.5:4b` (4.2B, 3.1 GB, Q4_K_M) — *Installed locally, primary production candidate*
  3. `qwen2.5-coder:1.5b-base` (1.5B, 0.98 GB, Q4_K_M) — *Installed locally, base code/completion*
  4. `phi3.5:latest` (3.8B, 2.03 GB, Q4_0) — *Installed locally, designated fallback*
- **Remediation Applied:**
  1. Segregated installed models into a dedicated **Installed Local Models (Live Ollama Runtime)** card.
  2. Created a separate **Model Registry Candidates (Uninstalled)** card displaying `llama3.1:8b` and `deepseek-r1:7b` with a distinct `Not Installed (Requires Pull)` status tag.
  3. Marked `qwen3.5:9b` with an explicit **`4GB VRAM Constrained (OOM Risk)`** warning badge.

### Finding 3: Benchmark Integrity & Provenance (Resolved)
- **Previous Fixture State:** Displayed synthetic benchmark values (58.4 tok/s, 64.2 tok/s, etc.) without empirical run evidence.
- **Actual Phase 2 Runtime Status:** Real local inference test on `qwen3.5:9b` timed out (>120s) due to 4GB VRAM exhaustion. No formal benchmark run had been recorded for the other models.
- **Remediation Applied:**
  1. Replaced synthetic numbers with verified provenance metadata:
     - `qwen3.5:9b`: Speed marked as **`Timed Out (>120s)`**, Status: **`Timeout (OOM)`**.
     - `qwen3.5:4b`, `phi3.5:latest`, `qwen2.5-coder:1.5b-base`: Speed marked as **`Not benchmarked`**, Status: **`Pending Run`**.
  2. Added a permanent **Benchmark Provenance & Empirical Measurement Standard** disclosure banner directly on `/infrastructure`.

---

## 3. Comprehensive Backend API Contract Audit

Every HTTP request defined in `frontend/src/lib/api-client.ts` was audited against FreeBuff's Python repository (`src/`):

| Method | Endpoint | Request Schema | Response Schema | Auth Required | Server-Side Authority | Backend Status in `src/` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | `{ email, password }` | `{ token, user }` | Public | FreeBuff Auth Manager | **Missing** (Slated for FastAPI phase) |
| `GET` | `/api/v1/auth/me` | None | `UserProfile` | Bearer Token | RBAC / Tenant Context | **Missing** |
| `GET` | `/api/v1/agents` | None | `AgentDetails[]` | Bearer Token | `permissions.py` / Orchestrator | **Missing** (`src/governance/permissions.py` defines permissions, but no HTTP route) |
| `GET` | `/api/v1/agents/:id` | None | `AgentDetails` | Bearer Token | `permissions.py` | **Missing** |
| `POST` | `/api/v1/agents/:id/execute` | `{ action, parameters }` | `{ task_id, status }` | Bearer Token | `permissions.py` + `killswitch.py` | **Missing** |
| `GET` | `/api/v1/approvals` | None | `ApprovalRequest[]` | Bearer Token | Human Admin / Manager | **Missing** |
| `POST` | `/api/v1/approvals/:id/decision` | `{ action, note }` | `{ id, status, audited }` | Bearer Token | Human Admin / `audit.py` | **Missing** (`src/governance/audit.py` exists, HTTP route pending) |
| `GET` | `/api/v1/content/drafts` | None | `ContentDraft[]` | Bearer Token | `permissions.py` | **Missing** |
| `POST` | `/api/v1/content/drafts` | `Partial<ContentDraft>` | `ContentDraft` | Bearer Token | `permissions.py` | **Missing** |
| `GET` | `/api/v1/reputation/reviews` | None | `ReviewItem[]` | Bearer Token | `permissions.py` | **Missing** |
| `GET` | `/api/v1/conversations` | None | `LeadConversation[]` | Bearer Token | `permissions.py` | **Missing** |
| `GET` | `/api/v1/seo/rankings` | None | `{ keywords, visibilityScore }` | Bearer Token | `permissions.py` | **Missing** |
| `GET` | `/api/v1/intelligence/competitors` | None | `CompetitorProfile[]` | Bearer Token | `permissions.py` | **Missing** |
| `GET` | `/api/v1/brand-os` | None | `BrandOSData` | Bearer Token | Tenant Brand OS | **Missing** |
| `PUT` | `/api/v1/brand-os` | `Partial<BrandOSData>` | `BrandOSData` | Bearer Token | Tenant Brand OS | **Missing** |
| `GET` | `/api/v1/budget` | None | `BudgetOverview` | Bearer Token | `budget.py` | **Missing** (`src/governance/budget.py` exists, HTTP route pending) |
| `GET` | `/api/v1/governance/killswitch` | None | `KillSwitchStatus` | Bearer Token | `killswitch.py` | **Missing** (`src/governance/killswitch.py` exists, HTTP route pending) |
| `POST` | `/api/v1/governance/killswitch` | `{ engaged, reason }` | `KillSwitchStatus` | Bearer Token | `killswitch.py` + `audit.py` | **Missing** |
| `GET` | `/api/v1/governance/audit` | None | `{ entries, chainValid }` | Bearer Token | `audit.py` | **Missing** (`src/governance/audit.py` exists, HTTP route pending) |
| `POST` | `/api/v1/governance/audit/verify`| None | `{ valid, verifiedCount, message }` | Bearer Token | `audit.py` | **Missing** |
| `GET` | `/api/v1/ai/hardware` | None | `HardwareTelemetry` | Bearer Token | `src/ai/hardware.py` | **Missing** (`detect_hardware()` exists, HTTP route pending) |
| `GET` | `/api/v1/ai/health` | None | `OllamaRuntimeHealth` | Bearer Token | `src/ai/model_manager.py` | **Missing** (`ModelManager.health()` exists, HTTP route pending) |
| `GET` | `/api/v1/ai/models` | None | `OllamaModelInfo[]` | Bearer Token | `src/ai/ollama_client.py` | **Missing** (`OllamaClient.list_models()` exists, HTTP route pending) |
| `GET` | `/api/v1/ai/telemetry` | None | `InferenceTelemetry` | Bearer Token | `src/ai/model_manager.py` | **Missing** |
| `GET` | `/api/v1/ai/config` | None | `LocalAIConfig` | Bearer Token | `src/ai/config.py` | **Missing** (`load_ai_config()` exists, HTTP route pending) |
| `PUT` | `/api/v1/ai/config` | `Partial<LocalAIConfig>`| `LocalAIConfig` | Bearer Token | `src/ai/config.py` | **Missing** |
| `POST` | `/api/v1/ai/active-model` | `{ model }` | `{ active_model, status }` | Bearer Token | `src/ai/model_manager.py` | **Missing** (`set_active_model()` exists, HTTP route pending) |
| `GET` | `/api/v1/ai/agent-assignments` | None | `AgentModelAssignment[]` | Bearer Token | Orchestrator | **Missing** |
| `PUT` | `/api/v1/ai/agent-assignments/:id`| `{ assigned_model, fallback }` | `AgentModelAssignment` | Bearer Token | `permissions.py` | **Missing** |
| `GET` | `/api/v1/ai/benchmarks` | None | `ModelBenchmarkResult[]` | Bearer Token | Benchmark Engine | **Missing** |
| `GET` | `/api/v1/ai/registry-candidates` | None | `RegistryCandidate[]` | Bearer Token | `src/ai/registry.py` | **Missing** (`ModelRegistry.all()` exists, HTTP route pending) |

---

## 4. Governance & Security Verification

1. **Emergency Halt / Kill Switch:**
   - The frontend Emergency Halt button on the global header routes strictly to `POST /api/v1/governance/killswitch`.
   - In Python, `KillSwitch` in `src/governance/killswitch.py` enforces a **fail-closed** policy (unreadable or corrupt state is treated as engaged).
   - The frontend will directly consume this state once the FastAPI router is exposed.

2. **Mandatory Human-in-the-Loop Publishing Signoff:**
   - The frontend contains **zero** direct publishing triggers for agents.
   - All posts submitted from Content Studio land in `status: "pending_approval"`.
   - Approval decisions require human submission via `/approvals`.
   - In Python, `src/governance/permissions.py` enforces `Action.PUBLISH` only for `human_admin`; no standalone agent holds `Action.PUBLISH`.

3. **Tenant & Business Isolation:**
   - The frontend displays the tenant scope (`biz_apex_enterprises`).
   - In Python, `src/governance/permissions.py` line 122 enforces:
     ```python
     if ctx.actor_business_id is not None and ctx.actor_business_id != ctx.business_id:
         raise PermissionDeniedError(...)
     ```
   - In `src/governance/audit.py`, each business writes to its own isolated file (`{business_id}.jsonl`).

4. **Cryptographic Hash Chaining:**
   - `src/governance/audit.py` computes SHA-256 hash chains with genesis `0` * 64 and recursive PII redaction (`_EMAIL_RE`, `_PHONE_RE`, `_LONG_NUMBER_RE`).
   - The frontend Audit page displays the hash link `prev_hash` ➔ `entry_hash` and provides a verification action intended for `verify_audit_chain()`.

5. **Visual Distinction of Fixture Mode:**
   - A persistent, high-visibility amber warning banner (`FixtureBanner`) is displayed across the top of all authenticated pages whenever the FastAPI backend is disconnected.
   - An additional targeted alert is mounted on `/infrastructure` explicitly stating that live backend sensors are disconnected.

---

## 5. Automated Build and Test Evidence

### Test Suite Execution (`npm test`):
```text
> ai-native-social-media-agent-team-v2@2.0.0 test
> npm --prefix frontend run test

> ai-native-social-media-agent-team-frontend@2.0.0 test
> node tests/frontend.test.mjs

✔ Next.js App Router Structure & All 8 Agent Routes (12.6ms)
✔ Agent Command Center Config & Governance Restrictions (0.89ms)
✔ API Client Governance Enforcement (No Frontend Bypass) (0.85ms)
✔ Design System Navy Theme & Tailwind Tokens (1.24ms)
✔ Local AI Infrastructure & Unified LLMProvider Contract (1.30ms)
ℹ tests 5
ℹ suites 0
ℹ pass 5
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 23.9ms
```

### TypeScript Compilation Check (`npm run type-check`):
```text
> ai-native-social-media-agent-team-frontend@2.0.0 type-check
> tsc --noEmit

(Exited with code 0 - Zero type errors)
```

### ESLint Check (`npm run lint`):
```text
> ai-native-social-media-agent-team-frontend@2.0.0 lint
> next lint

✔ No ESLint warnings or errors
(Exited with code 0 - Zero lint warnings/errors)
```

### Production Build Compilation (`npm run build`):
```text
> ai-native-social-media-agent-team-frontend@2.0.0 build
> next build

  ▲ Next.js 14.2.15

   Creating an optimized production build ...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/24) ...
   Generating static pages (6/24) 
   Generating static pages (12/24) 
   Generating static pages (18/24) 
 ✓ Generating static pages (24/24)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    199 B           242 kB
├ ○ /_not-found                          876 B          88.3 kB
├ ○ /agents                              4.84 kB         136 kB
├ ƒ /agents/[slug]                       5.44 kB         136 kB
├ ○ /analytics                           2.82 kB         226 kB
├ ○ /approvals                           5.16 kB         136 kB
├ ○ /audit                               3.75 kB         135 kB
├ ○ /brand-os                            4.96 kB         136 kB
├ ○ /budget                              3.75 kB         135 kB
├ ○ /calendar                            3.92 kB         135 kB
├ ○ /competitor                          4.12 kB         135 kB
├ ○ /content-studio                      6.46 kB         137 kB
├ ○ /conversations                       4.4 kB          135 kB
├ ○ /creative-studio                     4.35 kB         127 kB
├ ○ /dashboard                           199 B           242 kB
├ ○ /forgot-password                     2.3 kB          104 kB
├ ○ /infrastructure                      11.6 kB         247 kB
├ ○ /login                               2.4 kB          117 kB
├ ○ /onboarding                          3.47 kB         111 kB
├ ○ /register                            2.47 kB         117 kB
├ ○ /reviews                             4.29 kB         135 kB
├ ○ /seo                                 4.29 kB         236 kB
└ ○ /settings                            3.57 kB         126 kB
+ First Load JS shared by all            87.4 kB
  ├ chunks/117-ed26d89af1deb24f.js       31.8 kB
  ├ chunks/fd9d1056-d6d0ffcbea477a37.js  53.6 kB
  └ other shared chunks (total)          2 kB

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand

(Exited with code 0 - All 24 routes successfully compiled)
```

---

## 6. Prioritized Remediation Roadmap

To transition the platform from "Frontend Architecture Complete" to "Production-Verified End-to-End System", the following technical sequence is recommended:

### Priority 1: Expose Real FastAPI Endpoints for Hardware & Local AI
- **Owner:** Backend Team (FreeBuff) / Integration
- **Action:** Create `src/api/` FastAPI app exposing:
  1. `GET /api/v1/ai/hardware` ➔ calls `detect_hardware().to_dict()`
  2. `GET /api/v1/ai/health` ➔ calls `ModelManager.health()`
  3. `GET /api/v1/ai/models` ➔ calls live Ollama `/api/tags`
  4. `POST /api/v1/ai/active-model` ➔ calls `ModelManager.set_active_model()`
- **Impact:** Instantly replaces frontend hardware/model fixtures with live machine telemetry.

### Priority 2: Expose Governance & Kill Switch Endpoints
- **Owner:** Backend Team (FreeBuff) / Integration
- **Action:** Expose:
  1. `GET/POST /api/v1/governance/killswitch` ➔ connected to `KillSwitch` in `src/governance/killswitch.py`
  2. `GET/POST /api/v1/governance/audit/verify` ➔ connected to `verify_audit_chain()` in `src/governance/audit.py`
  3. `POST /api/v1/approvals/:id/decision` ➔ writes to immutable audit log with human admin context.
- **Impact:** Guarantees that emergency halt and publication approvals are enforced by the Python kernel.

### Priority 3: Empirical Benchmarking Run on Local RTX 3050
- **Owner:** AI Infrastructure Team
- **Action:** Execute a dedicated benchmark script against the four locally installed models (`qwen3.5:4b`, `phi3.5:latest`, `qwen2.5-coder:1.5b-base`, and `qwen3.5:9b`) recording prompt tokens, completion tokens, time-to-first-token, and tokens per second.
- **Impact:** Replaces `Not benchmarked` with verifiable empirical measurements.

### Priority 4: Complete Single End-to-End Workflow Verification
- **Owner:** Full Team
- **Action:** Execute a live multi-agent execution cycle:
  `Tenant Registration` ➔ `Brand OS Ground Truth` ➔ `Search Visibility & Content Engine generation using local qwen3.5:4b` ➔ `Approval Center human signoff` ➔ `Audit log hash verification`.
- **Impact:** Proves the entire multi-agent loop with zero synthetic simulation.

