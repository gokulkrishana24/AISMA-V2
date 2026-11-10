from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.deps import BRAND_OS_STORE, STORE_BUSINESS_ID, get_audit_logger

router = APIRouter(prefix="/api/v1/brand-os", tags=["Brand OS"])


class UpdateBrandOSPayload(BaseModel):
    brand_voice: dict[str, Any] | None = None
    positioning: dict[str, Any] | None = None
    target_audience: dict[str, Any] | None = None
    messaging_bank: dict[str, Any] | None = None
    prohibited_claims: list[str] | None = None
    approved_products_services: list[dict[str, Any]] | None = None
    channel_guidelines: dict[str, Any] | None = None
    content_restrictions: list[str] | None = None


@router.get("")
def get_brand_os() -> dict[str, Any]:
    return BRAND_OS_STORE


@router.put("")
def update_brand_os(payload: UpdateBrandOSPayload) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True)
    for k, v in updates.items():
        if v is not None:
            BRAND_OS_STORE[k] = v

    audit = get_audit_logger()
    audit.log(
        business_id=STORE_BUSINESS_ID,
        actor="human_admin",
        action="brand_os_updated",
        resource="system:brand_os",
        outcome="ok",
        details={"updated_keys": list(updates.keys())},
    )
    return BRAND_OS_STORE

