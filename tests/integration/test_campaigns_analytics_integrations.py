from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from api.main import app

os.environ["AISMA_TEST_MODE"] = "true"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_integrations_list_and_health(client: TestClient) -> None:
    resp = client.get("/api/v1/integrations")
    assert resp.status_code == 200
    platforms = {item["platform"] for item in resp.json()}
    assert "linkedin" in platforms
    assert "meta" in platforms
    assert "twitter" in platforms
    assert "gsc" in platforms
    assert "ga4" in platforms
    assert "reviews" in platforms


def test_integrations_publish_sandbox(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/integrations/linkedin/publish",
        json={"content": "Autonomous Enterprise Marketing with AISMA v2", "media_urls": []},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["platform"] == "linkedin"
    assert data["is_sandbox"] is True
    assert "urn:li:share:" in data["post_id"]


def test_campaigns_lifecycle(client: TestClient) -> None:
    # 1. Create campaign
    create_resp = client.post(
        "/api/v1/campaigns",
        json={
            "name": "Q4 Enterprise Brand Launch",
            "objective": "brand_awareness",
            "budget_allocated": 10000.0,
            "channels": ["linkedin", "twitter"],
        },
    )
    assert create_resp.status_code == 200
    camp = create_resp.json()
    camp_id = camp["id"]
    assert camp["name"] == "Q4 Enterprise Brand Launch"
    assert camp["status"] == "draft"

    # 2. Update status to active
    update_resp = client.patch(
        f"/api/v1/campaigns/{camp_id}/status",
        json={"status": "active"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "active"

    # 3. Record spend
    spend_resp = client.post(
        f"/api/v1/campaigns/{camp_id}/spend",
        json={"amount": 450.0},
    )
    assert spend_resp.status_code == 200
    assert spend_resp.json()["budget_spent"] == 450.0


def test_deterministic_roi_analytics(client: TestClient) -> None:
    resp = client.get("/api/v1/analytics/roi")
    assert resp.status_code == 200
    data = resp.json()
    assert "blended_roas" in data
    assert "marketing_roi_percentage" in data
    assert "customer_acquisition_cost" in data
    assert len(data["channels"]) >= 4
    # Verify deterministic audit hash is a 64-char hex string
    assert len(data["deterministic_audit_hash"]) == 64
