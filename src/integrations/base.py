from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class PublishPayload(BaseModel):
    content: str
    channel: str
    media_urls: list[str] = Field(default_factory=list)
    scheduled_at: datetime.datetime | None = None
    target_audience: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PublishResult(BaseModel):
    success: bool
    platform: str
    post_id: str | None = None
    url: str | None = None
    published_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    error: str | None = None
    is_sandbox: bool = False


class AnalyticsMetrics(BaseModel):
    platform: str
    period_start: str
    period_end: str
    impressions: int = 0
    reach: int = 0
    clicks: int = 0
    engagements: int = 0
    engagement_rate: float = 0.0
    conversions: int = 0
    spend: float = 0.0
    extra: dict[str, Any] = Field(default_factory=dict)


class AdapterHealth(BaseModel):
    platform: str
    connected: bool
    status_code: int = 200
    message: str = "Connected"
    latency_ms: float = 0.0


class PlatformAdapter(ABC):
    def __init__(self, platform_name: str, is_sandbox: bool = True) -> None:
        self.platform_name = platform_name
        self.is_sandbox = is_sandbox

    @abstractmethod
    def health_check(self) -> AdapterHealth:
        """Verify API connectivity and token validity."""
        pass

    @abstractmethod
    def publish(self, payload: PublishPayload) -> PublishResult:
        """Publish content or simulate in sandbox mode."""
        pass

    @abstractmethod
    def fetch_analytics(self, days: int = 30) -> AnalyticsMetrics:
        """Retrieve recent performance analytics."""
        pass
