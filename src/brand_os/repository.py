"""Filesystem-backed Brand Knowledge Repository.

Provides business-scoped persistent storage for brand knowledge artifacts.
For Phase 4, JSON files stored under business-specific directories are acceptable.
Design interfaces so Phase 5 can migrate to PostgreSQL without rewriting the Brand OS.

All file operations are restricted to authorized business directories to prevent
path traversal, unauthorized overwrites, and cross-tenant access.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from brand_os.schemas import (
    BrandCompletenessReport,
    ChunkContent,
    DocumentMeta,
    KnowledgeStatus,
    TemplateID,
    VersionRecord,
)

# ---------------------------------------------------------------------------
# Directory layout (Phase 4 filesystem-backed):
# BASE_DIR/state/brand_os/
#   biz_apex_enterprises/
#     documents/
#       <document_id>/
#         meta.json              # DocumentMeta
#         version_1/
#           chunks.json           # list of ChunkContent
#           meta.json             # VersionRecord
#         version_2/...
#     templates/                # optional exported template definitions
#     completeness_report.json
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATE_DIR = BASE_DIR / "state"
BRAND_OS_STATE_DIR = STATE_DIR / "brand_os"


class RepoPermissionError(PermissionError):
    """Raised when repository operation violates tenant boundary or permissions."""

    pass


def _ensure_business_dir(business_id: str) -> Path:
    """Ensure a business-specific directory exists; return its path.

    Raises PermissionError if the business_id contains path traversal attempts.
    """
    # Fail-closed: reject path traversal
    if ".." in business_id or business_id.startswith("/") or business_id.startswith("\\"):
        raise RepoPermissionError(
            f"Business ID '{business_id}' contains invalid characters (path traversal detected)"
        )

    biz_dir = BRAND_OS_STATE_DIR / business_id
    biz_dir.mkdir(parents=True, exist_ok=True)
    (biz_dir / "documents").mkdir(parents=True, exist_ok=True)
    return biz_dir


def _document_dir(business_id: str, document_id: str) -> Path:
    """Return the path for a document's subdirectory."""
    return BRAND_OS_STATE_DIR / business_id / "documents" / document_id


def _version_dir(business_id: str, document_id: str, version: str) -> Path:
    """Return the path for a specific version directory."""
    return _document_dir(business_id, document_id) / f"version_{version}"


def _chunk_file_path(business_id: str, document_id: str, version: str, chunk_id: str) -> Path:
    """Return the path for a single chunk JSON file."""
    return _version_dir(business_id, document_id, version) / f"chunk_{chunk_id}.json"


def _audit_log_path(business_id: str) -> Path:
    """Return the path for the business-level audit log."""
    return BRAND_OS_STATE_DIR / business_id / "audit.jsonl"


def _hash_content(content: str) -> str:
    """Compute a SHA-256 hash of content for change detection."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def store_document_meta(
    business_id: str,
    document_id: str,
    meta: DocumentMeta,
) -> None:
    """Persist DocumentMeta for a document.

    Writes: <base>/state/brand_os/<business_id>/documents/<document_id>/meta.json
    """
    _ensure_business_dir(business_id)
    doc_dir = _document_dir(business_id, document_id)
    doc_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(meta, dict):
        meta = DocumentMeta(**meta)

    meta.path = str(doc_dir)  # convenience for downstream
    (doc_dir / "meta.json").write_text(meta.model_dump_json(indent=2))


def load_document_meta(
    business_id: str,
    document_id: str,
) -> DocumentMeta | None:
    """Load DocumentMeta for a document.

    Returns None if the meta file does not exist (e.g., document not yet indexed).
    """
    doc_dir = _document_dir(business_id, document_id)
    meta_path = doc_dir / "meta.json"
    if not meta_path.exists():
        return None
    try:
        data = json.loads(meta_path.read_text())
        return DocumentMeta(**data)
    except (json.JSONDecodeError, ValueError):
        return None


def store_version_record(
    business_id: str,
    document_id: str,
    version: VersionRecord,
) -> None:
    """Persist a VersionRecord for a document version.

    Writes: <base>/state/brand_os/<business_id>/documents/<document_id>/version_<v>/meta.json
    """
    if isinstance(version, dict):
        version = VersionRecord(**version)
    vz_dir = _version_dir(business_id, document_id, version.version)
    vz_dir.mkdir(parents=True, exist_ok=True)

    # Also update the document's top-level meta with this version
    doc_meta = load_document_meta(business_id, document_id)
    if doc_meta is not None:
        doc_meta.updated_at = version.updated_at
        store_document_meta(business_id, document_id, doc_meta)

    (vz_dir / "meta.json").write_text(version.model_dump_json(indent=2))


def load_version_record(
    business_id: str,
    document_id: str,
    version: str,
) -> VersionRecord | None:
    """Load a VersionRecord for a specific version."""
    vz_path = _version_dir(business_id, document_id, version) / "meta.json"
    if not vz_path.exists():
        return None
    try:
        data = json.loads(vz_path.read_text())
        return VersionRecord(**data)
    except (json.JSONDecodeError, ValueError):
        return None


def load_version_records(
    business_id: str,
    document_id: str,
) -> list[VersionRecord]:
    """Load all VersionRecords for a document."""
    doc_dir = _document_dir(business_id, document_id)
    if not doc_dir.exists():
        return []
    records: list[VersionRecord] = []
    for item in sorted(doc_dir.iterdir()):
        if item.is_dir() and item.name.startswith("v"):
            rec = load_version_record(business_id, document_id, item.name)
            if rec:
                records.append(rec)
    return records


def store_chunks(
    business_id: str,
    document_id: str,
    version: str,
    chunks: list[ChunkContent],
) -> None:
    """Persist a list of ChunkContent for a document version.

    Writes per-chunk JSON files under version directory.
    """
    vz_dir = _version_dir(business_id, document_id, version)
    vz_dir.mkdir(parents=True, exist_ok=True)

    for chunk in chunks:
        c_path = _chunk_file_path(business_id, document_id, version, chunk.chunk_id)
        c_path.write_text(chunk.model_dump_json(indent=2))

    # Also store a consolidated chunks index
    (vz_dir / "chunks_index.json").write_text(
        json.dumps([c.model_dump() for c in chunks], indent=2)
    )


def load_chunks(
    business_id: str,
    document_id: str,
    version: str,
) -> list[ChunkContent] | None:
    """Load all ChunkContent for a document version."""
    vz_dir = _version_dir(business_id, document_id, version)
    index_path = vz_dir / "chunks_index.json"
    if not index_path.exists():
        return None
    try:
        data = json.loads(index_path.read_text())
        return [ChunkContent(**c) for c in data]
    except (json.JSONDecodeError, ValueError):
        return None


def archive_document(
    business_id: str,
    document_id: str,
    reason: str = "manual_archive",
) -> bool:
    """Move a document to an 'archived' state by renaming its directory.

    The directory is renamed to include a timestamp and the reason for archival.
    Returns True on success.
    """
    doc_path = _document_dir(business_id, document_id)
    if not doc_path.exists():
        return False

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    archive_name = f"{document_id}_archived_{timestamp}"
    archive_path = doc_path.parent / archive_name

    # Prevent overwriting existing archived documents
    if archive_path.exists():
        return False

    shutil.move(str(doc_path), str(archive_path))

    # Log the archival
    _append_audit(business_id, "document_archived", {"document_id": document_id, "reason": reason, "at": timestamp})
    return True


def _append_audit(
    business_id: str,
    action: str,
    resource_or_details: Any = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Append an audit entry to the business audit log."""
    audit_path = _audit_log_path(business_id)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    if details is None:
        merged_details = resource_or_details if isinstance(resource_or_details, dict) else {"target": str(resource_or_details)}
    else:
        merged_details = {"target": str(resource_or_details), **details}

    entry = {
        "business_id": business_id,
        "action": action,
        "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "details": merged_details,
    }
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_audit_log(business_id: str) -> list[dict[str, Any]]:
    """Read the full audit log for a business."""
    audit_path = _audit_log_path(business_id)
    if not audit_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    try:
        with audit_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return entries


