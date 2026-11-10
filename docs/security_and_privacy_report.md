# AISMA v2 — Security & Privacy Acceptance Report

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Security Controls Implemented & Verified

| Security Domain | Mechanism | Verification Evidence |
| :--- | :--- | :--- |
| **Authentication & Lifecycle** | bcrypt (12 rounds), HS256 JWT access tokens (`24h`) + refresh tokens (`7d`), `jti` revocation on `/logout`, non-enumerating `/forgot-password`. | `tests/integration/test_auth_rbac_isolation.py`, `tests/integration/test_modernization_and_ops.py` |
| **Tenant Isolation & RBAC** | `require_tenant_access` checks `Membership` table for `X-Business-Id`; `require_platform_admin` guards `/api/v1/admin/*`. | Cross-tenant requests return `403 Forbidden`; non-admin access to `/admin/overview` returns `403`. |
| **Rate Limiting & CORS** | `RateLimitMiddleware` (30 req/min on `/api/v1/auth/*`, 300 req/min default) returning `429` + `Retry-After`; environment-specific `CORS_ALLOWED_ORIGINS` (no wildcard with credentials). | `test_rate_limiter_enforces_429` passed (`429` verified). |
| **OAuth & Webhook Integrity** | CSPRNG OAuth CSRF `state` verification + `CredentialVault` Fernet encryption at rest; HMAC-SHA256 webhook verification (`X-AISMA-Signature`). | `test_oauth_csrf_state_and_webhook_hmac` passed. |
| **Prompt Injection & Killswitch** | `scan_untrusted_text` flags injection patterns + wraps with `<UNTRUSTED_TEXT>`; `KillSwitch` blocks approvals and post scheduling when engaged. | `tests/security/test_security_acceptance.py` (4 passed). |
| **Container & Network Hardening** | Non-root `aisma` user (`Dockerfile.backend`), non-root `nextjs` user (`Dockerfile.frontend`), Ollama exposed only internally on `aisma-net`. | Verified in `Dockerfile.backend`, `docker-compose.yml`. |

---

## 2. Privacy & Data Portability (`src/api/routers/privacy.py`)

- **Data Export (`GET /api/v1/privacy/export`):** Exports user profile, tenant approvals, content drafts, Brand OS context, and audit logs in structured JSON.
- **Account Erasure (`DELETE /api/v1/privacy/account`):** Deactivates user account (`is_active = False`), logs `account_deletion_scheduled` to SHA-256 audit ledger with 30-day retention window.
- **Compliance Note:** Engineering primitives for data portability and erasure are implemented; formal legal/GDPR/SOC2 compliance requires external organizational policy review and legal sign-off.

