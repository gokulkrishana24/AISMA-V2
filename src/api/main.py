from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.deps import get_audit_logger, get_db, get_model_manager
from api.middleware import CorrelationAndLoggingMiddleware, RateLimitMiddleware
from api.routers import (
    admin,
    agents,
    ai,
    analytics,
    approvals,
    auth,
    beta,
    billing,
    brand,
    budget,
    campaigns,
    content,
    governance,
    integrations,
    marketing,
    notifications,
    onboarding,
    organizations,
    privacy,
    scheduler,
    support,
)


def validate_production_security() -> None:
    """Fail-closed check ensuring production mode cannot fall back to insecure dev defaults."""
    if os.getenv("AISMA_ENV", "development").lower() != "production":
        return

    jwt_secret = os.getenv("JWT_SECRET_KEY", "")
    if not jwt_secret or len(jwt_secret) < 32 or "2026_dev_prod" in jwt_secret or "change_this" in jwt_secret:
        raise RuntimeError("SECURITY BLOCK: Production mode requires a unique >=32-char JWT_SECRET_KEY.")

    vault_secret = os.getenv("INTEGRATION_VAULT_SECRET", "")
    if not vault_secret or "aisma_vault_enterprise" in vault_secret or "change_this" in vault_secret:
        raise RuntimeError("SECURITY BLOCK: Production mode requires a non-default INTEGRATION_VAULT_SECRET.")

    cors_raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if "*" in cors_raw:
        raise RuntimeError("SECURITY BLOCK: Wildcard CORS origins are prohibited in production mode.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production_security()
    # Initialize background model manager & audit logger
    if os.getenv("AISMA_TEST_MODE") != "true":
        try:
            mm = get_model_manager()
            _ = mm.health()
            audit = get_audit_logger()
            audit.log(
                business_id="system",
                actor="system",
                action="api_daemon_started",
                resource="server:port_8000",
                outcome="ok",
                details={"service": "fastapi", "version": "v2.0"},
            )
        except Exception as exc:
            print(f"[AISMA] Warning during startup: {exc}")
    yield


app = FastAPI(
    title="AI-Native Social Media Agent Team v2 — Enterprise Backend API",
    description="Multi-agent marketing operations platform with local Ollama runtime and fail-closed governance sentinel.",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable secure CORS for frontend Next.js App
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CorrelationAndLoggingMiddleware)

# Mount feature routers
app.include_router(ai.router)
app.include_router(agents.router)
app.include_router(approvals.router)
app.include_router(governance.router)
app.include_router(content.router)
app.include_router(brand.router)
app.include_router(budget.router)
app.include_router(marketing.router)
app.include_router(auth.router)
app.include_router(integrations.router)
app.include_router(campaigns.router)
app.include_router(analytics.router)
app.include_router(onboarding.router)
app.include_router(organizations.router)
app.include_router(billing.router)
app.include_router(notifications.router)
app.include_router(support.router)
app.include_router(privacy.router)
app.include_router(admin.router)
app.include_router(scheduler.router)
app.include_router(beta.router)


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "AI-Native Social Media Agent Team v2",
        "status": "operational",
        "docs": "/docs",
        "version": "2.0.0",
    }


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "aisma_backend", "version": "2.0.0"}


@app.get("/ready")
@app.get("/api/v1/ready")
def readiness_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        db.execute(text("SELECT 1"))
        return {"ready": True, "database": "connected"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not ready: {exc}",
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
