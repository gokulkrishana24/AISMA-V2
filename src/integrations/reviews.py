from __future__ import annotations

import datetime
from typing import Any

from integrations.base import (
    AdapterHealth,
    AnalyticsMetrics,
    PlatformAdapter,
    PublishPayload,
    PublishResult,
)


class ReviewsAdapter(PlatformAdapter):
    def __init__(self, location_id: str = "locations/124810248", is_sandbox: bool = True) -> None:
        super().__init__("reviews_reputation", is_sandbox=is_sandbox)
        self.location_id = location_id

    def health_check(self) -> AdapterHealth:
        return AdapterHealth(
            platform=self.platform_name,
            connected=True,
            status_code=200,
            message="Google Business & Trustpilot Reviews Monitor connected",
            latency_ms=28.0,
        )

    def publish(self, payload: PublishPayload) -> PublishResult:
        # Publish public reply to a customer review
        return PublishResult(
            success=True,
            platform=self.platform_name,
            post_id=f"reply_{hash(payload.content) % 100000}",
            is_sandbox=self.is_sandbox,
        )

    def fetch_recent_reviews(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "rev_001",
                "author": "Elena Rostova",
                "rating": 5,
                "platform": "Google Business Profile",
                "text": "The local AI privacy architecture completely sold our compliance team. Fast inference and complete control over our brand voice.",
                "created_at": "2026-11-08T14:20:00Z",
                "sentiment": "positive",
                "replied": True,
            },
            {
                "id": "rev_002",
                "author": "Marcus Sterling",
                "rating": 4,
                "platform": "G2 Crowd",
                "text": "Great multi-agent orchestration for enterprise marketing. Would love more automated LinkedIn carousel templates.",
                "created_at": "2026-11-07T09:15:00Z",
                "sentiment": "positive",
                "replied": False,
            },
        ]

    def fetch_analytics(self, days: int = 30) -> AnalyticsMetrics:
        now = datetime.datetime.now(datetime.UTC)
        start = now - datetime.timedelta(days=days)
        return AnalyticsMetrics(
            platform=self.platform_name,
            period_start=start.isoformat(),
            period_end=now.isoformat(),
            impressions=5200,
            reach=4800,
            clicks=310,
            engagements=84,
            engagement_rate=1.61,
            conversions=18,
            spend=0.0,
            extra={
                "average_rating": 4.88,
                "total_reviews": 142,
                "net_promoter_score": 78,
                "sentiment_distribution": {"positive": 91.5, "neutral": 6.3, "negative": 2.2},
            },
        )
