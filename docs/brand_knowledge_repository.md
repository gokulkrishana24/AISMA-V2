# Brand Knowledge Repository

## Overview
The Brand Knowledge Repository is the persistent, business-scoped knowledge storage layer for AISMA v2. It acts as the central source of truth for all eight AI agents, ensuring that only approved, business-specific knowledge is supplied during agent execution.

## Directory Layout (Phase 4 Filesystem-Backed)

```
BASE_DIR/state/brand_os/
  biz_apex_enterprises/
    documents/
      <document_id>/
        meta.json              # DocumentMeta (business_id, document_id, template_id, etc.)
        version_1/
          chunks.json           # list of ChunkContent for version 1
          meta.json             # VersionRecord (version, change_summary, etc.)
        version_2/...           # Additional versions
    templates/                # optional exported template definitions
    completeness_report.json
```

## Every Record Must Contain

### Core Metadata
- `business_id` - Tenant identifier (required for isolation)
- `document_id` - Unique identifier for the source document
- `template_id` - Which of the 27 templates this knowledge maps to
- `section_id` - Which section within the template
- `version` - Version string (e.g., "v1.0", "v2.3")
- `status` - Content state: draft, imported, pending_approval, approved, rejected, archived
- `source` - Source name/reference
- `created_at` - ISO format timestamp
- `updated_at` - ISO format timestamp
- `created_by` - Who created the record
- `updated_by` - Who last updated the record

### Chunk-Level Metadata (every chunk)
- `business_id`, `document_id`, `template_id`, `section_id`, `version`
- `chunk_id` - Unique chunk identifier
- `content` - The extracted text
- `approved` - Boolean: is this chunk approved?
- `missing` - Boolean: does text contain `[MISSING]` marker?
- `verified` - Boolean: is this claim verified?
- `source_attribution` - `{source_name, source_type, chunk_id}`

### Version Record Metadata
- `version` - Version number
- `previous_version` - Reference to prior version (or None)
- `change_summary` - Description of changes
- `updated_by` - Who made the change
- `updated_at` - ISO timestamp
- `approval_state` - Current approval status
- `source` - Source document reference

## Content States Supported

| State | Description | Agent Access |
|-------|-------------|--------------|
| `draft` | Internal draft, not yet reviewed | Restricted |
| `imported` | Imported from external document | Restricted, requires approval |
| `pending_approval` | Awaiting human approval | Restricted |
| `approved` | Human-approved, safe for agent use | ✅ All agents |
| `rejected` | Failed approval, not for agent use | ❌ Blocked |
| `archived` | Historically preserved, not active | ❌ Blocked |

## Never Convert Draft to Approved
- Draft and unverified knowledge must remain distinguishable
- Never silently convert draft content into approved content
- Approval transitions must be deterministic and validated

## Repository Capabilities

### Create
- `store_document_meta(business_id, document_id, meta)` - Persist DocumentMeta
- `store_version_record(business_id, document_id, version)` - Persist VersionRecord
- `store_chunks(business_id, document_id, version, chunks)` - Persist chunk data
- `ingest_document(file_path, business_id, template_id)` - Full ingestion pipeline

### Read
- `load_document_meta(business_id, document_id)` - Load DocumentMeta
- `load_version_record(business_id, document_id, version)` - Load specific version
- `load_chunks(business_id, document_id, version)` - Load all chunks for version
- `get_audit_log(business_id)` - Read full audit log
- `compute_completeness_report(business_id)` - Compute completeness report

### Update
- New version creation via `create_version()` (adds new version, doesn't overwrite)
- Version restoration via `restore_version()` (creates new version pointing to historical chunks)

### Archive
- `archive_document(business_id, document_id)` - Moves document directory to `_archived_<timestamp>` name
- Audit log entry created on archival

### Delete/Remove
- `delete_chunks(business_id, document_id)` - Remove from vector store
- `clear_collection(vector_store_config)` - Delete entire ChromaDB collection (use with caution)

## Business Scoped Storage

### Directory Isolation
- Each business has its own directory: `state/brand_os/<business_id>/`
- All file operations restricted to authorized business directories
- Path traversal prevention: reject `..` or absolute business_ids
- Cross-tenant access explicitly blocked at storage boundary

### Permission Enforcement
- `PermissionManager.verify_business_id(business_id)` - Validates business_id
- `PermissionManager.check_can_read/write/retrieve()` - Explicit permission checks
- `RepoPermissionError` raised on isolation violations

## Phase 5 Migration Path

### PostgreSQL + pgvector Designed Interfaces
- Repository `add()`, `read()`, `update()`, `delete()`, `archive()` signatures designed for migration
- Vector store interface: `add_chunks()`, `query_chunks()`, `delete_chunks()`, `clear_collection()`
- All schemas use standalone Pydantic models (no base class) to prevent circular imports
- `QueryContext` business_id field enforced at every storage boundary

### Migration Considerations
- Data format JSON → PostgreSQL rows with identical fields
- ChromaDB embeddings → pgvector embeddings (same 384-dimension all-MiniLM-L6-v2 vectors)
- Audit JSONL → PostgreSQL audit table with similar schema
- Version tracking preserved through version numbers and change summaries
- No rewriting of Brand OS logic needed - only storage adapter implementation