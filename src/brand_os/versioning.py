"""Knowledge versioning and audit history for Brand OS.

Supports:
- Drafts, pending approvals, approved, rejected, and archived states.
- Version history tracking with previous version links.
- Version diffing and comparison.
- Controlled restoration with audit logs.
"""

from __future__ import annotations

import difflib
from datetime import UTC, datetime
from typing import Any

from brand_os.permissions import PermissionManager
from brand_os.repository import (
    _append_audit,
    load_chunks,
    load_document_meta,
    load_version_records,
    store_chunks,
    store_document_meta,
    store_version_record,
)
from brand_os.schemas import ApprovalState, DocumentMeta, VersionRecord


def create_version(
    business_id: str,
    document_id: str,
    change_summary: str = "Update",
    updated_by: str = "system",
    source: str = "manual",
    approval_state: ApprovalState = ApprovalState.PENDING,
) -> VersionRecord:
    """Create a new version record for an existing document."""
    PermissionManager.verify_business_id(business_id)
    records = load_version_records(business_id, document_id)
    prev_version = records[-1].version if records else None

    # Deterministic increment (v1, v2, v3, etc.)
    if prev_version and prev_version.startswith("v") and prev_version[1:].isdigit():
        new_v = f"v{int(prev_version[1:]) + 1}"
    else:
        new_v = f"v{len(records) + 1}"

    now_iso = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    rec = VersionRecord(
        version=new_v,
        previous_version=prev_version,
        change_summary=change_summary,
        updated_by=updated_by,
        updated_at=now_iso,
        approval_state=approval_state,
        source=source,
    )
    store_version_record(business_id, document_id, rec)
    _append_audit(
        business_id,
        "version_created",
        f"{document_id}@{new_v}",
        {"updated_by": updated_by, "summary": change_summary},
    )
    return rec


def list_versions(business_id: str, document_id: str) -> list[VersionRecord]:
    """Retrieve all historical version records for a document."""
    PermissionManager.verify_business_id(business_id)
    return load_version_records(business_id, document_id)


def compare_versions(
    business_id: str, document_id: str, v1: str, v2: str
) -> dict[str, Any]:
    """Generate a unified diff between two historical document versions."""
    PermissionManager.verify_business_id(business_id)
    chunks_v1 = load_chunks(business_id, document_id, version=v1) or []
    chunks_v2 = load_chunks(business_id, document_id, version=v2) or []

    text_v1 = "\n\n".join(c.content for c in chunks_v1).splitlines()
    text_v2 = "\n\n".join(c.content for c in chunks_v2).splitlines()

    diff = list(
        difflib.unified_diff(
            text_v1,
            text_v2,
            fromfile=f"{document_id}@{v1}",
            tofile=f"{document_id}@{v2}",
            lineterm="",
        )
    )

    return {
        "document_id": document_id,
        "from_version": v1,
        "to_version": v2,
        "diff_lines": diff,
        "added_lines": sum(1 for line in diff if line.startswith("+") and not line.startswith("+++")),
        "removed_lines": sum(1 for line in diff if line.startswith("-") and not line.startswith("---")),
    }


def load_version_record(business_id: str, document_id: str, version: str) -> VersionRecord:
    """Load a specific version record by version tag."""
    PermissionManager.verify_business_id(business_id)
    records = load_version_records(business_id, document_id)
    for r in records:
        if r.version == version:
            return r
    now_iso = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return VersionRecord(
        version=version,
        change_summary="Recorded version",
        updated_by="system",
        updated_at=now_iso,
        approval_state=ApprovalState.PENDING,
        source="system",
    )


def restore_version(
    business_id: str,
    document_id: str,
    target_version: str,
    updated_by: str = "system",
) -> DocumentMeta:
    """Restore a previous version by creating a new version pointing back to historical chunks."""
    PermissionManager.verify_business_id(business_id)
    meta = load_document_meta(business_id, document_id)
    target_chunks = load_chunks(business_id, document_id, version=target_version)

    # Create new increment version record representing the restoration
    new_rec = create_version(
        business_id,
        document_id,
        change_summary=f"Restored from {target_version}",
        updated_by=updated_by,
        source=f"restoration_of_{target_version}",
        approval_state=ApprovalState.PENDING,
    )

    if target_chunks:
        restored_chunks = []
        for c in target_chunks:
            restored_chunks.append(
                c.model_copy(update={"version": new_rec.version, "chunk_id": f"{c.section_id}_{new_rec.version}"})
            )
        store_chunks(business_id, document_id, new_rec.version, restored_chunks)

    # Update document metadata
    now_iso = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if meta is not None:
        updated_meta = meta.model_copy(
            update={
                "version": new_rec.version,
                "updated_at": now_iso,
                "updated_by": updated_by,
                "approval_state": ApprovalState.PENDING,
            }
        )
    else:
        updated_meta = DocumentMeta(
            business_id=business_id,
            document_id=document_id,
            template_id="brand_identity",
            section_id="root",
            chunk_id="root",
            version=new_rec.version,
            source_name=f"restored_{target_version}",
            approval_state=ApprovalState.PENDING,
            created_at=now_iso,
            updated_at=now_iso,
            created_by=updated_by,
            updated_by=updated_by,
        )

    store_document_meta(business_id, document_id, updated_meta)
    _append_audit(
        business_id,
        "version_restored",
        f"{document_id}@{new_rec.version}",
        {"restored_from": target_version, "updated_by": updated_by},
    )
    object.__setattr__(updated_meta, "change_summary", f"Restored from {target_version}")
    return updated_meta
