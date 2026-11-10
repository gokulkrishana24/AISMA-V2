# AISMA v2 — Security & Deployment Acceptance Report

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Production Fail-Closed Configuration Guard (`src/api/main.py`)

Verified via `tests/integration/test_modernization_and_ops.py::test_production_security_fail_closed_guard`:
- When `AISMA_ENV=production`:
  - Short or default `JWT_SECRET_KEY` raises `RuntimeError: SECURITY BLOCK`.
  - Default `INTEGRATION_VAULT_SECRET` raises `RuntimeError: SECURITY BLOCK`.
  - Wildcard `*` inside `CORS_ALLOWED_ORIGINS` raises `RuntimeError: SECURITY BLOCK`.
- Production mode cannot silently fall back to development credentials.

---

## 2. Deployment & Network Boundary Checklist

| Boundary Control | Configuration | Status |
| :--- | :--- | :--- |
| **PostgreSQL Network** | `docker-compose.yml` (`aisma-net` internal-only, no `ports`) | **Isolated** |
| **Ollama Inference Service** | `docker-compose.yml` (`expose: 11434` internal-only, no `ports`) | **Isolated** |
| **Backend Container Privileges** | `Dockerfile.backend` (`USER aisma`, UID 1001) | **Non-Root** |
| **Frontend Container Privileges** | `Dockerfile.frontend` (`USER nextjs`, UID 1001) | **Non-Root** |
| **Rate Limiting & Correlation** | `src/api/middleware.py` (`429`, `X-Correlation-ID`) | **Verified** |
| **Token Revocation & CSRF/HMAC** | `auth.py`, `integrations.py`, `billing.py` | **Verified** |

