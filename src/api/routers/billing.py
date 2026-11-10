from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_audit_logger, get_db, require_tenant_access
from db.models import Subscription, SubscriptionPlan
from services.billing import BillingService

router = APIRouter(prefix="/api/v1/billing", tags=["SaaS Subscription & Usage Metering"])

_BILLING_WEBHOOK_SECRET = os.getenv("BILLING_WEBHOOK_SECRET", "aisma_billing_webhook_hmac_secret_2026")
_PROCESSED_BILLING_EVENTS: set[str] = set()


class UpgradePlanPayload(BaseModel):
    plan_slug: str  # starter, professional, agency, enterprise


@router.get("/plans")
def list_available_plans(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return BillingService.get_plans(db)


@router.get("/subscription")
def get_tenant_subscription(
    business_id: str = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return BillingService.get_subscription(db, business_id)


@router.get("/quota")
def check_quota_status(
    business_id: str = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    quota = BillingService.check_quota(db, business_id)
    return quota.model_dump()


@router.post("/upgrade")
def upgrade_plan(
    payload: UpgradePlanPayload,
    business_id: str = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    target_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == payload.plan_slug.lower()).first()
    if not target_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{payload.plan_slug}' does not exist")

    sub = db.query(Subscription).filter(Subscription.business_id == business_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription record not found")

    sub.plan_id = target_plan.id
    sub.status = "active"
    db.commit()

    return {
        "success": True,
        "business_id": business_id,
        "new_plan": target_plan.name,
        "monthly_executions": target_plan.max_monthly_executions,
        "price_monthly": target_plan.price_monthly,
    }


@router.post("/cancel")
def cancel_plan(
    business_id: str = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    sub = db.query(Subscription).filter(Subscription.business_id == business_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription record not found")

    sub.cancel_at_period_end = True
    db.commit()

    return {
        "success": True,
        "business_id": business_id,
        "cancel_at_period_end": True,
        "message": "Subscription set to cancel at end of current billing period.",
    }


@router.post("/webhook")
async def handle_billing_webhook(
    request: Request,
    x_billing_signature: str | None = Header(None, alias="X-Billing-Signature"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Modular, idempotent payment webhook receiver (no live merchant charges enabled)."""
    raw_body = await request.body()
    if not x_billing_signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Billing-Signature header")

    expected_sig = hmac.new(_BILLING_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(x_billing_signature.replace("sha256=", ""), expected_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid billing webhook signature")

    payload = await request.json()
    event_id = str(payload.get("event_id", ""))
    event_type = str(payload.get("event_type", ""))
    business_id = str(payload.get("business_id", ""))

    if not event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event_id")

    if event_id in _PROCESSED_BILLING_EVENTS:
        return {"received": True, "event_id": event_id, "duplicate_ignored": True}

    sub = db.query(Subscription).filter(Subscription.business_id == business_id).first() if business_id else None
    new_status = None
    if sub:
        if event_type == "invoice.paid":
            sub.status = "active"
            new_status = "active"
        elif event_type == "invoice.payment_failed":
            sub.status = "past_due"
            new_status = "past_due"
        elif event_type == "customer.subscription.deleted":
            sub.status = "canceled"
            new_status = "canceled"
        db.commit()

    _PROCESSED_BILLING_EVENTS.add(event_id)
    audit = get_audit_logger()
    audit.log(
        business_id=business_id or "system",
        actor="billing_webhook",
        action=f"billing_event:{event_type}",
        resource=f"event:{event_id}",
        outcome="ok",
        details={"event_type": event_type, "new_status": new_status},
    )

    return {
        "received": True,
        "event_id": event_id,
        "duplicate_ignored": False,
        "subscription_status": new_status,
    }
