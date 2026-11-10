# Brand Knowledge Versioning

## Overview
Immutable version tracking for AISMA v2 Brand OS knowledge. Every document update creates a new version record, preserving previous versions through a chain. Version transitions are deterministic and validated through the governance system.

## Version Lifecycle

### Example Lifecycle: draft → pending_approval → approved

```text
v1.0 (draft) 
  → v1.1 (pending_approval) 
  → v1.2 (approved) 
  → v1.3 (approved, with updates) 
  → v2.0 (restored from v1.2) 
  → v2.1 (new updates after restore)
```

### Key Properties

| Property | Description |
|----------|-------------|
| **Immutable** | Previous versions never overwritten; new version always created |
| **Traced** | Every version linked to previous via `previous_version` field |
| **Audited** | `create_version()` and `restore_version()` both append audit log entries |
| **Deterministic** | Version numbering follows strict increment pattern |
| **Controlled** | Only authorized humans can approve; agents cannot self-approve |

## Version Record Structure

### `VersionRecord` Schema (src/brand_os/schemas.py)
```python
class VersionRecord:
    version: StrictStr              # e.g., "v1.0", "v2.3"
    previous_version: Optional[StrictStr] = None  # e.g., "v1.0"
    change_summary: StrictStr = ""  # Human-readable change description
    updated_by: StrictStr           # Who made the change
    updated_at: StrictStr           # ISO format timestamp
    approval_state: ApprovalState   # draft, pending_approval, approved, rejected, archived
    source: StrictStr               # Source document/reference
```

### Per-Version Tracking
- `version` - Monotonically increasing: v1, v2, v3, etc.
- `previous_version` - Link to prior version (None for first version)
- `change_summary` - Why this version was created
- `approval_state` - Current state of this version
- `source` - Original source or restoration marker

## Version Creation

### `create_version()` (src/brand_os/versioning.py)

```python
def create_version(
    business_id: str,
    document_id: str,
    *,
    change_summary: str,
    updated_by: str,
    source: str,
    approval_state: ApprovalState = ApprovalState.PENDING,
) -> VersionRecord:
```

#### Process
1. `PermissionManager.check_business_id(business_id)` - Validate tenant
2. `load_version_records(business_id, document_id)` - Get existing versions
3. Determine `prev_version` - Last version in the chain
4. Compute `new_v` - Increment: `v{int(prev_version[1:]) + 1}` if numeric, else `v{len(records) + 1}`
5. Create `VersionRecord` with:
   - `version=new_v`
   - `previous_version=prev_version`
   - `change_summary` as provided
   - `updated_by` as provided
   - `updated_at` - ISO timestamp
   - `approval_state` as provided (default PENDING)
   - `source` as provided
6. `store_version_record(business_id, document_id, rec)` - Persist
7. `_append_audit(business_id, "version_created", ...)` - Audit log

#### Version Numbering Rules
- First version: `v1.0` (or `v1` depending on implementation)
- Increment: `v1 → v2 → v3` etc.
- If previous version is `v1.0`, new is `v2.0`
- If previous version is `v1`, new is `v2`
- Restoration creates new increment version (not a return to old version)

## Version Restoration

### `restore_version()` (src/brand_os/versioning.py)

```python
def restore_version(
    business_id: str,
    document_id: str,
    target_version: str,
    *,
    updated_by: str,
) -> DocumentMeta:
```

#### Process
1. `PermissionManager.check_business_id(business_id)` - Validate tenant
2. `load_document_meta(business_id, document_id)` - Get current document meta
3. `load_chunks(business_id, document_id, version=target_version)` - Get historical chunks
4. **Validation**: Raise `ValueError` if target_version chunks not found
5. `create_version()` - Create new increment version with:
   - `change_summary=f"Restored from {target_version}"`
   - `source=f"restoration_of_{target_version}"`
   - `approval_state=ApprovalState.PENDING`
6. **Re-save chunks** with new version tag:
   - Each chunk `model_copy(update={"version": new_rec.version, "chunk_id": f"{c.section_id}_{new_rec.version}"})`
   - `store_chunks(business_id, document_id, restored_chunks, version=new_rec.version)`
7. Update document metadata with new version
8. `_append_audit(business_id, "version_restored", ...)` - Audit log

#### Restoration Guarantees
- Original historical chunks preserved (never modified)
- New version created with incremented number
- Restoration explicitly marked in source/change_summary
- Previous version chain intact (new version appended, not replacing)

## Version Comparison

### `compare_versions()` (src/brand_os/versioning.py)

```python
def compare_versions(
    business_id: str,
    document_id: str,
    v1: str,
    v2: str,
) -> dict[str, Any]:
```

#### Returns
```python
{
    "document_id": "...",
    "from_version": "v1.0",
    "to_version": "v2.3",
    "diff_lines": [...],  # unified diff output
    "added_lines": int,
    "removed_lines": int,
}
```

#### Process
1. Load chunks for v1 and v2
2. Extract text content from chunks
3. Generate `difflib.unified_diff()` between the two version's texts
4. Count added/removed lines
5. Return structured diff result

## Audit Logging for Versions

Every version operation creates an audit log entry:

### `version_created` Entry
```json
{
    "business_id": "...",
    "action": "version_created",
    "timestamp": "2024-01-15T10:30:00Z",
    "details": {
        "document_id": "...",
        "new_version": "v2.0",
        "updated_by": "human_admin",
        "summary": "Updated pricing policy per compliance review"
    }
}
```

### `version_restored` Entry
```json
{
    "business_id": "...",
    "action": "version_restored",
    "timestamp": "2024-01-15T10:45:00Z",
    "details": {
        "document_id": "...",
        "new_version": "v2.1",
        "restored_from": "v1.2",
        "updated_by": "human_admin"
    }
}
```

## Approval Workflow Integration

### Version State Transitions

| From → To | Allowed? | Notes |
|-----------|----------|-------|
| draft → pending_approval | ✅ | Human must explicitly approve |
| pending_approval → approved | ✅ | After human approval |
| approved → rejected | ✅ | Human escalation |
| approved → draft | ❌ | Not allowed (would lose approval) |
| any → rejected | ✅ | Terminal state |
| any → archived | ✅ | For historical preservation |
| PENDING → APPROVED | ✅ | Governance API call required |
| DRAFT → PENDING_APPROVAL | ✅ | Ingestion pipeline sets this |

### Agent Restrictions
- **An agent must not approve its own knowledge**
- Agents must retrieve approved/current versions by default
- Version restoration requires human `updated_by` actor
- Approval transitions through governance APIs, not frontend-only state changes

## Phase 5 Migration Considerations

### PostgreSQL + pgvector
- Version records map to PostgreSQL rows with identical columns
- `previous_version` forms a self-referential foreign key
- Audit log can be persisted in separate table with version foreign key
- Version numbering preserved through application logic (not DB sequence)
- Restoration logic unchanged - only storage adapter swap

### Key Invariants Preserved Across Migration
- Every update creates new version, never overwrites old
- `previous_version` chain maintained
- Audit entries for every version operation
- Approval states validated through same deterministic logic
- Restoration creates increment version, doesn't return to old version