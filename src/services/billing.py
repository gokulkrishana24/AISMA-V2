from __future__ import annotations

import datetime
import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.models import Subscription, SubscriptionPlan, UsageMeter


class QuotaStatus(BaseModel):
    allowed: bool
    plan_name: str
    max_executions: int
    current_executions: int
    usage_percentage: float
    warning: bool = False
    message: str = "Quota within limits"


class BillingService:
    @staticmethod
    def get_plans(db: Session) -> list[dict[str, Any]]:
        plans = db.query(SubscriptionPlan).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "price_monthly": p.price_monthly,
                "max_agents": p.max_agents,
                "max_monthly_executions": p.max_monthly_executions,
                "max_social_accounts": p.max_social_accounts,
                "features": p.features,
            }
            for p in plans
        ]

    @staticmethod
    def get_subscription(db: Session, business_id: str) -> dict[str, Any]:
        sub = db.query(Subscription).filter(Subscription.business_id == business_id).first()
        if not sub:
            # Default to starter plan if none exists
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == "starter").first()
            plan_id = plan.id if plan else "plan_starter"
            sub = Subscription(
                id=f"sub_{uuid.uuid4().hex[:12]}",
                business_id=business_id,
                plan_id=plan_id,
                status="active",
            )
            db.add(sub)
            db.commit()

        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()

        current_month = datetime.datetime.now(datetime.UTC).strftime("%Y-%m")
        meter = (
            db.query(UsageMeter)
            .filter(UsageMeter.business_id == business_id, UsageMeter.period_month == current_month)
            .first()
        )

        return {
            "subscription_id": sub.id,
            "business_id": business_id,
            "status": sub.status,
            "plan": {
                "id": plan.id if plan else sub.plan_id,
                "name": plan.name if plan else "Standard",
                "slug": plan.slug if plan else "standard",
                "price_monthly": plan.price_monthly if plan else 0.0,
                "max_monthly_executions": plan.max_monthly_executions if plan else 1000,
            },
            "usage": {
                "period": current_month,
                "agent_executions": meter.agent_executions_count if meter else 0,
                "tokens_consumed": meter.tokens_consumed if meter else 0,
                "published_posts": meter.published_posts_count if meter else 0,
            },
            "cancel_at_period_end": sub.cancel_at_period_end,
        }

    @staticmethod
    def check_quota(db: Session, business_id: str) -> QuotaStatus:
        sub_info = BillingService.get_subscription(db, business_id)
        max_exec = sub_info["plan"]["max_monthly_executions"]
        current_exec = sub_info["usage"]["agent_executions"]

        usage_pct = round((current_exec / max_exec) * 100, 1) if max_exec > 0 else 0.0
        is_warning = usage_pct >= 80.0
        is_allowed = current_exec < max_exec

        msg = "Quota within limits"
        if not is_allowed:
            msg = f"Monthly execution quota reached ({current_exec}/{max_exec}). Upgrade your subscription."
        elif is_warning:
            msg = f"Approaching quota limit: {usage_pct}% consumed."

        return QuotaStatus(
            allowed=is_allowed,
            plan_name=sub_info["plan"]["name"],
            max_executions=max_exec,
            current_executions=current_exec,
            usage_percentage=usage_pct,
            warning=is_warning,
            message=msg,
        )

    @staticmethod
    def record_usage(db: Session, business_id: str, executions: int = 1, tokens: int = 0) -> None:
        current_month = datetime.datetime.now(datetime.UTC).strftime("%Y-%m")
        meter = (
            db.query(UsageMeter)
            .filter(UsageMeter.business_id == business_id, UsageMeter.period_month == current_month)
            .first()
        )
        if not meter:
            meter = UsageMeter(
                id=f"meter_{uuid.uuid4().hex[:12]}",
                business_id=business_id,
                period_month=current_month,
                agent_executions_count=0,
                tokens_consumed=0,
                published_posts_count=0,
            )
            db.add(meter)

        meter.agent_executions_count += executions
        meter.tokens_consumed += tokens
        db.commit()

