from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy.orm import Session

from db.models import (
    ApprovalItem,
    Business,
    Campaign,
    ContentDraft,
    Membership,
    Notification,
    Subscription,
    UsageMeter,
)

DEMO_BIZ_ID = "biz_demo_nova_saas"


def seed_synthetic_beta_workspace(db: Session, owner_user_id: str = "usr_enterprise_01") -> dict[str, Any]:
    """Deterministically seed clearly labeled fictional [DEMO] workspace & marketing records.

    Strictly isolated under biz_demo_nova_saas so real customer records remain untouched.
    """
    existing_biz = db.query(Business).filter(Business.id == DEMO_BIZ_ID).first()
    if not existing_biz:
        db.add(
            Business(
                id=DEMO_BIZ_ID,
                name="[DEMO] NovaCloud Analytics Inc.",
                slug="demo-novacloud-analytics",
                industry="B2B Developer Analytics (Synthetic)",
            )
        )
        db.flush()

    existing_mem = (
        db.query(Membership)
        .filter(Membership.business_id == DEMO_BIZ_ID, Membership.user_id == owner_user_id)
        .first()
    )
    if not existing_mem:
        db.add(
            Membership(
                id="mem_demo_owner",
                user_id=owner_user_id,
                business_id=DEMO_BIZ_ID,
                role="admin",
            )
        )

    existing_sub = db.query(Subscription).filter(Subscription.business_id == DEMO_BIZ_ID).first()
    if not existing_sub:
        db.add(
            Subscription(
                id="sub_demo_01",
                business_id=DEMO_BIZ_ID,
                plan_id="plan_agency",
                status="active",
            )
        )

    current_month = datetime.datetime.now(datetime.UTC).strftime("%Y-%m")
    existing_meter = (
        db.query(UsageMeter)
        .filter(UsageMeter.business_id == DEMO_BIZ_ID, UsageMeter.period_month == current_month)
        .first()
    )
    if not existing_meter:
        db.add(
            UsageMeter(
                id="meter_demo_01",
                business_id=DEMO_BIZ_ID,
                period_month=current_month,
                agent_executions_count=64,
                tokens_consumed=31200,
                published_posts_count=7,
            )
        )

    # Fictional Campaigns
    demo_campaigns = [
        ("cmp_demo_01", "[DEMO] Q4 Zero-Latency Telemetry Launch", "product_launch", "active", 8500.0, 2140.0, ["linkedin", "twitter"]),
        ("cmp_demo_02", "[DEMO] FinOps Engineer Outreach Sprint", "lead_generation", "draft", 4000.0, 0.0, ["linkedin"]),
    ]
    for cid, name, obj, status_val, alloc, spent, chans in demo_campaigns:
        if not db.query(Campaign).filter(Campaign.id == cid).first():
            db.add(
                Campaign(
                    id=cid,
                    business_id=DEMO_BIZ_ID,
                    name=name,
                    objective=obj,
                    status=status_val,
                    budget_allocated=alloc,
                    budget_spent=spent,
                    channels=chans,
                )
            )

    # Fictional Content Draft & Approval
    if not db.query(ContentDraft).filter(ContentDraft.id == "draft_demo_01").first():
        db.add(
            ContentDraft(
                id="draft_demo_01",
                business_id=DEMO_BIZ_ID,
                title="[DEMO] Why Deterministic Analytics Matter for AI Teams",
                channel="linkedin",
                status="pending_approval",
                content="[SYNTHETIC DEMO] AI should summarize marketing insights—never guess financial ROAS numbers.",
                hooks=["Why AI should never invent financial metrics."],
                selected_hook="Why AI should never invent financial metrics.",
                brand_voice_score=96,
                seo_keywords=["deterministic analytics", "marketing governance"],
            )
        )

    if not db.query(ApprovalItem).filter(ApprovalItem.id == "appr_demo_01").first():
        db.add(
            ApprovalItem(
                id="appr_demo_01",
                business_id=DEMO_BIZ_ID,
                title="[DEMO] LinkedIn Thought Leadership Draft",
                agent_id="content_engine",
                agent_name="Content Engine Agent",
                type="content_draft",
                status="pending",
                priority="high",
                channel="linkedin",
                content="[SYNTHETIC DEMO] Approved-only Brand OS retrieval guarantees zero unverified product claims.",
                hooks=["Approved-only Brand OS retrieval guarantees zero unverified product claims."],
                selected_hook="Approved-only Brand OS retrieval guarantees zero unverified product claims.",
                brand_voice_score=95,
                policy_checks=[{"name": "Synthetic Demo Label Verified", "status": "passed"}],
                estimated_spend=0.0,
            )
        )

    if not db.query(Notification).filter(Notification.id == "notif_demo_01").first():
        db.add(
            Notification(
                id="notif_demo_01",
                business_id=DEMO_BIZ_ID,
                title="[DEMO] Approval Pending",
                message="Synthetic demonstration approval item ready for review.",
                category="approval",
                read=False,
            )
        )

    db.commit()
    return {
        "seeded": True,
        "is_synthetic": True,
        "business_id": DEMO_BIZ_ID,
        "business_name": "[DEMO] NovaCloud Analytics Inc.",
        "note": "All generated records are strictly synthetic demonstration fixtures isolated to biz_demo_nova_saas.",
    }


def reset_synthetic_beta_workspace(db: Session) -> dict[str, Any]:
    """Safely reset ONLY synthetic demo records (biz_demo_nova_saas). Never touches non-demo data."""
    db.query(Notification).filter(Notification.business_id == DEMO_BIZ_ID).delete()
    db.query(ApprovalItem).filter(ApprovalItem.business_id == DEMO_BIZ_ID).delete()
    db.query(ContentDraft).filter(ContentDraft.business_id == DEMO_BIZ_ID).delete()
    db.query(Campaign).filter(Campaign.business_id == DEMO_BIZ_ID).delete()
    db.query(UsageMeter).filter(UsageMeter.business_id == DEMO_BIZ_ID).delete()
    db.query(Subscription).filter(Subscription.business_id == DEMO_BIZ_ID).delete()
    db.query(Membership).filter(Membership.business_id == DEMO_BIZ_ID).delete()
    deleted_biz = db.query(Business).filter(Business.id == DEMO_BIZ_ID).delete()
    db.commit()

    return {
        "reset": True,
        "deleted_demo_business_count": deleted_biz,
        "real_data_preserved": True,
    }

