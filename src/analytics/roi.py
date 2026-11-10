from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChannelPerformance(BaseModel):
    channel: str
    spend: float
    attributed_revenue: float
    impressions: int
    clicks: int
    conversions: int
    roas: float
    cpa: float  # Cost per acquisition


class ROAMetricsResult(BaseModel):
    business_id: str
    period: str
    total_spend: float
    total_attributed_revenue: float
    blended_roas: float
    net_marketing_profit: float
    marketing_roi_percentage: float
    customer_acquisition_cost: float
    customer_lifetime_value: float
    ltv_to_cac_ratio: float
    channels: list[ChannelPerformance]
    deterministic_audit_hash: str = ""
    computed_at: str = Field(default_factory=lambda: "")


class DeterministicROIEngine:
    """Pure, deterministic Python ROI and ROAS engine.

    Guarantees mathematically exact marketing calculations without AI hallucinations.
    """

    @staticmethod
    def calculate_roas(revenue: float, ad_spend: float) -> float:
        if ad_spend <= 0:
            return 0.0 if revenue <= 0 else 999.99
        return round(revenue / ad_spend, 2)

    @staticmethod
    def calculate_roi(revenue: float, total_costs: float) -> float:
        if total_costs <= 0:
            return 0.0
        return round(((revenue - total_costs) / total_costs) * 100, 2)

    @staticmethod
    def calculate_cac(acquisition_costs: float, new_customers: int) -> float:
        if new_customers <= 0:
            return 0.0
        return round(acquisition_costs / new_customers, 2)

    @staticmethod
    def calculate_ltv_to_cac(ltv: float, cac: float) -> float:
        if cac <= 0:
            return 0.0
        return round(ltv / cac, 2)

    @classmethod
    def evaluate_performance(
        cls,
        business_id: str,
        period: str,
        channel_data: list[dict[str, Any]],
        fixed_marketing_overhead: float = 0.0,
        estimated_cltv: float = 4500.0,
    ) -> ROAMetricsResult:
        import datetime
        import hashlib
        import json

        total_spend = fixed_marketing_overhead
        total_revenue = 0.0
        total_conversions = 0
        computed_channels: list[ChannelPerformance] = []

        for ch in channel_data:
            name = ch.get("channel", "unknown")
            spend = float(ch.get("spend", 0.0))
            rev = float(ch.get("revenue", 0.0))
            imp = int(ch.get("impressions", 0))
            clicks = int(ch.get("clicks", 0))
            conv = int(ch.get("conversions", 0))

            roas = cls.calculate_roas(rev, spend)
            cpa = round(spend / conv, 2) if conv > 0 else 0.0

            total_spend += spend
            total_revenue += rev
            total_conversions += conv

            computed_channels.append(
                ChannelPerformance(
                    channel=name,
                    spend=spend,
                    attributed_revenue=rev,
                    impressions=imp,
                    clicks=clicks,
                    conversions=conv,
                    roas=roas,
                    cpa=cpa,
                )
            )

        ad_spend_only = sum(c.spend for c in computed_channels)
        blended_roas = cls.calculate_roas(total_revenue, ad_spend_only)
        net_profit = round(total_revenue - total_spend, 2)
        roi_pct = cls.calculate_roi(total_revenue, total_spend)
        cac = cls.calculate_cac(total_spend, total_conversions)
        ltv_cac = cls.calculate_ltv_to_cac(estimated_cltv, cac)

        now_str = datetime.datetime.now(datetime.UTC).isoformat()
        audit_payload = {
            "business_id": business_id,
            "period": period,
            "total_spend": total_spend,
            "total_revenue": total_revenue,
            "blended_roas": blended_roas,
            "roi_pct": roi_pct,
            "cac": cac,
            "timestamp": now_str,
        }
        audit_hash = hashlib.sha256(json.dumps(audit_payload, sort_keys=True).encode("utf-8")).hexdigest()

        return ROAMetricsResult(
            business_id=business_id,
            period=period,
            total_spend=round(total_spend, 2),
            total_attributed_revenue=round(total_revenue, 2),
            blended_roas=blended_roas,
            net_marketing_profit=net_profit,
            marketing_roi_percentage=roi_pct,
            customer_acquisition_cost=cac,
            customer_lifetime_value=estimated_cltv,
            ltv_to_cac_ratio=ltv_cac,
            channels=computed_channels,
            deterministic_audit_hash=audit_hash,
            computed_at=now_str,
        )
