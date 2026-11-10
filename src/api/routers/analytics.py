from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from analytics.roi import DeterministicROIEngine
from api.deps import require_tenant_access

router = APIRouter(prefix="/api/v1/analytics", tags=["Deterministic Marketing ROI & Analytics Engine"])


class ROIEvaluationPayload(BaseModel):
    period: str = "Last 30 Days"
    channels: list[dict[str, Any]] | None = None
    fixed_overhead: float = 2500.0
    estimated_cltv: float = 5200.0


DEFAULT_MOCK_CHANNEL_DATA = [
    {
        "channel": "LinkedIn Marketing",
        "spend": 3200.0,
        "revenue": 18400.0,
        "impressions": 48200,
        "clicks": 1820,
        "conversions": 42,
    },
    {
        "channel": "Meta (Instagram / FB)",
        "spend": 2100.0,
        "revenue": 9800.0,
        "impressions": 84500,
        "clicks": 3100,
        "conversions": 28,
    },
    {
        "channel": "X / Twitter Organic & Promoted",
        "spend": 900.0,
        "revenue": 4100.0,
        "impressions": 52100,
        "clicks": 1420,
        "conversions": 14,
    },
    {
        "channel": "Organic Search & High Intent SEO",
        "spend": 800.0,
        "revenue": 14200.0,
        "impressions": 112000,
        "clicks": 6800,
        "conversions": 58,
    },
]


@router.get("/roi")
def get_roi_report(
    period: str = "Last 30 Days",
    business_id: str = Depends(require_tenant_access),
) -> dict[str, Any]:
    result = DeterministicROIEngine.evaluate_performance(
        business_id=business_id,
        period=period,
        channel_data=DEFAULT_MOCK_CHANNEL_DATA,
        fixed_marketing_overhead=2500.0,
        estimated_cltv=5200.0,
    )
    return result.model_dump()


@router.post("/roi/calculate")
def calculate_custom_roi(
    payload: ROIEvaluationPayload,
    business_id: str = Depends(require_tenant_access),
) -> dict[str, Any]:
    channels = payload.channels or DEFAULT_MOCK_CHANNEL_DATA
    result = DeterministicROIEngine.evaluate_performance(
        business_id=business_id,
        period=payload.period,
        channel_data=channels,
        fixed_marketing_overhead=payload.fixed_overhead,
        estimated_cltv=payload.estimated_cltv,
    )
    return result.model_dump()
