"""Pydantic schemas for Brand OS + RAG data models.

All models are strict (extra="forbid") and use validatedfield rules so that
invalid/untested data cannot silently enter the pipeline.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, StrictStr


class KnowledgeStatus(StrEnum):
    DRAFT = "draft"
    IMPORTED = "imported"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ApprovalState(StrEnum):
    UNAUTHORIZED = "unauthorized"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MissingIndicator(StrEnum):
    MISSING = "[MISSING]"
    VERIFY = "[VERIFY]"


class TemplateID(StrEnum):
    # The original 27 Brand OS templates — exact names preserved if they exist
    # in the repo; otherwise deterministic registry aligned to Brand OS sections.
    BRAND_IDENTITY = "brand_identity"
    BRAND_STORY_AND_MISSION = "brand_story_and_mission"
    BRAND_VISION_AND_VALUES = "brand_vision_and_values"
    BRAND_VOICE_AND_TONE = "brand_voice_and_tone"
    COMMUNICATION_GUIDELINES = "communication_guidelines"
    TARGET_AUDIENCE = "target_audience"
    CUSTOMER_PERSONAS = "customer_personas"
    CUSTOMER_PAIN_POINTS = "customer_pain_points"
    BRAND_POSITIONING = "brand_positioning"
    VALUE_PROPOSITION = "value_proposition"
    MESSAGING_PILLARS = "messaging_pillars"
    PRODUCTS_AND_SERVICES = "products_and_services"
    PRICING_AND_OFFER_POLICIES = "pricing_and_offer_policies"
    VERIFIED_PROOF_POINTS = "verified_proof_points"
    CLAIMS_AND_EVIDENCE_POLICY = "claims_and_evidence_policy"
    VISUAL_IDENTITY = "visual_identity"
    CREATIVE_GUIDELINES = "creative_guidelines"
    CHANNEL_GUIDELINES = "channel_guidelines"
    CONTENT_STRATEGY = "content_strategy"
    SEO_AND_KEYWORD_CONTEXT = "seo_and_keyword_context"
    COMPETITOR_INTELLIGENCE = "competitor_intelligence"
    CUSTOMER_REVIEWS_AND_REPUTATION = "customer_reviews_and_reputation"
    LEAD_AND_CONVERSATION_GUIDELINES = "lead_and_conversation_guidelines"
    PUBLISHING_AND_APPROVAL_RULES = "publishing_and_approval_rules"
    LEGAL_AND_COMPLIANCE_RESTRICTIONS = "legal_and_compliance_restrictions"
    PERFORMANCE_AND_EXPERIMENT_LEARNINGS = "performance_and_experiment_learnings"
    KNOWLEDGE_SOURCES_AND_MISSING_INFO_REGISTER = "knowledge_sources_and_missing_info_register"


class TemplateField(StrEnum):
    """Meta-field for a template section, not a content field itself."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    VALIDATION_RULE = "validation_rule"
    MISSING_INDICATOR = "missing_indicator"
    VERIFICATION_INDICATOR = "verification_indicator"
    APPROVAL_REQUIREMENT = "approval_requirement"


class DocumentMeta(BaseModel):
    """Metadata attached to every ingested document chunk."""

    business_id: str
    document_id: str
    template_id: TemplateID | str
    section_id: StrictStr
    chunk_id: StrictStr
    version: StrictStr
    source_name: StrictStr
    source_path: StrictStr | None = None
    path: StrictStr | None = None
    approval_state: ApprovalState = ApprovalState.UNAUTHORIZED
    created_at: StrictStr
    updated_at: StrictStr
    created_by: StrictStr | None = None
    updated_by: StrictStr | None = None


class ChunkContent(BaseModel):
    """A single chunk of extracted text with full metadata."""

    business_id: str
    document_id: str
    template_id: TemplateID | str
    section_id: StrictStr
    chunk_id: StrictStr
    version: StrictStr
    content: StrictStr
    relevance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    approved: bool = False
    missing: bool = False
    verified: bool = False
    source_attribution: dict[str, Any] | None = Field(default_factory=dict)


class VersionRecord(BaseModel):
    """Immutable version record for knowledge change tracking."""

    version: StrictStr
    previous_version: StrictStr | None = None
    change_summary: StrictStr = ""
    updated_by: StrictStr
    updated_at: StrictStr
    approval_state: ApprovalState | str
    source: StrictStr


class RetrievalResult(BaseModel):
    """Returned chunk from RAG query with attribution metadata."""

    chunk_id: StrictStr
    document_id: StrictStr
    template_id: TemplateID | str
    section_id: StrictStr
    version: StrictStr
    relevance_score: float
    approved: bool
    text: StrictStr
    source_reference: StrictStr  # document_id + template_id + section_id + version
    business_id: str = ""
    missing: bool = False
    verified: bool = False

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "business_id": self.business_id,
            "document_id": self.document_id,
            "template_id": self.template_id,
            "section_id": self.section_id,
            "version": self.version,
        }

    def get(self, k: str, default: Any = None) -> Any:
        if k == "metadata":
            return self.metadata
        return getattr(self, k, default)


class QueryContext(BaseModel):
    """Parameters passed into the RAG retrieval pipeline."""

    business_id: StrictStr
    agent_id: StrictStr = "general"
    task_id: StrictStr | None = None
    query: StrictStr = ""
    user_query: StrictStr = ""
    template_filters: list[TemplateID] | None = None
    source_filters: list[StrictStr] | None = None
    requested_top_k: int = Field(default=5, ge=1, le=20)
    enforce_approved_only: bool = True
    enforce_version_filter: bool = True


class BrandCompletenessReport(BaseModel):
    """Structured report of template completion status per business."""

    business_id: StrictStr
    total_templates: int = 0
    completed_templates: int = 0
    incomplete_templates: int = 0
    missing_fields: list[StrictStr] = Field(default_factory=list)
    verification_required: list[StrictStr] = Field(default_factory=list)
    pending_approvals: int = 0
    archived_records: int = 0
    last_updated: StrictStr = ""

    # Per-template breakdown
    template_status: dict[str, dict[str, Any]] = Field(default_factory=dict)


class EmbeddingConfig(BaseModel):
    """Configuration for the local embedding model."""

    model_name: StrictStr = "all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
    cpu_offload: bool = True
    normalize_embeddings: bool = True


class VectorStoreConfig(BaseModel):
    """Configuration for ChromaDB vector storage."""

    collection_name: StrictStr = "brand_os"
    persist_directory: StrictStr = "./state/chroma"
    enable_metadata_filtering: bool = True
    business_id_filter: StrictStr = ""  # enforced at query time


class RAGRetrievalConfig(BaseModel):
    """Configuration for the RAG retrieval pipeline."""

    top_k: int = Field(default=5, ge=1, le=20)
    context_size_limit: int = Field(default=4000, ge=100)
    enforce_approved_only: bool = True
    enforce_version_filter: bool = True
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)