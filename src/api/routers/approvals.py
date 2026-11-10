from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import (
    APPROVALS_STORE,
    DRAFTS_STORE,
    STORE_BUSINESS_ID,
    get_audit_logger,
    get_kill_switch,
    get_permission_manager,
    get_policy_engine,
    require_tenant_access,
)
from governance.permissions import Action, PermissionContext, PermissionDeniedError

router = APIRouter(prefix="/api/v1/approvals", tags=["Human Approval Center"])


class ApprovalDecisionPayload(BaseModel):
    action: str  # "approve" | "reject"
    note: str | None = None
    actor: str = "human_admin"


@router.get("")
def list_approvals(business_id: str = Depends(require_tenant_access)) -> list[dict[str, Any]]:
    return [app for app in APPROVALS_STORE if app.get("business_id", STORE_BUSINESS_ID) == business_id]


@router.post("/{approval_id}/decision")
def submit_approval_decision(
    approval_id: str,
    payload: ApprovalDecisionPayload,
    business_id: str = Depends(require_tenant_access),
) -> dict[str, Any]:
    # 1. Verify kill switch
    ks = get_kill_switch()
    if ks.is_engaged(business_id):
        raise HTTPException(
            status_code=403,
            detail=f"Kill switch is engaged for {business_id}. Approvals are blocked.",
        )

    # 2. Verify human admin permissions (fail-closed)
    perms = get_permission_manager()
    perm_ctx = PermissionContext(
        business_id=business_id,
        actor=payload.actor,
        actor_business_id=business_id,
    )
    try:
        perms.require(
            perm_ctx,
            Action.PUBLISH if payload.action == "approve" else Action.REQUEST_APPROVAL,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=403,
            detail=f"Actor '{payload.actor}' lacks permission: {exc}",
        ) from exc

    # 3. Locate approval
    found = None
    for app in APPROVALS_STORE:
        if app["id"] == approval_id:
            found = app
            break

    if not found:
        # Create a stub record so decision can proceed safely if requested
        found = {
            "id": approval_id,
            "business_id": business_id,
            "title": f"External Approval Request ({approval_id})",
            "type": "content_publish",
            "agentId": "content_engine",
            "urgency": "medium",
            "contentPreview": f"External approval item {approval_id}",
            "submittedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "policyViolations": [],
            "budgetWarnings": [],
            "riskScore": 10,
            "metadata": {},
            "status": "pending",
        }
        APPROVALS_STORE.append(found)

    # 4. Evaluate Policy
    policy = get_policy_engine()
    action_to_eval = "publish" if payload.action == "approve" else "queue_for_approval"
    decision = policy.evaluate(
        action=action_to_eval,
        actor=payload.actor,
        business_id=business_id,
        resource={"approval_id": approval_id, "status": "approved" if payload.action == "approve" else "pending_approval"},
        has_human_approval=True,
    )
    if not decision.allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Governance policy denied approval decision: {decision.reason}",
        )

    # 5. Apply decision
    new_status = "approved" if payload.action == "approve" else "rejected"
    found["status"] = new_status
    found["decidedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    found["decidedBy"] = payload.actor
    found["decisionNote"] = payload.note or ""

    # Synchronize corresponding draft status if present
    task_id = found.get("taskId")
    for draft in DRAFTS_STORE:
        if draft.get("id") == approval_id or draft.get("taskId") == task_id:
            draft["status"] = new_status

    # 6. Cryptographic SHA-256 Audit Log Entry
    audit = get_audit_logger()
    entry = audit.log(
        business_id=business_id,
        actor=payload.actor,
        action=f"approval_{new_status}",
        resource=f"approval:{approval_id}",
        outcome="ok",
        details={
            "approval_id": approval_id,
            "action": payload.action,
            "status": new_status,
            "note": payload.note or "",
            "item_title": found.get("title", ""),
        },
    )

    return {
        "id": approval_id,
        "status": new_status,
        "audited": True,
        "entry_hash": entry.entry_hash,
        "prev_hash": entry.prev_hash,
        "message": f"Approval decision '{payload.action}' successfully recorded in SHA-256 audit ledger.",
    }

