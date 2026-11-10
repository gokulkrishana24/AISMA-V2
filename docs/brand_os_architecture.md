# Brand OS + RAG Architecture Report

## Overview
The Brand Operating System (Brand OS) + RAG engine for AISMA v2 provides a local, open-source knowledge repository with tenant isolation, document ingestion, vector storage, and Retrieval-Augmented Generation capabilities. All operations are deterministic Python logic with no paid AI API dependencies.

## Architecture Components

### 1. Python Backend (`src/brand_os/`)
Package implementing all Brand OS + RAG features:

- **`__init__.py`** - Package init, exports all submodules
- **`schemas.py`** - Pydantic v2 models for all data types (TemplateID enum with 27 templates, DocumentMeta, ChunkContent, VersionRecord, RetrievalResult, QueryContext, BrandCompletenessReport, EmbeddingConfig, VectorStoreConfig, ApprovalState, KnowledgeStatus, MissingIndicator)
- **`templates.py`** - 27-template registry with exact names from spec; `get_template()`, `list_templates()`, `validate_template_field()`, `get_template_completeness()`
- **`repository.py`** - Filesystem persistence: store/load document meta, version records, chunks; `archive_document()`; audit log (JSONL); `compute_completeness_report()`; path traversal prevention
- **`chunking.py`** - Section extraction, token-budget chunking (~800 chars/chunk), metadata enrichment, [MISSING]/[VERIFY] detection
- **`embeddings.py`** - Lazy singleton SentenceTransformer (`all-MiniLM-L6-v2`, 384 dims); `initialize()`, `is_initialized()`, `embed_query()`, `embed_batch()`, `reset()`
- **`vector_store.py`** - ChromaDB adapter: `initialize_chroma()`, `add_chunks()`, `query_chunks()` (with mandatory business_id filtering), `delete_chunks()`, `clear_collection()`; mandatory metadata enforcement
- **`rag.py`** - Full retrieval pipeline: embed query → vector query → approved-only filter → version filter → top-k → missing/verify detection → source attribution → compact context dict
- **`ingestion.py`** - Full ingestion pipeline: format/size/encoding validation → text extraction → [MISSING]/[VERIFY] detection → section splitting → token-budget chunking → metadata enrichment → DocumentMeta/VersionRecord/ChunkContent storage → optional vector indexing → approval status
- **`permissions.py`** - Business-scoped PermissionManager: `verify_business_id()`, `check_can_read/write/retrieve()`; `RepoPermissionError` for isolation violations
- **`attribution.py`** - Source reference extraction (document_id, template_id, section_id, version, source_reference); `validate_source_support()`, `attach_attribution_to_output()`
- **`versioning.py`** - Version record creation, listing, comparison, and restoration with audit logging
- **`validation.py`** - Template field validation, [MISSING]/[VERIFY] marker detection, comprehensive validation logic

### 2. Brand Context Integration (`src/services/brand_context.py`)
- Extended `BrandContext` with RAG mode; `build()` supports `rag_query` parameter
- Two modes: RAG retrieval + `compact_prompt()` integrates RAG context, or Phase 3 in-memory fallback
- `get_completeness_report()` delegates to repository

### 3. Agent Integration (`src/agents/base.py`)
- `_build_system_prompt()` enhanced to pass RAG context through `compact_prompt`
- Governance reminders appended deterministically

### 4. Frontend (`frontend/src/app/brand-os/page.tsx`)
- Existing Next.js 14.2 App Router route `/brand-os`
- 5-tab interface: Identity & Positioning, Brand Voice & Guidelines, Messaging Bank, Approved Proof Points, Target Personas
- Preserves dark navy enterprise design system
- Uses TanStack Query `useQuery` for `apiClient.getBrandOS()`
- Development fixtures when backend unavailable

### 5. API Client (`frontend/src/lib/api-client.ts`)
- `getBrandOS()` → `GET /api/v1/brand-os` → `MOCK_BRAND_OS` fixture fallback
- `updateBrandOS()` → `PUT /api/v1/brand-os` → typed fixture merge

## Data Flow

```
Document Ingestion → Text Extraction → Section Splitting → Chunking → [MISSING]/[VERIFY] Detection
       ↓                                       ↓                              ↓
  Format Validation                     Metadata Enrichment         ChunkContent Storage
       ↓                                       ↓                              ↓
   Vector Indexing                      Approval Status Tracking    Version Record Creation

Query → business_id Validation → Kill Switch → Embedding → Vector Query → business_id Isolation
      ↓                      ↓              ↓                ↓              ↓                ↓
  Approved-only Filter         Version Filter   Top-k Limit  Context Size  Missing/Verify Detection → Source Attribution → Compact Context
```

## Key Design Decisions

### Tenant Isolation
- Every record must contain `business_id`
- All repository operations restricted to authorized business directories
- Vector store queries enforce `business_id` at the storage boundary (not just frontend filtering)
- Cross-tenant access explicitly blocked

### Graceful Degradation
- RAG features fall back to in-memory mode when services unavailable
- Mocked embeddings and vector storage for normal tests
- Optional real-RAG smoke tests: `AISMA_RUN_REAL_RAG_TESTS=1`

### Deterministic Logic
- No LLM decisions for governance, approval, or validation
- All state transitions validated through deterministic Python logic
- [MISSING] and [VERIFY] markers preserved, never automatically removed

### Phase 5 Migration Path
- Repository interfaces designed for PostgreSQL + pgvector migration
- Vector store signatures (add, update, delete, query, get, metadata filtering) abstracted for backend swap
- All schemas use `strict=True` (Pydantic v2) to prevent invalid data entry
- Clean separation between Brand OS logic and infrastructure concerns

## Constraints & Limitations

### Hardware
- Target: NVIDIA RTX 3050 GPU (4GB VRAM) + 16GB RAM Windows 11 Python 3.12
- Embedding model: `all-MiniLM-L6-v2` (384 dimensions, CPU-friendly)
- Batch sizes limited to respect memory constraints
- Retrieval top_k limited to 5-20 to control context size

### Dependencies
- Free, open-source stack only: Ollama, sentence-transformers, chromadb, FastAPI, Next.js, Tailwind CSS
- No paid AI APIs (OpenAI, Anthropic, Claude, Gemini)
- No cloud-dependent AI processing

### Known Limitations
- PDF/DOCX support not included (no relevant dependencies)
- Real inference not validated for full 8-agent workflow
- ChromaDB persistence suitable for development/local use; Phase 5 will PostgreSQL + pgvector
- Frontend fixtures used when backend unavailable (clearly labelled as development mode)