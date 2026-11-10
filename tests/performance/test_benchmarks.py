from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from analytics.roi import DeterministicROIEngine
from api.main import app

os.environ["AISMA_TEST_MODE"] = "true"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_benchmark_api_and_db_latency(client: TestClient) -> None:
    # Warm up
    client.get("/api/v1/ready")

    latencies_ms: list[float] = []
    for _ in range(20):
        t0 = time.perf_counter()
        resp = client.get("/api/v1/ready")
        t1 = time.perf_counter()
        assert resp.status_code == 200
        latencies_ms.append((t1 - t0) * 1000)

    avg_ms = sum(latencies_ms) / len(latencies_ms)
    p95_ms = sorted(latencies_ms)[int(len(latencies_ms) * 0.95)]
    assert avg_ms < 50.0, f"DB readiness avg latency too high: {avg_ms:.2f}ms"
    assert p95_ms < 100.0, f"DB readiness p95 latency too high: {p95_ms:.2f}ms"


def test_benchmark_deterministic_roi_throughput() -> None:
    channels = [
        {"channel": "linkedin", "spend": 2500.0, "revenue": 14000.0, "impressions": 40000, "clicks": 1500, "conversions": 35},
        {"channel": "meta", "spend": 1800.0, "revenue": 8200.0, "impressions": 72000, "clicks": 2600, "conversions": 22},
    ]

    t0 = time.perf_counter()
    for _ in range(100):
        res = DeterministicROIEngine.evaluate_performance("biz_bench", "Last 30 Days", channels)
        assert res.blended_roas > 0
    elapsed_ms = (time.perf_counter() - t0) * 1000

    assert elapsed_ms < 250.0, f"100 ROI evaluations took {elapsed_ms:.2f}ms (expected <250ms)"


def test_benchmark_controlled_concurrent_api_requests(client: TestClient) -> None:
    def fetch_roi(_: int) -> int:
        r = client.get("/api/v1/analytics/roi")
        return r.status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(fetch_roi, range(24)))

    assert all(code == 200 for code in statuses)

