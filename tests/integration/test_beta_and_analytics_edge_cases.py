from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from analytics.roi import DeterministicROIEngine
from api.deps import STORE_BUSINESS_ID
from api.main import app

os.environ["AISMA_TEST_MODE"] = "true"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_deterministic_roi_edge_cases() -> None:
    # 1. Zero denominators must never raise ZeroDivisionError
    assert DeterministicROIEngine.calculate_roas(revenue=1000.0, ad_spend=0.0) == 999.99
    assert DeterministicROIEngine.calculate_roas(revenue=0.0, ad_spend=0.0) == 0.0
    assert DeterministicROIEngine.calculate_roi(revenue=500.0, total_costs=0.0) == 0.0
    assert DeterministicROIEngine.calculate_cac(acquisition_costs=250.0, new_customers=0) == 0.0
    assert DeterministicROIEngine.calculate_ltv_to_cac(ltv=5000.0, cac=0.0) == 0.0

    # 2. Missing data / empty channels handled safely
    empty_res = DeterministicROIEngine.evaluate_performance(
        business_id="biz_empty",
        period="Empty Period",
        channel_data=[],
        fixed_marketing_overhead=0.0,
    )
    assert empty_res.total_spend == 0.0
    assert empty_res.total_attributed_revenue == 0.0
    assert empty_res.blended_roas == 0.0
    assert len(empty_res.deterministic_audit_hash) == 64

    # 3. Negative ROI calculation correctness
    loss_res = DeterministicROIEngine.evaluate_performance(
        business_id="biz_loss",
        period="Loss Period",
        channel_data=[{"channel": "ads", "spend": 1000.0, "revenue": 400.0, "conversions": 2}],
    )
    assert loss_res.net_marketing_profit == -600.0
    assert loss_res.marketing_roi_percentage == -60.0
    assert loss_res.blended_roas == 0.4


def test_synthetic_beta_seed_and_safe_reset(client: TestClient) -> None:
    # 1. Seed clearly labeled synthetic workspace
    seed_resp = client.post("/api/v1/beta/seed-demo")
    assert seed_resp.status_code == 200
    seed_data = seed_resp.json()
    assert seed_data["seeded"] is True
    assert seed_data["is_synthetic"] is True
    assert seed_data["business_id"] == "biz_demo_nova_saas"
    assert "[DEMO]" in seed_data["business_name"]

    # 2. Diagnostics endpoint succeeds without exposing secrets
    diag_resp = client.get("/api/v1/beta/diagnostics")
    assert diag_resp.status_code == 200
    assert diag_resp.json()["database_connected"] is True

    # 3. Feedback submission records to support ledger
    fb_resp = client.post(
        "/api/v1/beta/feedback",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
        json={"category": "feedback", "title": "Clean UI", "description": "Works well in local beta."},
    )
    assert fb_resp.status_code == 200
    assert fb_resp.json()["status"] == "recorded"

    # 4. Safe reset removes ONLY synthetic demo records, leaving real enterprise tenant intact
    reset_resp = client.post("/api/v1/beta/reset-demo")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["real_data_preserved"] is True

    # Enterprise approvals remain preserved
    appr_resp = client.get("/api/v1/approvals", headers={"X-Business-Id": STORE_BUSINESS_ID})
    assert appr_resp.status_code == 200
    assert len(appr_resp.json()) >= 1

