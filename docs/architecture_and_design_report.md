# AISMA v2 — System Architecture & Design Report

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Layered Modular Architecture

AISMA v2 uses a modular monolith backend coupled with a Next.js App Router frontend, optimizing for low latency, deterministic governance, and constrained local GPU execution (4 GB VRAM).

```text
+-------------------------------------------------------------------+
|                  Next.js 14.2 Enterprise UI (Port 3000)           |
|     24 Routes | TypeScript Strict | Typed ApiClient | Dark Navy   |
+-------------------------------------------------------------------+
                                  |
                     HTTPS / REST + Bearer JWT + X-Business-Id
                                  v
+-------------------------------------------------------------------+
|               FastAPI Gateway & Middleware (Port 8000)            |
|  CORS Lockdown | Sliding-Window Rate Limiter | X-Correlation-ID   |
|  14 Routers: auth, ai, agents, approvals, governance, content,    |
|  brand, budget, marketing, integrations, campaigns, analytics,    |
|  onboarding, organizations, billing, notifications, support,      |
|  privacy, admin, scheduler                                        |
+-------------------------------------------------------------------+
         |                        |                        |
         v                        v                        v
+------------------+   +---------------------+   +------------------+
| Governance Core  |   | Multi-Agent & RAG   |   | Persistence & BI |
| - Default-Deny   |   | - 8 Marketing Agents|   | - SQLAlchemy 2   |
| - Budget Limits  |   | - Central Orchestr. |   | - Alembic Schema |
| - Kill Switch    |   | - Brand OS (27 tmpl)|   | - Deterministic  |
| - SHA-256 Audit  |   | - Ollama (phi3.5)   |   |   ROI/ROAS Calc  |
| - Prompt Scanner |   | - ChromaDB Vector   |   | - Fernet Vault   |
+------------------+   +---------------------+   +------------------+
```

---

## 2. Core Architectural Invariants

1. **Governance Authority in Python:** Agents and LLMs never bypass `PermissionManager`, `BudgetEnforcer`, `KillSwitch`, or `PolicyEngine`.
2. **Strict Tenant Isolation:** Every multi-tenant resource and endpoint validates `business_id` membership via `require_tenant_access` (`X-Business-Id`). Cross-tenant requests return `403 Forbidden`.
3. **Deterministic Financial Analytics:** `DeterministicROIEngine` (`src/analytics/roi.py`) executes pure mathematical formulas; AI models explain results but never generate financial figures.
4. **Shared Single-Instance AI Serving:** All 8 agents share one `LLMProvider` instance to avoid spawning competing GPU processes on 4 GB VRAM hardware.

