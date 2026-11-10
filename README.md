# AI-Native Social Media Agent Team v2 (AISMA v2)

Enterprise, local-first, multi-tenant AI marketing operations platform powered by eight specialized agents, fail-closed governance, approved-only Brand OS RAG retrieval, deterministic Python analytics, and a Next.js 14 App Router dashboard.

---

## Key Capabilities

- **Eight Specialized Marketing Agents (`src/agents/`):** Search Visibility, Market Radar, Content Engine, Creative Studio, Publishing & Social, Reviews & Reputation, Leads & Conversations, and Results & ROI coordinated by a central Orchestrator (`src/orchestrator/`).
- **Local-First AI Infrastructure (`src/ai/`):** Unified `LLMProvider` targeting local Ollama (`phi3.5:latest`) with hardware detection (`detect_hardware()`), VRAM guardrails, CPU fallback, and lazy initialization.
- **Fail-Closed Python Governance Sentinel (`src/governance/`):** Default-deny permission matrix, hard daily budget caps, instant business killswitch, prompt-injection scanning (`scan_untrusted_text`), and cryptographic SHA-256 hash-chained audit logging.
- **27-Template Brand OS + RAG (`src/brand_os/`):** Document versioning, chunking, local `all-MiniLM-L6-v2` embeddings, ChromaDB vector persistence, and strict approved-only retrieval with `[MISSING]`/`[VERIFY]` placeholder enforcement.
- **Enterprise SaaS Platform (`src/api/`, `src/db/`, `src/services/`):** SQLAlchemy 2.0 ORM (PostgreSQL & SQLite), Alembic migrations (`migrations/`), bcrypt + JWT authentication (access & refresh tokens with logout revocation), strict `X-Business-Id` tenant isolation, sliding-window rate limiting, correlation IDs, subscription tiers, usage metering, onboarding, notifications, support tickets, GDPR export/erasure, and admin feature flags.
- **External Platform Adapters (`src/integrations/`):** Modular adapters for LinkedIn, Meta (Instagram/Facebook), X (Twitter), Google Search Console, Google Analytics 4, and Customer Reviews with Fernet-encrypted token storage, OAuth CSRF state flow, and HMAC-SHA256 webhook verification.
- **Deterministic ROI/ROAS Engine (`src/analytics/roi.py`):** Exact Python formulas for ROAS, ROI %, CAC, and LTV/CAC ratios with SHA-256 integrity hashing (zero LLM numerical fabrication).
- **Enterprise UI (`frontend/`):** Next.js 14.2 App Router, TypeScript strict, Tailwind CSS, dark navy design system, 24 routes, and transparent development-fixture banners when backend is offline.

---

## Quick Start

### 1. Environment Configuration
Copy `.env.example` to `.env` and configure your secrets and database URL:
```bash
cp .env.example .env
```

### 2. Backend Setup (Python 3.12+)
```bash
pip install -e ".[dev]"
pip install fastapi uvicorn[standard] sqlalchemy alembic psycopg2-binary bcrypt pyjwt cryptography email-validator httpx psutil pyyaml pydantic
set PYTHONPATH=src
python -m alembic upgrade head
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup (Node.js 20+)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

### 4. Production Docker Deployment
```bash
docker-compose up -d --build
```
Services started:
- `postgres`: PostgreSQL 16 (internal network)
- `backend`: FastAPI non-root container (`127.0.0.1:8000`)
- `frontend`: Next.js production container (`3000`)
- `ollama`: Local LLM runner (internal network only — never exposed publicly)

---

## Verification & Testing

```bash
# Backend Linter & Full Test Suite
python -m ruff check src tests scripts
python -m pytest -vv

# Frontend Type Check, Linter, Tests & Production Build
cd frontend
npm run type-check
npm run lint
npm run test
npm run build
```

---

## Database Backup & Restoration
```bash
python scripts/backup_restore.py backup
```

For full verification details, architectural decisions, and readiness classifications, see [`docs/ultimate_project_completion_report.md`](docs/ultimate_project_completion_report.md).

