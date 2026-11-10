# AISMA v2 — Deployment, Infrastructure & Operations Report

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Container & Orchestration Readiness

| Artifact | Purpose | Hardening & Verification |
| :--- | :--- | :--- |
| `Dockerfile.backend` | Python 3.12-slim FastAPI image | Non-root user `aisma` (UID 1001), includes Alembic & `psycopg2-binary`, healthcheck on `/api/v1/ready`. |
| `Dockerfile.frontend` | Multi-stage Node 20-alpine Next.js runner | Non-root user `nextjs`, healthcheck on `http://localhost:3000`. |
| `docker-compose.yml` | Multi-service topology (`postgres`, `backend`, `frontend`, `ollama`) | `postgres` healthcheck dependency, `ollama` isolated internally (`expose: 11434`, no public host port), backend bound to `127.0.0.1:8000`. |
| `.github/workflows/ci.yml` | Automated CI/CD pipeline | Parallel Python (Ruff + Pytest) and Frontend (`tsc`, ESLint, unit tests, `next build`) jobs. |
| `.env.example` | Environment template | Documents DB URL, secrets, CORS origins, Ollama host, and OAuth credentials. |

---

## 2. Database Backup, Restoration & Readiness

- **Backup & Restore Automation (`scripts/backup_restore.py`):** Uses SQLite's online `backup()` API, writes a SHA-256 checksum manifest JSON, and verifies restored integrity via `PRAGMA integrity_check;`. Verified passing in `tests/integration/test_modernization_and_ops.py::test_database_backup_and_restore_integrity`.
- **PostgreSQL Infrastructure Limitation:** Local Windows environment lacks a running PostgreSQL server instance; SQLAlchemy 2 + Alembic + `psycopg2-binary` configurations and `docker-compose.yml` are ready, but live PostgreSQL container execution must be verified on a Docker host before public launch.

