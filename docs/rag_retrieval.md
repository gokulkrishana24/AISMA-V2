# RAG Retrieval Pipeline

## Overview
The Retrieval-Augmented Generation (RAG) pipeline for AISMA v2 Brand OS implements approved-only, tenant-isolated retrieval with source attribution and missing/unverified detection. All processing is deterministic Python logic.

## Pipeline Input

### `QueryContext` Parameters
- `business_id` (StrictStr) - **Required**: Tenant isolation boundary
- `agent_id` (StrictStr) - The requesting agent (e.g., "search_visibility")
- `task_id` (Optional[str]) - Task identifier
- `query` (StrictStr) - User objective or query text
- `template_filters` (Optional[List[TemplateID]]) - Filter by template IDs
- `source_filters` (Optional[List[StrictStr]]) - Filter by source names
- `requested_top_k` (int, default=5, ge=1, le=20) - Maximum chunks to return

### Example QueryContext
```python
QueryContext(
    business_id="biz_apex_enterprises",
    agent_id="content_engine",
    task_id="task_001",
    query="What are our approved pricing policies?",
    requested_top_k=5,
)
```

## Pipeline Processing Steps

### Step 1: Validate Pipeline Input
- `_validate_pipeline_input(query_context)`
- Raises `ValueError` if `business_id` missing
- Kill switch checked by caller (not in core pipeline)

### Step 2: Embed Query Locally
- `_embed_query(query_context.query)` - Uses singleton SentenceTransformer
- Model: `all-MiniLM-L6-v2` (384 dimensions)
- Raises `RuntimeError` if model not initialized

### Step 3: Vector Store Query with Tenant Isolation
- `query_chunks(query_embedding, query_context, vector_store_config)`
- **Mandatory**: `business_id` filter in `where` clause
- Optional: `template_id` filter if `template_filters` provided
- ChromaDB `where` filter: `{"business_id": query_context.business_id}`
- May prepend `$and` business_id + template_id filters

### Step 4: Enforce Approved-Only Filter
- Each retrieved chunk has `approved` metadata flag
- If `query_context.enforce_approved_only=True` (default), skip unapproved chunks
- Chunks with `approved=False` are filtered out at retrieval time
- If all chunks unapproved, result surfaces `[MISSING] no approved brand knowledge`

### Step 5: Enforce Version Filter
- Current version only enforced via `template_id + section_id + version` combo
- Version matching done through metadata; vector query returns all versions
- Application-level filtering: only chunks matching current version used
- `query_context.enforce_version_filter` (default True)

### Step 6: Rank and Limit
- ChromaDB returns results sorted by similarity (cosine distance)
- `top_k` applied at query time (default 5, max 20)
- Context size limited to 4000 characters (configurable via `RAGRetrievalConfig`)
- Relevance scores returned (0.0 to 1.0, cosine similarity)

### Step 7: Detect [MISSING] / [VERIFY] Markers
- `_detect_missing_verified(retrieved)` - Scans chunk texts
- Sets `result.missing = True` if `[MISSING]` found in text
- Sets `result.verified = True` if `[VERIFY]` found in text (secondary to metadata flag)
- Returns dict with `missing_chunks`, `verify_chunks`, `has_missing`, `has_verified`

### Step 8: Attach Source Attribution
- `extract_source_reference(result)` - Returns dict with:
  - `document_id`, `template_id`, `section_id`, `version`, `source_reference`
- `attach_attribution_to_output(output, source_chunks)` - Adds `evidence` field to agent output
- Output gets `requires_human_approval` flag if any chunk is missing/unapproved

### Step 9: Return Compact Structured Context

