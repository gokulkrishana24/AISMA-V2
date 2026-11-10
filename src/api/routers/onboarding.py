from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from db.models import Business, Membership, Subscription, User

router = APIRouter(prefix="/api/v1/onboarding", tags=["Customer Onboarding & Workspace Setup"])


class OnboardingSetupPayload(BaseModel):
    company_name: str
    industry: str
    target_audience: str
    primary_channels: list[str] = ["linkedin"]
    selected_plan: str = "starter"


@router.post("/setup")
def complete_onboarding_setup(
    payload: OnboardingSetupPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    biz_id = f"biz_{uuid.uuid4().hex[:12]}"
    biz_slug = payload.company_name.lower().replace(" ", "-")[:40]

    business = Business(
        id=biz_id,
        name=payload.company_name,
        slug=biz_slug,
        industry=payload.industry,
    )
    db.add(business)
    db.flush()

    # Assign user as organization admin
    membership = Membership(
        id=f"mem_{uuid.uuid4().hex[:12]}",
        user_id=current_user.id,
        business_id=business.id,
        role="admin",
    )
    db.add(membership)

    # Attach selected subscription plan
    plan_id = f"plan_{payload.selected_plan.lower()}"
    subscription = Subscription(
        id=f"sub_{uuid.uuid4().hex[:12]}",
        business_id=business.id,
        plan_id=plan_id,
        status="active",
    )
    db.add(subscription)
    db.commit()

    return {
        "success": True,
        "business_id": business.id,
        "business_name": business.name,
        "role": "admin",
        "plan": payload.selected_plan,
        "message": f"Organization '{business.name}' successfully provisioned and ready for multi-agent marketing operations.",
    }

