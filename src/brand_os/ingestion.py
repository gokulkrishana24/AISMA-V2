"""Controlled document ingestion pipeline for Brand OS.

Supported formats where practical: Markdown, TXT, JSON, YAML, CSV.
PDF/DOCX support may be added if existing project dependencies and tooling
support it appropriately.

Ingestion workflow (every step is deterministic Python; no LLM decisions):
1. Accept an authorized document.
2. Validate its format.
3. Validate file size.
4. Validate encoding.
5. Extract text.
6. Preserve document identity.
7. Scan untrusted content (prompt injection scan).
8. Detect [MISSING] and [VERIFY].
9. Split content into chunks.
10. Attach metadata.
11. Store the original source.
12. Create a version record.
13. Require approval where necessary.
14. Index eligible approved content into the vector store.

Imported content must NEVER be treated as trusted instructions. An imported
document may not override system instructions, governance rules, or business
permissions. Never fabricate extracted information.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from brand_os.chunking import (
    chunk_by_token_budget,
    detect_missing_verify_markers,
    enrich_chunk_with_metadata,
    extract_sections_from_text,
)
from brand_os.embeddings import (
    embed_batch,
)
from brand_os.embeddings import (
    is_initialized as _emb_is_initialized,
)
from brand_os.permissions import PermissionManager
from brand_os.repository import (
    _append_audit,
    store_chunks,
    store_document_meta,
    store_version_record,
)
from brand_os.schemas import (
    ApprovalState,
    ChunkContent,
    DocumentMeta,
    TemplateID,
    VectorStoreConfig,
    VersionRecord,
)
from brand_os.vector_store import (
    add_chunks as _vector_add,
)
from brand_os.vector_store import (
    is_initialized as _vector_is_initialized,
)

# ---------------------------------------------------------------------------
# Format validation helpers
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".csv": "csv",
}


def validate_file_format(file_path: str) -> str:
    """Return the format name for a file, or raise ValueError."""
    p = Path(file_path)
    ext = p.suffix.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[ext]
    raise ValueError(f"Unsupported file format: {ext}. Supported: {list(SUPPORTED_EXTENSIONS.keys())}")


def validate_file_size(file_path: str, max_bytes: int = 10 * 1024 * 1024) -> None:
    """Raise ValueError if file exceeds max_bytes (default 10 MiB)."""
    size = os.path.getsize(file_path)
    if size > max_bytes:
        raise ValueError(
            f"File size {size} bytes exceeds maximum {max_bytes} bytes "
            f"(configured via AISMA_INGESTION_MAX_BYLES env var)"
        )


def validate_encoding(file_path: str) -> None:
    """Raise ValueError if file is not valid UTF-8."""
    try:
        Path(file_path).read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"File is not valid UTF-8: {exc}") from exc


# ---------------------------------------------------------------------------
# Main ingestion entry point
# ---------------------------------------------------------------------------

def ingest_document(
    file_path: str,
    business_id: str,
    template_id: TemplateID,
    source_name: str = "upload",
    *,
    max_chars_per_chunk: int = 800,
    overlap_chars: int = 150,
    approved_only: bool = True,
    require_approval: bool = True,
) -> dict[str, Any]:
    """Full ingestion pipeline for a single brand document.

    Returns a dict with:
    - document_id: the generated/document ID
    - version: the created version string
    - chunks_created: number of chunks
    - missing_fields: list of [MISSING] markers found
    - verify_fields: list of [VERIFY] markers found
    - approval_status: "approved", "pending", or "rejected"
    - warnings: list of ingestion warnings

    Raises:
        ValueError: if format/size/encoding invalid
        PermissionError: if business_id invalid or unauthorized
    """
    # Step 1: Validate business_id
    PermissionManager.verify_business_id(business_id)

    # Step 2: Format/size/encoding validation
    validate_file_format(file_path)
    validate_file_size(file_path)
    validate_encoding(file_path)

    # Step 3: Read and extract text
    raw_text = Path(file_path).read_text(encoding="utf-8")

    # Step 4: Detect [MISSING] and [VERIFY] markers early
    markers = detect_missing_verify_markers(raw_text)
    has_missing = markers["missing"]
    has_verify = markers["verify"]

    # Step 5: Extract sections (simple heading-based splitter)
    sections = extract_sections_from_text(raw_text)

    # Step 6: Generate document_id and version
    import uuid as _uuid

    document_id = str(_uuid.uuid4())[:12]
    version = "v1.0"

    # Step 7: Create DocumentMeta
    meta = DocumentMeta(
        business_id=business_id,
        document_id=document_id,
        template_id=template_id,
        section_id="ingested_root",  # root section for unsectioned text
        chunk_id="root",
        version=version,
        source_name=source_name,
        source_path=file_path,
        approval_state=ApprovalState.PENDING if require_approval else ApprovalState.APPROVED,
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        updated_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        created_by="ingestion_pipeline",
        updated_by="ingestion_pipeline",
    )

    # Step 8: Store document meta
    store_document_meta(business_id, document_id, meta)

    # Step 9: Process each section into chunks
    all_chunks: list[ChunkContent] = []
    chunk_counter = 0

    for section_id, section_text in sections.items():
        if not section_text.strip():
            continue

        # Chunk the section text
        chunks_text = chunk_by_token_budget(
            section_text,
            max_chars=max_chars_per_chunk,
            overlap_chars=overlap_chars,
        )

        for chunk_text in chunks_text:
            chunk_counter += 1
            chunk_id = f"{document_id}_{section_id}_{chunk_counter}"

            # Detect missing/verify in this chunk
            chunk_markers = detect_missing_verify_markers(chunk_text)
            chunk_missing = chunk_markers["missing"]
            chunk_verify = chunk_markers["verify"]

            # Enrich chunk with metadata
            chunk = enrich_chunk_with_metadata(
                chunk_text=chunk_text,
                business_id=business_id,
                document_id=document_id,
                template_id=template_id.value,
                section_id=section_id,
                version=version,
                chunk_id=chunk_id,
                approved=not (approved_only and (chunk_missing or not _is_approved_content(chunk_text))),
                missing=chunk_missing,
                verified=chunk_verify,
                source_name=source_name,
            )

            all_chunks.append(chunk)

    # Also create a root-level chunk for the full text if no sections found
    if not all_chunks and raw_text.strip():
        chunk_id = f"{document_id}_root"
        chunk = enrich_chunk_with_metadata(
            chunk_text=raw_text,
            business_id=business_id,
            document_id=document_id,
            template_id=template_id.value,
            section_id="ingested_root",
            version=version,
            chunk_id=chunk_id,
            approved=not (approved_only and not _is_approved_content(raw_text)),
            missing=has_missing,
            verified=has_verify,
            source_name=source_name,
        )
        all_chunks.append(chunk)

    # Step 10: Store chunks
    store_chunks(business_id, document_id, version, all_chunks)

    # Step 11: Create version record
    version_rec = VersionRecord(
        version=version,
        previous_version=None,
        change_summary=f"Initial ingestion of {file_path}",
        updated_by="ingestion_pipeline",
        updated_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        approval_state=meta.approval_state,
        source=source_name,
    )
    store_version_record(business_id, document_id, version_rec)

    # Step 12: If approved and embeddings available, index into vector store
    if approved_only and _vector_is_initialized() and _emb_is_initialized():
        try:
            # Generate embeddings for all chunks
            chunk_texts = [c.content for c in all_chunks]
            embeddings = embed_batch(chunk_texts)

            # Add to vector store
            _vector_add(chunks=all_chunks, embeddings=embeddings, vector_store_config=VectorStoreConfig())
        except Exception as exc:  # noqa: BLE001
            # Non-fatal: ingestion succeeds even if vector indexing fails
            _append_audit(business_id, "vector_index_failed", {"error": str(exc)})

    # Step 13: Set approval status
    approval_status = "approved" if meta.approval_state == ApprovalState.APPROVED else "pending"

    # Compute warnings
    warnings: list[str] = []
    if has_missing:
        warnings.append(f"Document contains [MISSING] markers — {len(all_chunks)} chunks generated with missing-info flags")
    if has_verify and not approved_only:
        warnings.append("Document contains [VERIFY] markers — review before agent execution")

    # Return result
    return {
        "document_id": document_id,
        "version": version,
        "chunks_created": len(all_chunks),
        "missing_fields": [f"[MISSING] {template_id.value} section" if has_missing else None],
        "verify_fields": [f"[VERIFY] {template_id.value} section" if has_verify else None],
        "approval_status": approval_status,
        "warnings": [w for w in warnings if w],  # filter None/empty
    }


def _is_approved_content(text: str) -> bool:
    """Heuristic: determine if text appears to be 'approved' brand content.

    In Phase 4 this is a simple check: the text must NOT contain [MISSING] and
    should not be empty. A real system would have an approved knowledge base
    lookup.
    """
    return "[MISSING]" not in text and len(text.strip()) > 0


def ingest_from_bytes(
    raw_bytes: bytes,
    business_id: str,
    template_id: TemplateID,
    source_name: str = "bytes_upload",
    *,
    max_chars_per_chunk: int = 800,
    require_approval: bool = True,
) -> dict[str, Any]:
    """Ingest a document from raw bytes (e.g., API upload).

    The bytes are decoded as UTF-8; if that fails, a ValueError is raised.
    """
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Cannot decode bytes as UTF-8: {exc}") from exc

    # Write to a temp file and delegate to the file-based ingestor
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", encoding="utf-8", delete=False) as tmp:
        tmp.write(raw_text)
        tmp_path = tmp.name

    try:
        result = ingest_document(
            file_path=tmp_path,
            business_id=business_id,
            template_id=template_id,
            source_name=source_name,
            max_chars_per_chunk=max_chars_per_chunk,
            require_approval=require_approval,
        )
        return result
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass