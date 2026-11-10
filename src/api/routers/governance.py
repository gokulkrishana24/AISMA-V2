from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.deps import (
    get_audit_logger,
    get_kill_switch,
    require_tenant_access,
)
from governance.audit import verify_audit_chain

router = APIRouter(prefix="/api/v1/governance", tags=["Governance Sentinel"])


class KillSwitchTogglePayload(BaseModel):
    engaged: bool
    reason: str
    actor: str = "human_admin"


@router.get("/killswitch")
def get_killswitch_status(business_id: str = Depends(require_tenant_access)) -> dict[str, Any]:
    ks = get_kill_switch()
    engaged = ks.is_engaged(business_id)
    state = ks.get_business_state(business_id)
    return {
        "engaged": engaged,
        "scope": state.scope,
        "reason": state.reason or ("Emergency kill switch engaged." if engaged else "System running normally. No active halt triggers."),
        "updated_at": state.updated_at,
        "updated_by": state.updated_by,
        "active_halt_triggers": ["manual_admin_halt"] if engaged else [],
    }


@router.post("/killswitch")
def toggle_killswitch(
    payload: KillSwitchTogglePayload,
    business_id: str = Depends(require_tenant_access),
) -> dict[str, Any]:
    ks = get_kill_switch()
    audit = get_audit_logger()

    if payload.engaged:
        state = ks.engage_business(
            business_id=business_id,
            reason=payload.reason,
            updated_by=payload.actor,
        )
        action_name = "killswitch_engaged"
    else:
        state = ks.disengage_business(
            business_id=business_id,
            reason=payload.reason or "manual_admin_disengage",
            updated_by=payload.actor,
        )
        action_name = "killswitch_disengaged"

    # Cryptographic SHA-256 Audit Log Entry
    audit.log(
        business_id=business_id,
        actor=payload.actor,
        action=action_name,
        resource="system:killswitch",
        outcome="ok",
        details={"engaged": payload.engaged, "reason": payload.reason},
    )

    return {
        "engaged": state.engaged,
        "scope": state.scope,
        "reason": state.reason,
        "updated_at": state.updated_at,
        "updated_by": state.updated_by,
        "active_halt_triggers": ["manual_admin_halt"] if state.engaged else [],
    }


@router.get("/audit")
def get_audit_logs(business_id: str = Depends(require_tenant_access)) -> dict[str, Any]:
    audit = get_audit_logger()
    entries = audit.read_entries(business_id)
    chain_valid, _ = verify_audit_chain(entries)

    return {
        "entries": entries,
        "chainValid": chain_valid,
        "total": len(entries),
    }


@router.post("/audit/verify")
def verify_cryptographic_audit_chain(business_id: str = Depends(require_tenant_access)) -> dict[str, Any]:
    audit = get_audit_logger()
    entries = audit.read_entries(business_id)
    if not entries:
        return {
            "valid": True,
            "verifiedCount": 0,
            "message": "Genesis state: No audit log entries exist yet. Hash chain is clean.",
        }

    is_valid, msg = verify_audit_chain(entries)
    first_hash = entries[0].get("entry_hash", "") if entries else None
    last_hash = entries[-1].get("entry_hash", "") if entries else None
    return {
        "valid": is_valid,
        "verifiedCount": len(entries),
        "message": f"Cryptographic SHA-256 audit chain verified ({len(entries)} records): {msg}",
        "first_hash": first_hash,
        "last_hash": last_hash,
    }

