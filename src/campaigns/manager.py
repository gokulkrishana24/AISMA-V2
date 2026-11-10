from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    name: str
    objective: str  # e.g. "brand_awareness", "lead_generation", "product_launch"
    budget_allocated: float = 0.0
    channels: list[str] = Field(default_factory=list)
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None


class CampaignRecord(BaseModel):
    id: str
    business_id: str
    name: str
    objective: str
    status: str  # "draft", "active", "paused", "completed"
    budget_allocated: float
    budget_spent: float = 0.0
    channels: list[str]
    start_date: str | None = None
    end_date: str | None = None
    created_at: str


class CampaignManager:
    def __init__(self) -> None:
        self._campaigns: dict[str, list[CampaignRecord]] = {}

    def create_campaign(self, business_id: str, payload: CampaignCreate) -> CampaignRecord:
        now = datetime.datetime.now(datetime.UTC).isoformat()
        campaign_id = f"cmp_{uuid.uuid4().hex[:12]}"
        record = CampaignRecord(
            id=campaign_id,
            business_id=business_id,
            name=payload.name,
            objective=payload.objective,
            status="draft",
            budget_allocated=payload.budget_allocated,
            budget_spent=0.0,
            channels=payload.channels or ["linkedin", "twitter"],
            start_date=payload.start_date.isoformat() if payload.start_date else None,
            end_date=payload.end_date.isoformat() if payload.end_date else None,
            created_at=now,
        )
        if business_id not in self._campaigns:
            self._campaigns[business_id] = []
        self._campaigns[business_id].append(record)
        return record

    def list_campaigns(self, business_id: str) -> list[CampaignRecord]:
        return self._campaigns.get(business_id, [])

    def get_campaign(self, business_id: str, campaign_id: str) -> CampaignRecord | None:
        for c in self._campaigns.get(business_id, []):
            if c.id == campaign_id:
                return c
        return None

    def update_status(self, business_id: str, campaign_id: str, new_status: str) -> CampaignRecord | None:
        valid_statuses = {"draft", "active", "paused", "completed"}
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: {valid_statuses}")
        camp = self.get_campaign(business_id, campaign_id)
        if camp:
            camp.status = new_status
        return camp

    def record_spend(self, business_id: str, campaign_id: str, amount: float) -> CampaignRecord | None:
        camp = self.get_campaign(business_id, campaign_id)
        if camp:
            camp.budget_spent = round(camp.budget_spent + amount, 2)
        return camp