def compute_completeness_report(
    business_id: str,
) -> BrandCompletenessReport:
    """Compute a BrandCompletenessReport for a business by inspecting stored data.

    Scans all documents/versions/chunks for the business and determines which
    templates are completed, which have missing fields, etc.
    """
    populated: dict[TemplateID, dict[str, Any]] = {}

    # Collect all document metadata and chunk data
    get_audit_log(business_id)

    # List all document directories
    documents_dir = BRAND_OS_STATE_DIR / business_id / "documents"
    if not documents_dir.exists():
        return BrandCompletenessReport(
            business_id=business_id,
            total_templates=len(list(TemplateID)),
            completed_templates=0,
            incomplete_templates=len(list(TemplateID)),
            missing_fields=[],
            verification_required=[],
            pending_approvals=0,
            archived_records=0,
            last_updated=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            template_status={},
        )

    doc_entries = [d for d in documents_dir.iterdir() if d.is_dir() and d.name != "archived*"]

    for doc_dir in doc_entries:
        document_id = doc_dir.name
        doc_meta = load_document_meta(business_id, document_id)
        if doc_meta is None:
            continue

        # For each version of this document
        version_dirs = [d for d in doc_dir.iterdir() if d.is_dir() and d.name.startswith("version_")]
        for ver_dir in version_dirs:
            version = ver_dir.name.replace("version_", "")
            chunks = load_chunks(business_id, document_id, version)
            if chunks is None:
                continue

            # Read version record
            version_rec = load_version_record(business_id, document_id, version)
            if version_rec is None:
                continue

            # Determine which template this chunk belongs to
            for chunk in chunks:
                tid_str = chunk.template_id
                try:
                    tid = TemplateID(tid_str)
                except ValueError:
                    continue

                # Initialize template entry if not yet populated
                if tid not in populated:
                    populated[tid] = {
                        "business_id": business_id,
                        "document_id": document_id,
                        "version": version,
                        "chunks": [],
                    }

                populated[tid]["chunks"].append(
                    {
                        "content": chunk.content,
                        "approved": chunk.approved,
                        "missing": chunk.missing,
                        "verified": chunk.verified,
                        "version": version,
                    }
                )

    # Now compute completeness using the helper from templates.py
    from brand_os.templates import TEMPLATE_REGISTRY, get_template_completeness
    report = get_template_completeness(business_id, {tid: {"documents": docs} for tid, docs in populated.items()})

    # Post-process: ensure all template IDs are present even if no data
    for tid in TemplateID:
        if tid not in {TemplateID(k): k for k in report.template_status.keys()}:
            report.template_status[tid.value] = {
                "completed": False,
                "hasContent": False,
                "approvalState": KnowledgeStatus.DRAFT.value,
                "missingIndicators": TEMPLATE_REGISTRY.get(tid, {}).get("missing", []),
                "verificationIndicators": TEMPLATE_REGISTRY.get(tid, {}).get("verify", []),
            }

    return report