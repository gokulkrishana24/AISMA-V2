from __future__ import annotations

import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.deps import (
    get_audit_logger,
    get_current_user,
    get_db,
    get_model_manager,
    require_tenant_access,
)
from db.models import SupportTicket, User
from services.synthetic_data import reset_synthetic_beta_workspace, seed_synthetic_beta_workspace

router = APIRouter(prefix="/api/v1/beta", tags=["Local Beta Testing, Synthetic Simulation & Diagnostics"])


class BetaFeedbackPayload(BaseModel):
    category: str = "feedback"  # feedback, bug, feature_request
    title: str
    description: str
    severity: str = "medium"


@router.post("/seed-demo")
def seed_demo_workspace(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return seed_synthetic_beta_workspace(db, owner_user_id=current_user.id)


@router.post("/reset-demo")
def reset_demo_workspace(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return reset_synthetic_beta_workspace(db)


@router.get("/diagnostics")
def get_local_diagnostics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    mm = get_model_manager()
    ai_health = mm.health()

    return {
        "mode": "local_development_beta",
        "database_connected": db_ok,
        "ollama_connected": ai_health.get("connected", False),
        "active_model": ai_health.get("active_model", "phi3.5:latest"),
        "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
    }


@router.post("/feedback")
def submit_beta_feedback(
    payload: BetaFeedbackPayload,
    business_id: str = Depends(require_tenant_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ticket = SupportTicket(
        id=f"beta_{uuid.uuid4().hex[:10]}",
        business_id=business_id,
        user_id=current_user.id,
        subject=f"[{payload.category.upper()}] {payload.title}",
        description=payload.description,
        priority=payload.severity,
        status="open",
        created_at=datetime.datetime.now(datetime.UTC),
    )
    db.add(ticket)
    db.commit()

    audit = get_audit_logger()
    audit.log(
        business_id=business_id,
        actor=current_user.email,
        action="beta_feedback_submitted",
        resource=f"ticket:{ticket.id}",
        outcome="ok",
        details={"category": payload.category, "severity": payload.severity},
    )

    return {
        "id": ticket.id,
        "status": "recorded",
        "message": "Beta feedback recorded cleanly in local database and audit ledger.",
    }
