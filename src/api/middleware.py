from __future__ import annotations

import logging
import os
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("aisma.api")


class CorrelationAndLoggingMiddleware(BaseHTTPMiddleware):
    """Assigns X-Correlation-ID to every request/response and emits structured audit timings."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or f"req_{uuid.uuid4().hex[:12]}"
        start_time = time.perf_counter()

        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        # Redact authorization and cookie values from logs
        logger.info(
            "api_request",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        return response


class SlidingWindowRateLimiter:
    """In-memory sliding-window rate limiter per client IP + route bucket."""

    def __init__(self, default_limit: int = 300, auth_limit: int = 30, window_seconds: int = 60) -> None:
        self.default_limit = default_limit
        self.auth_limit = auth_limit
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str, is_auth_route: bool = False) -> tuple[bool, int]:
        now = time.time()
        limit = self.auth_limit if is_auth_route else self.default_limit
        bucket = self._buckets[key]

        # Evict expired timestamps
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= limit:
            retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
            return False, retry_after

        bucket.append(now)
        return True, 0


_global_rate_limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Protects auth and write endpoints against brute-force and abuse."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Allow automated tests to opt out unless explicitly testing rate limiting
        if os.getenv("AISMA_TEST_MODE") == "true" and request.headers.get("X-Test-Rate-Limit") != "true":
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        is_auth = request.url.path.startswith("/api/v1/auth/")
        bucket_key = f"{client_ip}:{'auth' if is_auth else 'general'}"

        allowed, retry_after = _global_rate_limiter.is_allowed(bucket_key, is_auth_route=is_auth)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Too many requests.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
