# 27-Template Knowledge Library

## Overview
The Brand OS implements a deterministic 27-template registry covering all required Brand OS sections. Each template has a unique ID, name, description, required/optional fields, validation rules, [MISSING]/[VERIFY] markers, and approval requirements.

## Template ID Enum

All template IDs are defined in `src/brand_os/schemas.py` as the `TemplateID` enum:

1. `brand_identity` - Brand Identity
2. `brand_story_and_mission` - Brand Story and Mission
3. `brand_vision_and_values` - Brand Vision and Values
4. `brand_voice_and_tone` - Brand Voice and Tone
5. `communication_guidelines` - Communication Guidelines
6. `target_audience` - Target Audience
7. `customer_personas` - Customer Personas
8. `customer_pain_points` - Customer Pain Points
9. `brand_positioning` - Brand Positioning
10. `value_proposition` - Value Proposition
11. `messaging_pillars` - Messaging Pillars
12. `products_and_services` - Products and Services
13. `pricing_and_offer_policies` - Pricing and Offer Policies
14. `verified_proof_points` - Verified Proof Points
15. `claims_and_evidence_policy` - Claims and Evidence Policy
16. `visual_identity` - Visual Identity
17. `creative_guidelines` - Creative Guidelines
18. `channel_guidelines` - Channel Guidelines
19. `content_strategy` - Content Strategy
20. `seo_and_keyword_context` - SEO and Keyword Context
21. `competitor_intelligence` - Competitor Intelligence
22. `customer_reviews_and_reputation` - Customer Reviews and Reputation
23. `lead_and_conversation_guidelines` - Lead and Conversation Guidelines
24. `publishing_and_approval_rules` - Publishing and Approval Rules
25. `legal_and_compliance_restrictions` - Legal and Compliance Restrictions
26. `performance_and_experiment_learnings` - Performance and Experiment Learnings
27. `knowledge_sources_and_missing_info_register` - Knowledge Sources and Missing Information Register

## Template Structure

Each template entry in `TEMPLATE_REGISTRY` (src/brand_os/templates.py) contains:

```python
TemplateID.BRAND_IDENTITY: {
    "name": "Brand Identity",
    "description": "Core brand identity elements",
    "fields": {
        "brandName": {"type": "required", "validation": "non_empty_string"},
        "tagline": {"type": "optional", "validation": "max_chars(200)"},
        "mission": {"type": "required", "validation": "non_empty_string"},
        "coreValues": {"type": "list", "validation": "min_items(1)", "validation_value": "non_empty_string"},
    },
    "missing": ["[MISSING] brand name or mission statement"],
    "verify": ["[VERIFY] core values alignment with leadership"],
    "approval": "pending",
}
```

## Template Validation

### `validate_template_field(template_id, field_name, field_value)`
Returns list of errors for a single field against the template's rules.

### `get_template_completeness(business_id, populated_data)`
Computes a `BrandCompletenessReport` containing:
- `total_templates`: 27 (fixed)
- `completed_templates`: count with all required fields populated
- `incomplete_templates`: count with missing required fields
- `missing_fields`: list of `template_id.field` strings for empty required fields
- `verification_required`: list of [MISSING]/[VERIFY] indicator strings
- `pending_approvals`: count of templates with `pending_approval` state
- `archived_records`: count of templates with `archived` state
- `last_updated`: timestamp
- `template_status`: per-template breakdown with completed/hasContent/approvalState/missingIndicators/verificationIndicators

## [MISSING] and [VERIFY] Markers

### Preservation Rule
- [MISSING] and [VERIFY] markers are never automatically removed
- Detected deterministically through Python regex scanning
- [MISSING] indicates required fields or information not yet provided
- [VERIFY] indicates claims that require evidence/verification

### Detection
- `detect_markers(text)` in `src/brand_os/validation.py` uses regex patterns
- `detect_missing_verify_markers()` in `src/brand_os/chunking.py` checks for `[MISSING]`/`[VERIFY]` strings
- Both detection functions are called during ingestion and RAG retrieval

## Template Completeness States

| State | Description |
|-------|-------------|
| Complete | All required fields have non-empty values |
| Incomplete | One or more required fields are empty |
| Requires Verification | [VERIFY] markers present in content |
| Pending Approval | Approval state is `pending_approval` |
| Not Configured | Template has no populated data |

## Per-Template Breakdown

The `BrandCompletenessReport.template_status` dict contains entries for each `TemplateID.value`:
- `completed`: boolean indicating if all required fields met
- `hasContent`: boolean indicating if any content exists beyond metadata
- `approvalState`: current `KnowledgeStatus` value
- `missingIndicators`: list of `[MISSING]` descriptions from template
- `verificationIndicators`: list of `[VERIFY]` descriptions from template