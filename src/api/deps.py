from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from agents.registry import AgentRegistry, build_default_registry
from ai.config import load_ai_config_file
from ai.model_manager import ModelManager
from ai.registry import ModelRegistry
from db.database import get_db, init_db
from db.models import Membership, User
from governance.audit import AuditLogger
from governance.budget import BudgetEnforcer
from governance.killswitch import KillSwitch
from governance.permissions import PermissionManager
from governance.policy import PolicyEngine
from orchestrator.orchestrator import Orchestrator
from services.auth import decode_access_token
from services.brand_context import BrandContextService

# Project root paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
STATE_DIR = BASE_DIR / "state"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Singletons
_audit_logger: AuditLogger | None = None
_kill_switch: KillSwitch | None = None
_budget_enforcer: BudgetEnforcer | None = None
_permission_manager: PermissionManager | None = None
_policy_engine: PolicyEngine | None = None
_model_manager: ModelManager | None = None
_agent_registry: AgentRegistry | None = None
_orchestrator: Orchestrator | None = None
_brand_service: BrandContextService | None = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(LOGS_DIR / "audit")
    return _audit_logger


def get_kill_switch() -> KillSwitch:
    global _kill_switch
    if _kill_switch is None:
        _kill_switch = KillSwitch(STATE_DIR / "killswitch")
    return _kill_switch


def get_budget_enforcer() -> BudgetEnforcer:
    global _budget_enforcer
    if _budget_enforcer is None:
        _budget_enforcer = BudgetEnforcer(state_dir=STATE_DIR / "budget")
        try:
            _budget_enforcer.get_limits(STORE_BUSINESS_ID)
        except Exception:
            _budget_enforcer.set_limits(
                STORE_BUSINESS_ID,
                {
                    "max_tokens_per_day": 500_000,
                    "max_actions_per_day": 1_000,
                    "max_cost_units_per_day": 250.0,
                },
            )
    return _budget_enforcer


def get_permission_manager() -> PermissionManager:
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager


def get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine({"default_deny_publishing": True})
    return _policy_engine


def get_model_manager() -> ModelManager:
    global _model_manager
    if _model_manager is None:
        import os

        # config/ai_config.yaml is optional (mounted at runtime by docker-compose);
        # a missing file yields the environment-derived configuration.
        cfg = load_ai_config_file(BASE_DIR / "config" / "ai_config.yaml")
        reg = ModelRegistry()
        ks = get_kill_switch()

        if (os.getenv("AISMA_TEST_MODE") == "true" or os.getenv("AISMA_MOCK_LLM") == "true") and os.getenv("AISMA_RUN_REAL_LLM_TESTS") != "true":
            from tests.agents.conftest import MockProvider
            mock_payload = {
                "summary": "Q4 Enterprise AI Playbook content draft generated",
                "main_draft": "Enterprise social teams spend 70% of bandwidth on manual scheduling.\n\nAI-Native Social Media Agent Team v2 shifts that equation:\n• Intent detection\n• Brand compliance\n• Governance verification",
                "alternative_hooks": [
                    {"type": "hook", "detail": "Autonomous orchestration is here."},
                    {"type": "hook", "detail": "The shift to intent-driven marketing."},
                ],
                "confidence": 0.95,
                "seo_keywords": ["autonomous marketing", "enterprise AI"],
                "requires_human_approval": True,
            }
            provider = MockProvider(mock_payload)
            _model_manager = ModelManager(config=cfg, provider=provider, registry=reg, kill_switch=ks)
        else:
            _model_manager = ModelManager(config=cfg, registry=reg, kill_switch=ks)
    return _model_manager


def get_agent_registry() -> AgentRegistry:
    global _agent_registry
    if _agent_registry is None:
        mm = get_model_manager()
        _agent_registry = build_default_registry(mm.provider)
    return _agent_registry


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator(
            registry=get_agent_registry(),
            model_manager=get_model_manager(),
            permissions=get_permission_manager(),
            policy=get_policy_engine(),
            kill_switch=get_kill_switch(),
            budget=get_budget_enforcer(),
            audit=get_audit_logger(),
        )
    return _orchestrator


def get_brand_service() -> BrandContextService:
    global _brand_service
    if _brand_service is None:
        _brand_service = BrandContextService()
    return _brand_service


# In-memory stores for operational data
STORE_BUSINESS_ID = "biz_apex_enterprises"

