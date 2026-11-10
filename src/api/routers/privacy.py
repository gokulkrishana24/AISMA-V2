from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import (
    get_audit_logger,
    get_brand_service,
    get_current_user,
    get_db,
    require_tenant_access,
)
from db.models import ApprovalItem, ContentDraft, User

router = APIRouter(prefix="/api/v1/privacy", tags=["Data Privacy, GDPR/CCPA & Account Retention"])


@router.get("/export")
def export_tenant_data(
    business_id: str = Depends(require_tenant_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """GDPR / CCPA Tenant Data Portability Export."""
    # 1. User profile data
    user_info = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat(),
    }

    # 2. Approvals data
    approvals = db.query(ApprovalItem).filter(ApprovalItem.business_id == business_id).all()
    approvals_data = [
        {
            "id": a.id,
            "title": a.title,
            "status": a.status,
            "channel": a.channel,
            "submitted_at": a.submitted_at.isoformat(),
        }
        for a in approvals
    ]

    # 3. Content drafts
    drafts = db.query(ContentDraft).filter(ContentDraft.business_id == business_id).all()
    drafts_data = [
        {
            "id": d.id,
            "title": d.title,
            "channel": d.channel,
            "status": d.status,
        }
        for d in drafts
    ]

    # 4. Brand OS Context
    brand_svc = get_brand_service()
    brand_ctx = brand_svc.build(business_id=business_id)
    brand_data = brand_ctx.to_dict()

    # 5. Audit Log Records
    audit = get_audit_logger()
    audit_entries = audit.read_entries(business_id)

    return {
        "export_metadata": {
            "business_id": business_id,
            "requested_by": current_user.email,
            "exported_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "format": "JSON",
            "compliance": "GDPR Article 20 / CCPA Data Portability",
        },
        "user_profile": user_info,
        "approvals": approvals_data,
        "content_drafts": drafts_data,
        "brand_os": brand_data,
        "audit_logs": audit_entries,
    }


@router.delete("/account")
def request_account_deletion(
    business_id: str = Depends(require_tenant_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """GDPR Article 17 Right to Erasure / Account Deletion Request."""
    current_user.is_active = False
    db.commit()

    # Audit log the erasure request
    audit = get_audit_logger()
    entry = audit.log(
        business_id=business_id,
        actor=current_user.id,
        action="account_deletion_scheduled",
        resource=f"user:{current_user.id}",
        outcome="ok",
        details={"email": current_user.email, "retention_grace_period_days": 30},
    )

    return {
        "success": True,
        "status": "deactivated_pending_erasure",
        "message": f"Account '{current_user.email}' has been deactivated. Data scheduled for purge following 30-day statutory retention window.",
        "audit_entry_hash": entry.entry_hash,
    }

