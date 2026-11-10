from __future__ import annotations

import datetime

from integrations.base import (
    AdapterHealth,
    AnalyticsMetrics,
    PlatformAdapter,
    PublishPayload,
    PublishResult,
)


class GA4Adapter(PlatformAdapter):
    def __init__(self, property_id: str = "properties/398124912", is_sandbox: bool = True) -> None:
        super().__init__("google_analytics_4", is_sandbox=is_sandbox)
        self.property_id = property_id

    def health_check(self) -> AdapterHealth:
        return AdapterHealth(
            platform=self.platform_name,
            connected=True,
            status_code=200,
            message="Google Analytics 4 Data API stream operational",
            latency_ms=19.5,
        )

    def publish(self, payload: PublishPayload) -> PublishResult:
        # Analytics is telemetry reporting
        return PublishResult(
            success=True,
            platform=self.platform_name,
            post_id="ga4_event_dispatch",
            is_sandbox=self.is_sandbox,
        )

    def fetch_analytics(self, days: int = 30) -> AnalyticsMetrics:
        now = datetime.datetime.now(datetime.UTC)
        start = now - datetime.timedelta(days=days)
        return AnalyticsMetrics(
            platform=self.platform_name,
            period_start=start.isoformat(),
            period_end=now.isoformat(),
            impressions=124000,
            reach=96000,
            clicks=18400,
            engagements=8900,
            engagement_rate=48.3,
            conversions=640,
            spend=0.0,
            extra={
                "sessions": 22100,
                "engaged_sessions": 14200,
                "average_session_duration_sec": 194.2,
                "bounce_rate_pct": 35.7,
                "conversion_rate_pct": 2.89,
            },
        )