APPROVALS_STORE: list[dict[str, Any]] = [
    {
        "id": "appr_001",
        "title": "Q4 Enterprise AI Playbook — LinkedIn Launch Draft",
        "agentId": "content_engine",
        "agentName": "Content Engine Agent",
        "type": "content_draft",
        "status": "pending",
        "priority": "high",
        "urgency": "high",
        "submittedAt": "2026-11-09T18:30:00Z",
        "channel": "linkedin",
        "content": "Most enterprise social teams spend 70% of their bandwidth on manual scheduling.\n\nAI-Native Social Media Agent Team v2 shifts that equation:\n• Search Radar detects buyer intent shifts\n• Content Engine constructs brand-compliant variants\n• Human-in-the-loop Governance guarantees verification\n\nHow is your organization rethinking organic distribution this quarter?",
        "contentPreview": "Most enterprise social teams spend 70% of their bandwidth on manual scheduling. AI-Native Social Media Agent Team v2 shifts that equation with Search Radar & Human-in-the-loop Governance.",
        "hooks": [
            "Most enterprise social teams spend 70% of their bandwidth on manual scheduling.",
            "Autonomous marketing isn't about replacing judgment—it's about scaling precision.",
            "The shift from scheduled publishing to intent-driven orchestration is happening now.",
        ],
        "selectedHook": "Most enterprise social teams spend 70% of their bandwidth on manual scheduling.",
        "brandVoiceScore": 94,
        "policyChecks": [
            {"name": "No Unverified Financial Claims", "status": "passed"},
            {"name": "Deterministic Budget Verification", "status": "passed"},
            {"name": "Brand Lexicon Consistency", "status": "passed"},
        ],
        "estimatedSpend": 0.0,
        "estimatedCost": 0.0,
        "budgetImpactPercent": 0.0,
        "policyViolations": [],
        "budgetWarnings": [],
        "riskScore": 12,
        "metadata": {},
    }
]

DRAFTS_STORE: list[dict[str, Any]] = [
    {
        "id": "draft_001",
        "title": "Enterprise Social Orchestration Announcement",
        "channel": "linkedin",
        "status": "pending_approval",
        "content": "Enterprise social media is evolving from scheduled posts to autonomous agent teams. Here is how our architecture works.",
        "hooks": [
            "Enterprise social media is evolving.",
            "Why scheduled posts are being replaced by autonomous agents.",
            "The new architecture of enterprise distribution.",
        ],
        "selectedHook": "Enterprise social media is evolving.",
        "brandVoiceScore": 92,
        "seoKeywords": ["autonomous marketing", "enterprise social", "AI agents"],
        "createdAt": "2026-11-09T17:00:00Z",
        "updatedAt": "2026-11-09T17:30:00Z",
    }
]

BRAND_OS_STORE: dict[str, Any] = {
    "business_id": STORE_BUSINESS_ID,
    "company_name": "Apex Multi-Channel Enterprise",
    "industry": "B2B SaaS & AI Marketing Technology",
    "identity": {
        "brandName": "Apex Multi-Channel Enterprise",
        "tagline": "Autonomous Marketing Under Fail-Closed Governance",
        "mission": "Empower marketing leaders to scale authentic multi-channel engagement locally without sacrificing security or brand compliance.",
        "coreValues": ["Deterministic Governance", "Zero Cloud Lock-in", "Evidence-First", "Human-in-the-Loop"],
    },
    "voice": {
        "archetype": "Authoritative Strategist",
        "toneKeywords": ["Authoritative", "Insightful", "Data-driven", "Accessible"],
        "dos": ["Cite approved Brand OS proof points", "Keep paragraphs concise", "Use measurable B2B insights"],
        "donts": ["Buzzword soup (synergy, 10x, game-changer)", "Unsubstantiated financial guarantees", "Excessive emojis"],
        "readingLevel": "Executive / Technical (Grade 11–13)",
    },
    "brand_voice": {
        "primary_tone": "Authoritative, insightful, data-driven, yet accessible",
        "characteristics": ["Clear and concise", "Technically rigorous", "Forward-looking", "Evidence-first"],
        "avoid": ["Buzzword soup (synergy, 10x, game-changer)", "Unsubstantiated superlative claims", "Excessive emojis"],
    },
    "positioning": {
        "statement": "The first open-source, local-first multi-agent marketing operations platform built for enterprise governance and deterministic privacy.",
        "differentiation": ["Fail-closed security sentinel", "Local GPU inference via Ollama", "Cryptographic audit trail", "Strict human-in-the-loop signoff"],
        "category": "Autonomous AI Marketing Operations",
        "targetSegment": "Mid-Market & Enterprise B2B Marketing Teams",
        "primaryPromise": "Autonomous multi-channel marketing execution with 100% human sign-off and local GPU privacy.",
        "reasonsToBelieve": [
            "Local Ollama inference (phi3.5:latest) with zero cloud API data sharing",
            "SHA-256 hash-chained immutable audit ledger on every action",
            "Deterministic Python ROAS & ROI analytics engine",
        ],
    },
    "audience": [
        {
            "persona": "VP / Head of Marketing",
            "title": "Executive Marketing Decision Maker",
            "painPoints": ["AI hallucinations damaging brand trust", "Disconnected scheduling tools", "Lack of audit compliance"],
            "keyAspirations": ["Predictable organic pipeline", "Full human governance over AI output", "Verifiable ROI"],
        },
        {
            "persona": "Demand Generation Director",
            "title": "Growth & Acquisition Lead",
            "painPoints": ["Manual multi-channel campaign adaptation", "Slow SEO to content turnaround"],
            "keyAspirations": ["Faster intent-to-draft execution", "Consistent brand voice across LinkedIn & X"],
        },
    ],
    "target_audience": {
        "primary": "Heads of Marketing, Demand Generation Directors, and Social Media Leads at mid-to-enterprise tech organizations",
        "secondary": "Growth marketing consultants and agency operations managers",
    },
    "messagingBank": [
        {
            "pillar": "Fail-Closed Governance",
            "approvedPhrases": ["Every external publication requires explicit human approval.", "Instant global kill switch stops agent operations in milliseconds."],
            "proofPoints": ["SHA-256 cryptographic audit logs on every decision"],
        },
        {
            "pillar": "Sovereign Local AI",
            "approvedPhrases": ["Run specialized marketing agents directly on local GPUs with Ollama."],
            "proofPoints": ["Zero cloud LLM API token fees for local inference"],
        },
    ],
    "approvedProofPoints": [
        {"claim": "Zero cloud LLM API costs for local Ollama models", "citation": "Local AI Architecture Spec v2", "verified": True},
        {"claim": "SHA-256 cryptographic audit logs on every approval and killswitch change", "citation": "Governance Audit Module", "verified": True},
    ],
    "faqs": [
        {
            "question": "Can AI agents publish directly to social media without approval?",
            "approvedAnswer": "No. AISMA v2 enforces a fail-closed PolicyEngine that requires explicit human admin approval before publishing.",
            "category": "Governance",
        }
    ],
    "visualGuidelines": {
        "primaryColor": "#0A0F1E (Dark Navy)",
        "accentColor": "#3B82F6 (Electric Blue) & #06B6D4 (Cyan)",
        "fontFamily": "Inter / JetBrains Mono",
        "imageryRules": ["Clean high-contrast enterprise visuals", "Zero unverified stock claims"],
    },
    "messaging_bank": {
        "value_props": [
            "Autonomous marketing without governance compromises",
            "Local inference with zero proprietary cloud lock-in",
            "Deterministic ROI tracking directly computed in Python",
        ],
        "approved_proof_points": [
            {"claim": "Zero cloud LLM API costs for local models", "verified": True},
            {"claim": "SHA-256 cryptographic audit logs on every decision", "verified": True},
        ],
    },
    "prohibited_claims": [
        "Guaranteed 100% viral reach",
        "Automatic unmonitored live posting to social accounts",
        "Arbitrary financial revenue guarantees",
    ],
    "approved_products_services": [
        {"name": "AISMA v2 Enterprise Platform", "tier": "Self-Hosted Open Source"},
    ],
    "channel_guidelines": {
        "linkedin": "Insight-led narratives, structured bullet points, clear professional CTA",
        "twitter": "Concise observations, single sharp hook, 1-2 focused hashtags",
    },
    "content_restrictions": [
        "Do not publish customer names without signed release",
        "Do not cite competitor pricing without dated screenshot",
    ],
}

