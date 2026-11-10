from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_audit_logger, get_current_user, get_db, get_model_manager
from db.models import (
    ApprovalItem,
    Business,
    Campaign,
    Subscription,
    SubscriptionPlan,
    UsageMeter,
    User,
)

router = APIRouter(prefix="/api/v1/admin", tags=["Platform Administration & Beta Controls"])

# Controlled Beta Feature Flags
BETA_FEATURE_FLAGS: dict[str, dict[str, Any]] = {
    "beta_agency_workspaces": {
        "enabled": True,
        "description": "Multi-client workspace switching for Marketing Agencies",
        "rollout_stage": "beta",
    },
    "beta_predictive_roi": {
        "enabled": False,
        "description": "Forecasting curves computed from historical ROAS baselines",
        "rollout_stage": "internal",
    },
    "beta_multilingual_content": {
        "enabled": False,
        "description": "Multi-language campaign variant localization",
        "rollout_stage": "alpha",
    },
    "beta_auto_scheduling": {
        "enabled": True,
        "description": "Event-driven calendar trigger execution",
        "rollout_stage": "beta",
    },
}


class FeatureFlagUpdatePayload(BaseModel):
    enabled: bool


def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator privileges required for this operation.",
        )
    return current_user


@router.get("/overview")
def get_admin_overview(
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    total_businesses = db.query(Business).count()
    total_users = db.query(User).count()
    active_subscriptions = db.query(Subscription).filter(Subscription.status == "active").count()
    pending_approvals = db.query(ApprovalItem).filter(ApprovalItem.status == "pending").count()
    total_campaigns = db.query(Campaign).count()

    mm = get_model_manager()
    ai_health = mm.health()

    return {
        "platform_status": "operational",
        "metrics": {
            "total_organizations": total_businesses,
            "total_users": total_users,
            "active_subscriptions": active_subscriptions,
            "pending_approvals": pending_approvals,
            "total_campaigns": total_campaigns,
        },
        "ai_runtime": {
            "ollama_connected": ai_health.get("connected", False),
            "active_model": ai_health.get("active_model", "phi3.5:latest"),
        },
        "audited_by": admin_user.email,
    }


@router.get("/organizations")
def list_all_organizations(
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    businesses = db.query(Business).all()
    results = []
    for biz in businesses:
        sub = db.query(Subscription).filter(Subscription.business_id == biz.id).first()
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first() if sub else None
        meter = db.query(UsageMeter).filter(UsageMeter.business_id == biz.id).first()
        results.append(
            {
                "id": biz.id,
                "name": biz.name,
                "slug": biz.slug,
                "industry": biz.industry,
                "plan_name": plan.name if plan else "None",
                "subscription_status": sub.status if sub else "none",
                "monthly_executions": meter.agent_executions_count if meter else 0,
                "created_at": biz.created_at.isoformat(),
            }
        )
    return results


@router.get("/feature-flags")
def get_feature_flags(
    admin_user: User = Depends(require_platform_admin),
) -> dict[str, Any]:
    return BETA_FEATURE_FLAGS


@router.put("/feature-flags/{flag_name}")
def toggle_feature_flag(
    flag_name: str,
    payload: FeatureFlagUpdatePayload,
    admin_user: User = Depends(require_platform_admin),
) -> dict[str, Any]:
    if flag_name not in BETA_FEATURE_FLAGS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Feature flag '{flag_name}' not found")

    BETA_FEATURE_FLAGS[flag_name]["enabled"] = payload.enabled

    audit = get_audit_logger()
    audit.log(
        business_id="system",
        actor=admin_user.email,
        action="feature_flag_updated",
        resource=f"feature_flag:{flag_name}",
        outcome="ok",
        details={"flag": flag_name, "enabled": payload.enabled},
    )

    return {"flag": flag_name, **BETA_FEATURE_FLAGS[flag_name]}

