from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import require_tenant_access
from campaigns.manager import CampaignCreate, CampaignManager

router = APIRouter(prefix="/api/v1/campaigns", tags=["Campaigns & Marketing Calendar"])

_campaign_manager = CampaignManager()


def get_campaign_manager() -> CampaignManager:
    return _campaign_manager


class StatusUpdatePayload(BaseModel):
    status: str


class RecordSpendPayload(BaseModel):
    amount: float


@router.get("")
def list_campaigns(
    business_id: str = Depends(require_tenant_access),
    mgr: CampaignManager = Depends(get_campaign_manager),
) -> list[dict[str, Any]]:
    campaigns = mgr.list_campaigns(business_id)
    return [c.model_dump() for c in campaigns]


@router.post("")
def create_campaign(
    payload: CampaignCreate,
    business_id: str = Depends(require_tenant_access),
    mgr: CampaignManager = Depends(get_campaign_manager),
) -> dict[str, Any]:
    created = mgr.create_campaign(business_id, payload)
    return created.model_dump()


@router.get("/{campaign_id}")
def get_campaign(
    campaign_id: str,
    business_id: str = Depends(require_tenant_access),
    mgr: CampaignManager = Depends(get_campaign_manager),
) -> dict[str, Any]:
    camp = mgr.get_campaign(business_id, campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return camp.model_dump()


@router.patch("/{campaign_id}/status")
def update_campaign_status(
    campaign_id: str,
    payload: StatusUpdatePayload,
    business_id: str = Depends(require_tenant_access),
    mgr: CampaignManager = Depends(get_campaign_manager),
) -> dict[str, Any]:
    try:
        updated = mgr.update_status(business_id, campaign_id, payload.status)
        if not updated:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return updated.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{campaign_id}/spend")
def record_campaign_spend(
    campaign_id: str,
    payload: RecordSpendPayload,
    business_id: str = Depends(require_tenant_access),
    mgr: CampaignManager = Depends(get_campaign_manager),
) -> dict[str, Any]:
    updated = mgr.record_spend(business_id, campaign_id, payload.amount)
    if not updated:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated.model_dump()