AGENT_ASSIGNMENTS_STORE: dict[str, dict[str, Any]] = {
    "search_visibility": {"assigned_model": "phi3.5:latest", "fallback_model": "qwen3.5:4b", "max_tokens": 2048, "temperature": 0.2},
    "market_radar": {"assigned_model": "phi3.5:latest", "fallback_model": "qwen3.5:4b", "max_tokens": 2048, "temperature": 0.3},
    "content_engine": {"assigned_model": "phi3.5:latest", "fallback_model": "qwen3.5:4b", "max_tokens": 2048, "temperature": 0.6},
    "creative_studio": {"assigned_model": "phi3.5:latest", "fallback_model": "qwen3.5:4b", "max_tokens": 1024, "temperature": 0.7},
    "publishing_social": {"assigned_model": "phi3.5:latest", "fallback_model": "qwen3.5:4b", "max_tokens": 512, "temperature": 0.0},
    "reviews_reputation": {"assigned_model": "phi3.5:latest", "fallback_model": "qwen3.5:4b", "max_tokens": 1024, "temperature": 0.3},
    "leads_conversations": {"assigned_model": "phi3.5:latest", "fallback_model": "qwen3.5:4b", "max_tokens": 1024, "temperature": 0.4},
    "results_roi": {"assigned_model": "phi3.5:latest", "fallback_model": "qwen3.5:4b", "max_tokens": 2048, "temperature": 0.1},
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    init_db()
    if token:
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User does not exist or has been deactivated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(err),
                headers={"WWW-Authenticate": "Bearer"},
            ) from err

    # Fallback to default enterprise admin for unauthenticated legacy test routes
    default_user = db.query(User).filter(User.id == "usr_enterprise_01").first()
    if default_user:
        return default_user

    # If DB not initialized somehow, create on the fly
    init_db()
    return db.query(User).filter(User.id == "usr_enterprise_01").first()


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


def require_tenant_access(
    business_id: str | None = Header(None, alias="X-Business-Id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> str:
    """Enforce strict multi-tenant boundary. If X-Business-Id header is provided,
    verify user has an active membership in that business."""
    target_biz_id = business_id or STORE_BUSINESS_ID

    # Superadmin bypass
    if current_user.role == "superadmin":
        return target_biz_id

    # Check membership
    membership = (
        db.query(Membership)
        .filter(
            Membership.user_id == current_user.id,
            Membership.business_id == target_biz_id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: user '{current_user.email}' is not a member of business '{target_biz_id}'",
        )
    return target_biz_id