```python
{
    "context_text": "[\{template_id}] {text_chunk_summary}|...|",  # joined with \n
    "source_attribution": [
        {"document_id": "...", "template_id": "...", "section_id": "...", "version": "...", "source_reference": "..."},
        ...
    ],
    "missing_info": ["{template_id}: {chunk_text[:200]}", ...],  # [MISSING] summaries
    "verify_info": ["{template_id}: {chunk_text[:200]}", ...],  # [VERIFY] summaries
    "retrieval_metadata": {
        "business_id": "...",
        "agent_id": "...",
        "task_id": "...",
        "requested_top_k": 5,
        "returned_count": 3,
        "total_context_chars": 2100,
        "enforce_approved_only": True,
        "enforce_version_filter": True,
        "no_approved_content": False,  # True if no approved chunks retrieved
    },
}
```

## If No Approved Chunks Retrieved

```python
result["context_text"] = "brand_context=missing"
result["missing_info"].append("[MISSING] no approved brand knowledge found for this query/business")
result["retrieval_metadata"]["no_approved_content"] = True
```

## Source Attribution per Chunk

Each `RetrievalResult` contains:
- `chunk_id` - Unique chunk identifier
- `document_id` - Source document ID
- `template_id` - Template ID (TemplateID enum)
- `section_id` - Section within template
- `version` - Version string
- `relevance_score` - Float 0.0-1.0 (cosine similarity)
- `approved` - Boolean approval flag
- `text` - Chunk content text
- `source_reference` - `f"doc:{document_id}:tid:{template_id}:sid:{section_id}:v:{version}"`
- `missing` - Boolean: `[MISSING]` detected
- `verified` - Boolean: `[VERIFY]` detected

## Tenant Isolation Enforcement

### At Storage Boundary (Backend)
```python
where_filter = {"business_id": query_context.business_id}
# May add: {"$and": [{"business_id": bid}, {"template_id": {"$in": [tids]}}]}
```
- Business_id enforced in ChromaDB query `where` parameter
- **Never** relies on frontend filtering alone
- Cross-tenant access explicitly blocked

### At Pipeline Level
- `business_id` required in `QueryContext` (Pydantic strict field)
- `PermissionManager.verify_business_id()` called in ingestion
- `PermissionManager.check_can_retrieve_brand_knowledge()` for agent authorization

## Version Filtering

### How It Works
- Each chunk stores `version` metadata (e.g., "v1.0", "v2.3")
- Retrieval returns chunks with their associated version
- Application filters to current version only
- Old versions preserved in version history (repository) but not surfaced in default retrieval

### Configuration
- `query_context.enforce_version_filter` (default True)
- When True: only chunks where version matches "current" are included
- When False: all versions returned (use for historical comparison)

## Approved-Only Retrieval

### Why It Matters
- Prevents agents from receiving draft/unverified knowledge
- Ensures only human-approved brand information influences output
- Maintains messaging consistency and compliance

### Implementation
- Each `ChunkContent` has `approved: bool` field
- Set during ingestion: `approved=not (approved_only and (chunk_missing or not _is_approved_content(chunk_text)))`
- In RAG query: `if query_context.enforce_approved_only and not approved: continue`
- If no approved chunks: surface `[MISSING]` rather than empty/invalid context

## Context Size Limits

### Configuration
- `RAGRetrievalConfig.context_size_limit = 4000` (characters)
- Total `context_text` character count computed after joining chunk summaries
- If approaching limit, `top_k` effectively reduced

### Enforcement
- Chunks added to context until `len(context_text) >= context_size_limit`
- Excess chunks skipped with warning in `retrieval_metadata`
- Prevents exceeding local inference token limits (4GB VRAM constraint)

## Graceful Degradation

### Embeddings Unavailable
- `RuntimeError` raised if `embed_query()` called without `initialize()`
- Tests use mocked embeddings
- Normal operation: `AISMA_RUN_REAL_RAG_TESTS=1` for real tests

### Vector Store Unavailable
- `is_initialized()` checks before operations
- Falls back to in-memory mode when ChromaDB not available
- All modules support "not initialized" code path

### Model Mismatch
- If model initialized with different name, warning emitted, new model NOT loaded
- Fail-closed: use already-loaded model or reset module state