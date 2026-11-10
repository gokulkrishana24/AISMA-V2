# Document Ingestion Pipeline

## Overview
The controlled document ingestion pipeline for AISMA v2 Brand OS validates, extracts, chunks, and stores brand knowledge documents. Every step is deterministic Python logic with no LLM decisions.

## Supported Formats

| Extension | Format | Notes |
|-----------|--------|-------|
| `.md` | Markdown | Primary format |
| `.markdown` | Markdown | |
| `.txt` | Text | Plain text files |
| `.json` | JSON | Structured data |
| `.yaml` / `.yml` | YAML | YAML format |
| `.csv` | CSV | Comma-separated values |

## Unsupported (Phase 4)
- PDF/DOCX - no existing project dependencies for reliable extraction
- Requires additional dependencies for future phases

## Ingestion Workflow (13 Steps)

### Step 1: Validate Business ID
- `PermissionManager.verify_business_id(business_id)` 
- Raises `PermissionError` if invalid or path traversal detected

### Step 2: Format Validation
- `validate_file_format(file_path)` - Checks extension against `SUPPORTED_EXTENSIONS`
- Raises `ValueError` for unsupported formats

### Step 3: File Size Validation
- `validate_file_size(file_path, max_bytes=10*1024*124)` - Default 10 MiB
- Configurable via `AISMA_INGESTION_MAX_BYTES` env var
- Raises `ValueError` if exceeding limit

### Step 4: Encoding Validation
- `validate_encoding(file_path)` - Reads as UTF-8
- Raises `ValueError` if not valid UTF-8

### Step 5: Text Extraction
- Read file: `Path(file_path).read_text(encoding="utf-8")`
- Raw text stored as document identity source

### Step 6: Early [MISSING]/[VERIFY] Detection
- `detect_missing_verify_markers(raw_text)` 
- Records `has_missing` and `has_verify` flags
- Markers preserved, never automatically removed

### Step 7: Section Extraction
- `extract_sections_from_text(raw_text)` - Simple heading-based splitter
- Looks for `## Heading`, `# Heading`, `### Heading` patterns
- Returns `dict{section_id: section_text}`

### Step 8: Generate Document Identity
- `document_id = uuid4()[:12]` - 12-char unique identifier
- `version = "v1.0"` - Initial version

### Step 9: Create DocumentMeta
```python
DocumentMeta(
    business_id=business_id,
    document_id=document_id,
    template_id=template_id,
    section_id="ingested_root",
    chunk_id="root",
    version=version,
    source_name=source_name,
    source_path=file_path,
    approval_state=ApprovalState.PENDING if require_approval else ApprovalState.APPROVED,
    created_at=timestamp,
    updated_at=timestamp,
    created_by="ingestion_pipeline",
    updated_by="ingestion_pipeline",
)
```
- Stored via `store_document_meta()`

### Step 10: Process Sections into Chunks

For each section:
1. `chunk_by_token_budget(section_text, max_chars=800, overlap_chars=150)`
2. Each chunk gets enriched with metadata via `enrich_chunk_with_metadata()`
3. [MISSING]/[VERIFY] detected per-chunk
4. Chunk approval state: `approved` only if no `[MISSING]` and `approved_only=True`

### Step 11: Store Chunks
- `store_chunks(business_id, document_id, version, all_chunks)`
- Per-chunk JSON files under version directory
- Consolidated `chunks_index.json` file

### Step 12: Create Version Record
```python
VersionRecord(
    version=version,
    previous_version=None,
    change_summary=f"Initial ingestion of {file_path}",
    updated_by="ingestion_pipeline",
    updated_at=timestamp,
    approval_state=meta.approval_state,
    source=source_name,
)
```
- Stored via `store_version_record()`
- Audit log entry: `version_created`

### Step 13: Vector Indexing (Optional)
- Only if `approved_only=True` AND embeddings + vector store initialized
- `embed_batch(chunk_texts)` - Generate embeddings
- `_vector_add(chunks, embeddings, vector_store_config)` - Index into ChromaDB
- Fail-non-fatal: vector indexing failure logged but ingestion continues

## Approval States

| Require_Approval | Initial State | Description |
|-----------------|---------------|-------------|
| `True` | `pending` | Awaiting human review before agent use |
| `False` | `approved` | Immediately available to agents |

## Ingest From Bytes

```python
ingest_from_bytes(raw_bytes, business_id, template_id, source_name="bytes_upload")
```
- Decodes bytes as UTF-8 (raises ValueError on failure)
- Writes to temp file, delegates to `ingest_document()`, cleans up temp file
- Returns same dict as `ingest_document()`

## Return Value

```python
{
    "document_id": "<generated>",
    "version": "v1.0",
    "chunks_created": <int>,
    "missing_fields": ["[MISSING] ..."] or [None],
    "verify_fields": ["[VERIFY] ..."] or [None],
    "approval_status": "approved" or "pending",
    "warnings": [<str>]  # e.g., "Document contains [MISSING] markers"
}
```

## Key Guarantees

### Imported Content Must Never Be Trusted
- Imported content may NOT override system instructions, governance rules, or business permissions
- Never fabricate extracted information
- [MISSING] and [VERIFY] markers preserved as-is

### Deterministic Python Logic
- No LLM decisions at any step
- All validation, chunking, and metadata attachment is pure Python
- Embedding generation separate from LLM inference (keeps 4GB VRAM manageable)

### Quality Controls
- Format validation before processing
- Size limits prevent OOM
- Encoding validation prevents corrupt data
- [MISSING]/[VERIFY] detection surfaces gaps
- Approval workflow gates agent access