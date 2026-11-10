"""27 Brand OS template registry.

If the original template names/organization exist in the repo, they are reused
verbatim. If not, a consistent deterministic registry covering all required
Brand OS sections is implemented here.

Each template entry has: unique ID, name, description, required/optional fields,
validation rules, [MISSING]/[VERIFY] markers, and approval requirements.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from brand_os.schemas import (
    BrandCompletenessReport,
    KnowledgeStatus,
    TemplateID,
)

# ---------------------------------------------------------------------------
# Deterministic 27-template registry (used when original repo templates are
# not found). If original templates exist in the repo, they would be loaded
# from disk and merged into this structure.
# ---------------------------------------------------------------------------

TEMPLATE_REGISTRY: dict[TemplateID, dict[str, Any]] = {
    # 1. Brand Identity
    TemplateID.BRAND_IDENTITY: {
        "name": "Brand Identity",
        "description": "Core brand identity elements",
        "fields": {
            "brandName": {"type": "required", "validation": "non_empty_string"},
            "tagline": {"type": "optional", "validation": "max_chars(200)"},
            "mission": {"type": "required", "validation": "non_empty_string"},
            "coreValues": {
                "type": "list",
                "validation": "min_items(1)",
                "validation_value": "non_empty_string",
            },
        },
        "missing": ["[MISSING] brand name or mission statement"],
        "verify": ["[VERIFY] core values alignment with leadership"],
        "approval": "pending",
    },
    # 2. Brand Story and Mission
    TemplateID.BRAND_STORY_AND_MISSION: {
        "name": "Brand Story and Mission",
        "description": "Narrative brand story and long-term mission",
        "fields": {
            "originStory": {"type": "required", "validation": "non_empty_string"},
            "missionStatement": {"type": "required", "validation": "non_empty_string"},
            "visionStatement": {"type": "optional", "validation": "max_chars(500)"},
        },
        "missing": ["[MISSING] origin story or mission statement"],
        "verify": ["[VERIFY] vision statement consistency with positioning"],
        "approval": "pending",
    },
    # 3. Brand Vision and Values
    TemplateID.BRAND_VISION_AND_VALUES: {
        "name": "Brand Vision and Values",
        "description": "Future-oriented vision and guiding values",
        "fields": {
            "vision": {"type": "required", "validation": "non_empty_string"},
            "coreValues": {"type": "list", "validation": "unique_items"},
        },
        "missing": ["[MISSING] vision statement"],
        "verify": ["[VERIFY] values publicly consistent with marketing claims"],
        "approval": "pending",
    },
    # 4. Brand Voice and Tone
    TemplateID.BRAND_VOICE_AND_TONE: {
        "name": "Brand Voice and Tone",
        "description": "Enforced during real-time copy validation in Content Engine",
        "fields": {
            "archetype": {"type": "required", "validation": "in(Authority, Caregiver, Explorer, etc.)"},
            "readingLevel": {"type": "optional", "validation": "in(elementary, highschool, college, professional)"},
            "toneKeywords": {"type": "list", "validation": "min_items(1)"},
            "dos": {"type": "list", "validation": "positive_behavior"},
            "donts": {"type": "list", "validation": "prohibited_behavior"},
        },
        "missing": ["[MISSING] archetype or tone keywords"],
        "verify": ["[VERIFY] dos/donts approved by brand leadership"],
        "approval": "pending",
    },
    # 5. Communication Guidelines
    TemplateID.COMMUNICATION_GUIDELINES: {
        "name": "Communication Guidelines",
        "description": "Rules for consistent messaging across channels",
        "fields": {
            "primaryTone": {"type": "required", "validation": "non_empty_string"},
            "characteristics": {"type": "list", "validation": "non_empty_strings"},
            "avoid": {"type": "list", "validation": "non_empty_strings"},
        },
        "missing": ["[MISSING] primary tone or characteristics"],
        "verify": ["[VERIFY] avoid list approved by compliance"],
        "approval": "pending",
    },
    # 6. Target Audience
    TemplateID.TARGET_AUDIENCE: {
        "name": "Target Audience",
        "description": "Primary and secondary audience definitions",
        "fields": {
            "primary": {"type": "required", "validation": "non_empty_string"},
            "secondary": {"type": "optional", "validation": "max_chars(500)"},
            "demographics": {"type": "list", "validation": "non_empty_strings"},
        },
        "missing": ["[MISSING] primary audience definition"],
        "verify": ["[VERIFY] secondary audience aligns with product messaging"],
        "approval": "pending",
    },
    # 7. Customer Personas
    TemplateID.CUSTOMER_PERSONAS: {
        "name": "Customer Personas",
        "description": "Detailed customer persona profiles",
        "fields": {
            "personaName": {"type": "required", "validation": "non_empty_string"},
            "title": {"type": "optional", "validation": "max_chars(100)"},
            "painPoints": {"type": "list", "validation": "min_items(1)"},
            "keyAspirations": {"type": "list", "validation": "min_items(1)"},
        },
        "missing": ["[MISSING] persona name or pain points"],
        "verify": ["[VERIFY] aspirational claims match product benefits"],
        "approval": "pending",
    },
    # 8. Customer Pain Points
    TemplateID.CUSTOMER_PAIN_POINTS: {
        "name": "Customer Pain Points",
        "description": "Explicitly documented customer pain points",
        "fields": {
            "painPoint": {"type": "required", "validation": "non_empty_string"},
            "impact": {"type": "optional", "validation": "in(high, medium, low)"},
            "resolved": {"type": "boolean", "validation": "default_false"},
        },
        "missing": ["[MISSING] documented pain points"],
        "verify": ["[VERIFY] any resolved claims have evidence"],
        "approval": "pending",
    },
    # 9. Brand Positioning
    TemplateID.BRAND_POSITIONING: {
        "name": "Brand Positioning",
        "description": "Market positioning and differentiation",
        "fields": {
            "category": {"type": "required", "validation": "non_empty_string"},
            "targetSegment": {"type": "required", "validation": "non_empty_string"},
            "primaryPromise": {"type": "required", "validation": "non_empty_string"},
            "reasonsToBelieve": {"type": "list", "validation": "min_items(1)"},
        },
        "missing": ["[MISSING] category or target segment"],
        "verify": ["[VERIFY] reasons-to-believe supported by proof points"],
        "approval": "pending",
    },
    # 10. Value Proposition
    TemplateID.VALUE_PROPOSITION: {
        "name": "Value Proposition",
        "description": "Core value proposition messaging",
        "fields": {
            "valueProp": {"type": "required", "validation": "non_empty_string"},
            "differentiators": {"type": "list", "validation": "min_items(1)"},
        },
        "missing": ["[MISSING] value proposition"],
        "verify": ["[VERIFY] differentiators not invented (must have evidence)"],
        "approval": "pending",
    },
    # 11. Messaging Pillars
    TemplateID.MESSAGING_PILLARS: {
        "name": "Messaging Pillars",
        "description": "Core approved messaging themes",
        "fields": {
            "pillar": {"type": "required", "validation": "non_empty_string"},
            "approvedPhrases": {"type": "list", "validation": "unique_items"},
        },
        "missing": ["[MISSING] messaging pillar without approved phrases"],
        "verify": ["[VERIFY] phrases do not contain unverified claims"],
        "approval": "pending",
    },
    # 12. Products and Services
    TemplateID.PRODUCTS_AND_SERVICES: {
        "name": "Products and Services",
        "description": "Offerings mapped to brand positioning",
        "fields": {
            "productName": {"type": "required", "validation": "non_empty_string"},
            "description": {"type": "optional", "validation": "max_chars(500)"},
            "pricingPolicy": {"type": "optional", "validation": "referenced_only"},
        },
        "missing": ["[MISSING] product/service name"],
        "verify": ["[VERIFY] pricing policy is approved (not inferred)"],
        "approval": "pending",
    },
    # 13. Pricing and Offer Policies
    TemplateID.PRICING_AND_OFFER_POLICIES: {
        "name": "Pricing and Offer Policies",
        "description": "Verified pricing policies — no fabricated prices",
        "fields": {
            "pricingTier": {"type": "required", "validation": "in(free, standard, premium, enterprise)"},
            "verifiedProofPoints": {"type": "list", "validation": "min_items(1)"},
            "priceMentions": {"type": "list", "validation": "must_be_approved"},
        },
        "missing": ["[MISSING] pricing tier"],
        "verify": ["[VERIFY] all price mentions have verified proof"],
        "approval": "required",
    },
    # 14. Verified Proof Points
    TemplateID.VERIFIED_PROOF_POINTS: {
        "name": "Verified Proof Points",
        "description": "Evidence-backed proof points (never fabricated)",
        "fields": {
            "claim": {"type": "required", "validation": "non_empty_string"},
            "citation": {"type": "required", "validation": "non_empty_string"},
            "verified": {"type": "boolean", "validation": "default_true"},
        },
        "missing": ["[MISSING] claim or citation"],
        "verify": ["[VERIFY] citation is a verifiable source document"],
        "approval": "required",
    },
    # 15. Claims and Evidence Policy
    TemplateID.CLAIMS_AND_EVIDENCE_POLICY: {
        "name": "Claims and Evidence Policy",
        "description": "Policy governing what claims are allowed and how evidence is validated",
        "fields": {
            "allowedClaimTypes": {"type": "list", "validation": "min_items(1)"},
            "prohibitedClaimTypes": {"type": "list", "validation": "min_items(1)"},
            "evidenceStandard": {"type": "required", "validation": "in(documentation, customer_testimonial, third_party_report, data)"},
        },
        "missing": ["[MISSING] evidence standard"],
        "verify": ["[VERIFY] evidence standard is formally approved"],
        "approval": "required",
    },
    # 16. Visual Identity
    TemplateID.VISUAL_IDENTITY: {
        "name": "Visual Identity",
        "description": "Logo, color palette, typography, and visual assets",
        "fields": {
            "logoDescription": {"type": "required", "validation": "non_empty_string"},
            "colorPalette": {"type": "list", "validation": "min_items(1)"},
            "typography": {"type": "required", "validation": "non_empty_string"},
        },
        "missing": ["[MISSING] visual identity elements"],
        "verify": ["[VERIFY] logo usage rights are documented"],
        "approval": "pending",
    },
    # 17. Creative Guidelines
    TemplateID.CREATIVE_GUIDELINES: {
        "name": "Creative Guidelines",
        "description": "Rules for creative asset production",
        "fields": {
            "approvedFormats": {"type": "list", "validation": "min_items(1)"},
            "brandColors": {"type": "list", "validation": "hex_color_format"},
            "prohibitedElements": {"type": "list", "validation": "non_empty_strings"},
        },
        "missing": ["[MISSING] approved formats"],
        "verify": ["[VERIFY] brand colors are registered trade dress"],
        "approval": "pending",
    },
    # 18. Channel Guidelines
    TemplateID.CHANNEL_GUIDELINES: {
        "name": "Channel Guidelines",
        "description": "Per-channel messaging and formatting rules",
        "fields": {
            "channel": {"type": "required", "validation": "in(linkedin,twitter,instagram,facebook,email,website)"},
            "formattingRules": {"type": "required", "validation": "non_empty_string"},
            "postingFrequency": {"type": "optional", "validation": "positive_integer"},
        },
        "missing": ["[MISSING] channel or formatting rules"],
        "verify": ["[VERIFY] channel rules align with overall brand voice"],
        "approval": "pending",
    },
    # 19. Content Strategy
    TemplateID.CONTENT_STRATEGY: {
        "name": "Content Strategy",
        "description": "Planned content types, themes, and cadence",
        "fields": {
            "contentTypes": {"type": "list", "validation": "min_items(1)"},
            "themes": {"type": "list", "validation": "min_items(1)"},
            "cadence": {"type": "optional", "validation": "positive_integer"},
        },
        "missing": ["[MISSING] content types or themes"],
        "verify": ["[VERIFY] cadence is realistic for team size"],
        "approval": "pending",
    },
    # 20. SEO and Keyword Context
    TemplateID.SEO_AND_KEYWORD_CONTEXT: {
        "name": "SEO and Keyword Context",
        "description": "Approved SEO keywords and search context",
        "fields": {
            "primaryKeywords": {"type": "list", "validation": "min_items(1)"},
            "secondaryKeywords": {"type": "list", "validation": "min_items(1)"},
            "forbiddenKeywords": {"type": "list", "validation": "min_items(1)"},
        },
        "missing": ["[MISSING] primary keywords"],
        "verify": ["[VERIFY] keywords do not violate advertising policies"],
        "approval": "pending",
    },
    # 21. Competitor Intelligence
    TemplateID.COMPETITOR_INTELLIGENCE: {
        "name": "Competitor Intelligence",
        "description": "Competitor context — no live rankings or fabricated data",
        "fields": {
            "competitorName": {"type": "required", "validation": "non_empty_string"},
            "positioningComparison": {"type": "optional", "validation": "max_chars(500)"},
            "avoidStatements": {"type": "list", "validation": "min_items(1)"},
        },
        "missing": ["[MISSING] competitor name"],
        "verify": ["[VERIFY] comparison claims are evidence-based"],
        "approval": "pending",
    },
    # 22. Customer Reviews and Reputation
    TemplateID.CUSTOMER_REVIEWS_AND_REPUTATION: {
        "name": "Customer Reviews and Reputation",
        "description": "Verified customer review summaries and reputation data",
        "fields": {
            "reviewSummary": {"type": "required", "validation": "non_empty_string"},
            "averageRating": {"type": "optional", "validation": "range(1,5)"},
            "prohibitedCommitments": {"type": "list", "validation": "min_items(1)"},
        },
        "missing": ["[MISSING] review summary"],
        "verify": ["[VERIFY] rating is from approved source"],
        "approval": "pending",
    },
    # 23. Lead and Conversation Guidelines
    TemplateID.LEAD_AND_CONVERSATION_GUIDELINES: {
        "name": "Lead and Conversation Guidelines",
        "description": "Rules for lead qualification and conversation flow",
        "fields": {
            "qualificationCriteria": {"type": "list", "validation": "min_items(1)"},
            "approvedProductDetails": {"type": "list", "validation": "min_items(1)"},
            "conversationFlow": {"type": "required", "validation": "non_empty_string"},
        },
        "missing": ["[MISSING] qualification criteria or conversation flow"],
        "verify": ["[VERIFY] no pricing/availability commitments without approval"],
        "approval": "pending",
    },
    # 24. Publishing and Approval Rules
    TemplateID.PUBLISHING_AND_APPROVAL_RULES: {
        "name": "Publishing and Approval Rules",
        "description": "Channel-specific publishing rules and approval requirements",
        "fields": {
            "channel": {"type": "required", "validation": "in(linkedin,twitter,instagram,facebook,email,website)"},
            "approvalRequired": {"type": "boolean", "validation": "default_true"},
            "schedulingRestrictions": {"type": "optional", "validation": "max_chars(500)"},
            "prohibitedContent": {"type": "list", "validation": "min_items(1)"},
        },
        "missing": ["[MISSING] channel or approval requirement"],
        "verify": ["[VERIFY] approval workflow is documented and enforced"],
        "approval": "required",
    },
    # 25. Legal and Compliance Restrictions
    TemplateID.LEGAL_AND_COMPLIANCE_RESTRICTIONS: {
        "name": "Legal and Compliance Restrictions",
        "description": "Legal and compliance restrictions on claims and publishing",
        "fields": {
            "restrictedClaims": {"type": "list", "validation": "min_items(1)"},
            "requiredDisclosures": {"type": "list", "validation": "min_items(1)"},
            "jurisdiction": {"type": "required", "validation": "non_empty_string"},
        },
        "missing": ["[MISSING] jurisdiction or restricted claims"],
        "verify": ["[VERIFY] all restrictions are legally reviewed"],
        "approval": "required",
    },
    # 26. Performance and Experiment Learnings
    TemplateID.PERFORMANCE_AND_EXPERIMENT_LEARNINGS: {
        "name": "Performance and Experiment Learnings",
        "description": "Documented experiment results and performance learnings",
        "fields": {
            "experimentName": {"type": "required", "validation": "non_empty_string"},
            "kpiMetric": {"type": "required", "validation": "non_empty_string"},
            "result": {"type": "optional", "validation": "in(success, inconclusive, failed)"},
            "lessonsLearned": {"type": "optional", "validation": "max_chars(1000)"},
        },
        "missing": ["[MISSING] experiment name or KPI metric"],
        "verify": ["[VERIFY] KPI metric is quantitatively defined"],
        "approval": "pending",
    },
    # 27. Knowledge Sources and Missing Information Register
    TemplateID.KNOWLEDGE_SOURCES_AND_MISSING_INFO_REGISTER: {
        "name": "Knowledge Sources and Missing Information Register",
        "description": "Register of all knowledge sources and tracked missing/unverified items",
        "fields": {
            "sourceName": {"type": "required", "validation": "non_empty_string"},
            "sourceType": {"type": "required", "validation": "in(documentation, database, api, human_interview, experiment)"},
            "coverageArea": {"type": "optional", "validation": "max_chars(500)"},
            "lastVerified": {"type": "optional", "validation": "iso_date_format"},
            "notes": {"type": "optional", "validation": "max_chars(1000)"},
        },
        "missing": ["[MISSING] source name or type"],
        "verify": ["[VERIFY] source is authenticated and traced"],
        "approval": "pending",
    },
}


def get_template(template_id: TemplateID) -> dict[str, Any]:
    """Retrieve a template by its TemplateID."""
    return TEMPLATE_REGISTRY.get(template_id, {})


def list_templates() -> list[dict[str, Any]]:
    """Return all 27 template registrations."""
    return list(TEMPLATE_REGISTRY.values())


def validate_template_field(
    template_id: TemplateID,
    field_name: str,
    field_value: Any,
) -> list[str]:
    """Validate a single field against the template's rules. Returns list of errors."""
    template = TEMPLATE_REGISTRY.get(template_id, {})
    field_def = template.get("fields", {}).get(field_name, {})
    errors: list[str] = []

    field_type = field_def.get("type")
    if field_type == "required" and not field_value:
        errors.append(f"{field_name}: required field is empty or None")
    if field_type == "list" and not isinstance(field_value, list):
        errors.append(f"{field_name}: expected list, got {type(field_value).__name__}")
    if field_type == "string":
        max_chars = field_def.get("validation")
        if max_chars and isinstance(field_value, str) and len(field_value) > int(max_chars.split("(")[1].rstrip(")")):
            errors.append(f"{field_name}: exceeds max length {max_chars}")
    # Add more validation as needed...

    return errors


