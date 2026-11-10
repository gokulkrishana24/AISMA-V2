# Brand Governance

## Overview
Governance engine for AISMA v2 Brand OS, integrating with existing Phase 1 modules (permissions, audit, killswitch, policy, budget) while adding Brand OS-specific controls.

## Mandatory Controls (Phase 4)

### Default Deny
- If business_id cannot be verified, deny all access
- Fail-closed when permissions cannot be verified
- Storage operations reject unauthorized business_ids immediately

### Least Privilege
- Minimum necessary data accessible per operation
- Agents only receive relevant brand context (never entire Brand OS)
- RAG retrieval enforces approved-only + business_id filtering

### Tenant Isolation
- Every record must contain `business_id`
- All repository operations restricted to authorized business directories
- Vector store queries enforce `business_id` at storage boundary
- Cross-tenant access explicitly blocked

### Kill-Switch Enforcement
- `getKillSwitchStatus()` → `GET /api/v1/governance/killswitch`
- `toggleKillSwitch(engaged, reason)` → `POST /api/v1/governance/killswitch`
- When engaged, all agent execution blocked
- Frontend shows distinct governance block (not ordinary network error)

### Permission Checks
- `PermissionManager.verify_business_id(business_id)`
- `PermissionManager.check_can_read_business_data(business_id)`
- `PermissionManager.check_can_write_brand_knowledge(business_id, actor)`
- `PermissionManager.check_can_retrieve_brand_knowledge(business_id, agent_id)`
- `PermissionManager.check_approval_access()` - Deterministic state transition check

### Audit Logging
- Every ingestion, version, retrieval, and governance operation appends to JSONL audit log
- Log location: `state/brand_os/<business_id>/audit.jsonl`
- Each entry: `business_id`, `action`, `timestamp`, `details`
- Chain validation: SHA-256 hash-chained entries (verified via `verifyAuditChain()`)

### Injection Scanning
- Untrusted content scanned before indexing
- Prompt injection patterns detected during ingestion
- [MISSING]/[VERIFY] markers preserved as detection results, not removed

### Budget Controls (Where Applicable)
- Budget enforcer integration from Phase 1
- Spend tracking per agent/channel
- Cap alerts when approaching monthly budget
- Budget warnings in agent execution context

### Output Validation
- Structured JSON output validated against schemas
- Extra="forbid" on all Pydantic models prevents silent data injection
- Linters and scorers run on generated content

## Brand OS-Specific Governance

### Template Validation
- `validate_template_data(template_id, data)` - Validates complete data against registered template
- Required fields must be non-empty
- Field validation rules: `non_empty_string`, `max_chars()`, `min_items()`
- [MISSING] and [VERIFY] markers tracked, never removed

### Approval Workflow
- `create_version()` sets `approval_state=PENDING` by default
- `ingest_document()` sets `approval_state` based on `require_approval` flag
- `BrandCompletenessReport.pending_approvals` counts pending templates
- Only human users can transition `pending_approval → approved`

### Source Attribution
- Every piece of knowledge supplied to agents carries evidence references
- `document_id`, `template_id`, `section_id`, `version`, `source_name`
- `validate_source_claim(claim, supporting_chunks)` - Determines if claim supported
- `attach_attribution_to_output(output, source_chunks)` - Adds evidence to agent output
- If no source supports a claim: identified as unsupported/requiring verification

### Missing Information Handling
- `[MISSING]` indicators surfaced in RAG context
- `BrandCompletenessReport.missing_fields` lists gaps
- Agents must not fabricate facts to fill [MISSING] gaps
- Missing information propagated through context, not invented

### Unverified Claims
- `[VERIFY]` markers detected and surfaced
- `BrandCompletenessReport.verification_required` lists items
- Agents must not convert unverified suggestions into brand facts
- Distinction maintained: source-supported facts vs. LLM suggestions vs. missing vs. unverified

## Governance API Endpoints (Existing Phase 1)

### Killswitch
- `GET /api/v1/governance/killswitch` → `KillSwitchStatus`
- `POST /api/v1/governance/killswitch` → `engaged, reason`

### Audit
- `GET /api/v1/governance/audit` → `{entries, chain_valid}`
- `POST /api/v1/governance/audit/verify` → `{valid, verifiedCount, message}`

### Approvals (if applicable)
- Governance API calls for approval transitions
- Never frontend-only bypass

## Failure Modes (Fail-Closed)

### Business Identity Missing
- `PermissionError: business_id is required for Brand OS operations`
- All operations fail; no silent fallback

### Permissions Cannot Be Verified
- `PermissionError: Invalid business_id: ...`
- Operation denied, audit log entry created

### Storage Metadata Malformed
- `ValueError: Mandatory metadata missing: field_name`
- Vector store rejects chunk with incomplete metadata

### Approval State Unknown
- Chunks with `approved=False` filtered from RAG retrieval
- Agent receives `[MISSING]` context instead of invalid data

### Kill-Switch State Cannot Be Read
- All agent execution blocked when engaged
- Frontend displays distinct governance error block

### Tenant Filters Cannot Be Enforced
- Cross-tenant query blocked at storage boundary
- `RepoPermissionError` raised on isolation violation

### Security Validation Fails
- Invalid file format → `ValueError`
- Oversized file → `ValueError`
- Bad encoding → `ValueError`
- All rejected with explicit error, not silent fallback