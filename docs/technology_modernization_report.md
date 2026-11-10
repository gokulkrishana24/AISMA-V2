# AISMA v2 — Technology Modernization Report

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Stack Inventory & Modernization Evaluation

| Component | Verified Version / Tech | Modernization Applied | Rationale & Impact |
| :--- | :--- | :--- | :--- |
| **Python Runtime** | Python 3.12.7 | Modernized type annotations (`from __future__ import annotations`, `datetime.UTC`), Ruff linting (`E, F, I, B, UP`). | Eliminates legacy Python 3.8–3.11 syntax and deprecated `datetime.timezone.utc` calls. |
| **Web Framework** | FastAPI + Uvicorn | Lifespan async context manager, correlation ID & timing middleware (`X-Correlation-ID`), sliding-window rate limiter. | Production-grade observability and brute-force protection without external Redis dependency for single-node deployments. |
| **ORM & Migrations** | SQLAlchemy 2.0.36 + Alembic 1.19.1 | Declarative `Mapped[T]` / `mapped_column`, dialect-agnostic SQLite/PostgreSQL URL handling, initial migration revision `62492e17008c`. | Full type safety, cascading multi-tenant deletes, and reversible schema evolution. |
| **Auth & Crypto** | PyJWT (HS256) + bcrypt + cryptography (Fernet) | Dual access/refresh token workflow (`token_use`), `jti` revocation store on logout, 12-round bcrypt hashing, Fernet encrypted token vault. | Prevents token replay after logout and secures OAuth credentials at rest. |
| **Frontend Stack** | Next.js 14.2.15, React 18.3.1, TypeScript 5.6.3, Tailwind 3.4.14 | App Router, single-worker stability setting (`cpus: 1, workerThreads: false`) for constrained memory builds, typed `ApiClient`. | Clean 24-route production compilation with zero TypeScript or ESLint errors. |
| **Local AI & RAG** | Ollama (`phi3.5:latest`), SentenceTransformers, ChromaDB | Lazy singleton imports (`api.main` cold import cut from 35.48s to 1.66s) + `OPENBLAS_NUM_THREADS=1`. | Prevents Windows OpenBLAS memory allocation crashes and 4GB VRAM OOM failures. |
| **Container & CI/CD** | Docker Compose, Python 3.12-slim, Node 20-alpine, GitHub Actions | Non-root `aisma` (UID 1001) backend container, `nextjs` non-root frontend container, isolated internal Ollama network, PostgreSQL 16 service. | Enforces least-privilege execution and isolates internal AI inference from public interfaces. |

---

## 2. Rejected Unnecessary Complexity
Per Section 4 guidelines ("Do not introduce microservices, Redis, Kafka, Kubernetes or additional frameworks without a demonstrated requirement"):
- **Kafka / RabbitMQ:** Rejected; local orchestrator priority queue and SQLAlchemy suffice for current single-host / vertical scale.
- **Kubernetes:** Rejected; Docker Compose provides deterministic multi-container operation without orchestration overhead.
- **External SaaS Auth (Auth0/Clerk):** Rejected; self-hosted bcrypt + PyJWT + RBAC keeps tenant data sovereign and zero-cost.