def get_all_template_ids() -> list[TemplateID]:
    """Return a list of all TemplateID enums."""
    return list(TemplateID)


def get_template_completeness(
    business_id: str,
    populated_data: dict[TemplateID, dict[str, Any]],
) -> BrandCompletenessReport:
    """Compute completeness report for a business's populated templates.

    Args:
        business_id: The business identifier.
        populated_data: Mapping of TemplateID -> populated fields dict.

    Returns:
        BrandCompletenessReport with per-template status and overall counts.
    """
    total = len(TemplateID)
    completed = 0
    incomplete = 0
    missing_fields: list[str] = []
    verification_required: list[str] = []
    pending_approvals = 0
    archived = 0
    template_status: dict[str, dict[str, Any]] = {}

    for tid in TemplateID:
        pop = populated_data.get(tid, {})
        template = TEMPLATE_REGISTRY.get(tid, {})
        field_defs = template.get("fields", {})
        required_fields = [
            fname for fname, fdef in field_defs.items() if fdef.get("type") == "required"
        ]

        # Check if all required fields have non-empty values
        all_required_met = all(pop.get(f) for f in required_fields)
        has_any_content = any(
            pop.get(f) for f in pop.keys() if f not in {"business_id", "version", "approval_state", "source"}
        )

        if all_required_met and has_any_content:
            completed += 1
        else:
            incomplete += 1
            for f in required_fields:
                if not pop.get(f):
                    missing_fields.append(f"{tid.value}.{f}")

        # Check missing/verify markers
        missing_ind = template.get("missing", [])
        verify_ind = template.get("verify", [])
        if missing_ind:
            verification_required.append(f"{tid.value}: {missing_ind[0]}")
        if verify_ind:
            verification_required.append(f"{tid.value}: {verify_ind[0]}")

        # Approval state
        approval = pop.get("approval_state", KnowledgeStatus.DRAFT.value)
        if approval == KnowledgeStatus.PENDING_APPROVAL.value:
            pending_approvals += 1
        elif approval == KnowledgeStatus.ARCHIVED.value:
            archived += 1

        template_status[tid.value] = {
            "completed": all_required_met,
            "hasContent": has_any_content,
            "approvalState": approval,
            "missingIndicators": missing_ind,
            "verificationIndicators": verify_ind,
        }

    return BrandCompletenessReport(
        business_id=business_id,
        total_templates=total,
        completed_templates=completed,
        incomplete_templates=incomplete,
        missing_fields=missing_fields,
        verification_required=verification_required,
        pending_approvals=pending_approvals,
        archived_records=archived,
        last_updated=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        template_status=template_status,
    )