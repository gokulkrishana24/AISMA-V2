from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from db.models import (
    ApprovalItem,
    BrandProfileRecord,
    Business,
    ContentDraft,
    Membership,
    Subscription,
    SubscriptionPlan,
    TenantSettingRecord,
    UsageMeter,
    User,
)
from services.auth import hash_password

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SQLITE_PATH = STATE_DIR / "aisma.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")

is_sqlite = DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_sqlite_columns() -> None:
    """Safely add newly introduced columns on existing SQLite tables without data loss."""
    if not is_sqlite:
        return
    required: dict[str, list[tuple[str, str]]] = {
        "approval_items": [
            ("decided_note", "TEXT"),
            ("draft_id", "VARCHAR(64)"),
            ("task_id", "VARCHAR(64)"),
            ("metadata_json", "JSON"),
        ],
        "content_drafts": [
            ("version", "INTEGER DEFAULT 1"),
            ("campaign_id", "VARCHAR(64)"),
        ],
    }
    with engine.begin() as conn:
        for table, cols in required.items():
            existing_cols = {
                row[1] for row in conn.execute(text(f"PRAGMA table_info('{table}')")).fetchall()
            }
            for col_name, col_type in cols:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))


def init_db() -> None:
    """Initialize database tables and seed baseline enterprise tenant & admin."""
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()

    with SessionLocal() as session:
        # Check if default enterprise business exists
        enterprise_biz_id = "biz_apex_enterprises"
        existing_biz = session.query(Business).filter(Business.id == enterprise_biz_id).first()
        if not existing_biz:
            biz = Business(
                id=enterprise_biz_id,
                name="Apex Multi-Channel Enterprise",
                slug="apex-enterprise",
                industry="B2B SaaS & AI Marketing Technology",
            )
            session.add(biz)
            session.flush()

        # Check if default admin user exists
        admin_user_id = "usr_enterprise_01"
        existing_user = session.query(User).filter(User.id == admin_user_id).first()
        if not existing_user:
            admin_user = User(
                id=admin_user_id,
                email="marcus.vance@apexmarketing.ai",
                hashed_password=hash_password("Password123!"),
                full_name="Marcus Vance",
                role="admin",
                is_active=True,
            )
            session.add(admin_user)
            session.flush()

            # Create membership
            membership = Membership(
                id="mem_admin_01",
                user_id=admin_user.id,
                business_id=enterprise_biz_id,
                role="admin",
            )
            session.add(membership)

        # Seed initial pending approval if empty
        existing_approval = session.query(ApprovalItem).filter(ApprovalItem.id == "appr_001").first()
        if not existing_approval:
            approval = ApprovalItem(
                id="appr_001",
                business_id=enterprise_biz_id,
                title="Q4 Enterprise AI Playbook — LinkedIn Launch Draft",
                agent_id="content_engine",
                agent_name="Content Engine Agent",
                type="content_draft",
                status="pending",
                priority="high",
                channel="linkedin",
                content=(
                    "Most enterprise social teams spend 70% of their bandwidth on manual scheduling.\n\n"
                    "AI-Native Social Media Agent Team v2 shifts that equation:\n"
                    "• Search Radar detects buyer intent shifts\n"
                    "• Content Engine constructs brand-compliant variants\n"
                    "• Human-in-the-loop Governance guarantees verification\n\n"
                    "How is your organization rethinking organic distribution this quarter?"
                ),
                hooks=[
                    "Most enterprise social teams spend 70% of their bandwidth on manual scheduling.",
                    "Autonomous marketing isn't about replacing judgment—it's about scaling precision.",
                    "The shift from scheduled publishing to intent-driven orchestration is happening now.",
                ],
                selected_hook="Most enterprise social teams spend 70% of their bandwidth on manual scheduling.",
                brand_voice_score=94,
                policy_checks=[
                    {"name": "No Unverified Financial Claims", "status": "passed"},
                    {"name": "Deterministic Budget Verification", "status": "passed"},
                    {"name": "Brand Lexicon Consistency", "status": "passed"},
                ],
                estimated_spend=0.0,
            )
            session.add(approval)

        # Seed initial draft if empty
        existing_draft = session.query(ContentDraft).filter(ContentDraft.id == "draft_001").first()
        if not existing_draft:
            draft = ContentDraft(
                id="draft_001",
                business_id=enterprise_biz_id,
                title="Enterprise Social Orchestration Announcement",
                channel="linkedin",
                status="pending_approval",
                content="Enterprise social media is evolving from scheduled posts to autonomous agent teams. Here is how our architecture works.",
                hooks=[
                    "Enterprise social media is evolving.",
                    "Why scheduled posts are being replaced by autonomous agents.",
                    "The new architecture of enterprise distribution.",
                ],
                selected_hook="Enterprise social media is evolving.",
                brand_voice_score=92,
                seo_keywords=["autonomous marketing", "enterprise social", "AI agents"],
            )
            session.add(draft)

        # Seed standard SaaS subscription plans
        plans_data = [
            ("plan_starter", "Starter Tier", "starter", 49.0, 8, 500, 3, ["8 AI Agents", "Local Ollama Inference", "Basic Brand OS", "3 Social Accounts"]),
            ("plan_professional", "Professional Tier", "professional", 149.0, 8, 2500, 10, ["8 AI Agents", "Advanced Brand OS", "10 Social Accounts", "Campaign Management", "Multi-Channel Scheduling"]),
            ("plan_agency", "Agency Tier", "agency", 399.0, 8, 10000, 25, ["Multi-Client Workspaces", "Advanced Human Approvals", "25 Social Accounts", "Dedicated Brand OS per Client", "Deterministic ROI Engine"]),
            ("plan_enterprise", "Enterprise Tier", "enterprise", 999.0, 8, 50000, 100, ["Unlimited Workspaces", "Fail-Closed Governance Sentinel", "Cryptographic Audit Ledger", "Unlimited Accounts", "Custom Model Routing"]),
        ]
        for pid, pname, pslug, price, max_ag, max_exec, max_acc, feats in plans_data:
            existing_plan = session.query(SubscriptionPlan).filter(SubscriptionPlan.id == pid).first()
            if not existing_plan:
                session.add(
                    SubscriptionPlan(
                        id=pid,
                        name=pname,
                        slug=pslug,
                        price_monthly=price,
                        max_agents=max_ag,
                        max_monthly_executions=max_exec,
                        max_social_accounts=max_acc,
                        features=feats,
                    )
                )

        # Seed enterprise active subscription
        existing_sub = session.query(Subscription).filter(Subscription.business_id == enterprise_biz_id).first()
        if not existing_sub:
            session.add(
                Subscription(
                    id="sub_enterprise_01",
                    business_id=enterprise_biz_id,
                    plan_id="plan_enterprise",
                    status="active",
                )
            )

        # Seed initial usage meter
        existing_meter = session.query(UsageMeter).filter(UsageMeter.business_id == enterprise_biz_id, UsageMeter.period_month == "2026-11").first()
        if not existing_meter:
            session.add(
                UsageMeter(
                    id="meter_apex_202611",
                    business_id=enterprise_biz_id,
                    period_month="2026-11",
                    agent_executions_count=0,
                    tokens_consumed=0,
                    published_posts_count=0,
                )
            )

        # Seed TenantSettingRecord for enterprise workspace if missing
        existing_settings = session.query(TenantSettingRecord).filter(
            TenantSettingRecord.business_id == enterprise_biz_id
        ).first()
        if not existing_settings:
            session.add(
                TenantSettingRecord(
                    id="set_apex_01",
                    business_id=enterprise_biz_id,
                    timezone="UTC",
                    currency="USD",
                    monthly_budget=0.0,
                    budget_alert_threshold=0.0,
                    notification_prefs={"approvals": True, "security": True, "billing": True},
                )
            )

        # Seed BrandProfileRecord for enterprise workspace if missing
        existing_brand = session.query(BrandProfileRecord).filter(
            BrandProfileRecord.business_id == enterprise_biz_id
        ).first()
        if not existing_brand:
            from api.deps import BRAND_OS_STORE

            session.add(
                BrandProfileRecord(
                    id="brand_apex_01",
                    business_id=enterprise_biz_id,
                    profile_data=dict(BRAND_OS_STORE),
                    onboarding_data={
                        "company_name": "Apex Multi-Channel Enterprise",
                        "industry": "B2B SaaS & AI Marketing Technology",
                        "website": "https://apexmarketing.ai",
                        "completed": True,
                    },
                    is_complete=True,
                )
            )

        session.commit()
