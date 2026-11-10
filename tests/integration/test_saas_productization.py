from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient

from api.deps import STORE_BUSINESS_ID
from api.main import app

os.environ["AISMA_TEST_MODE"] = "true"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_customer_onboarding_and_org_provisioning(client: TestClient) -> None:
    uid = uuid.uuid4().hex[:6]
    # 1. Register new user
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"founder_{uid}@scaleup.io",
            "password": "SecurePassword123!",
            "full_name": f"Founder {uid}",
            "business_name": f"ScaleUp Tech {uid}",
            "role": "admin",
        },
    )
    assert reg_resp.status_code == 200
    token = reg_resp.json()["token"]

    # 2. Complete guided onboarding setup
    setup_resp = client.post(
        "/api/v1/onboarding/setup",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_name": f"ScaleUp AI {uid}",
            "industry": "Marketing Technology",
            "target_audience": "Mid-market demand gen directors",
            "primary_channels": ["linkedin", "twitter"],
            "selected_plan": "professional",
        },
    )
    assert setup_resp.status_code == 200
    data = setup_resp.json()
    assert data["success"] is True
    assert data["plan"] == "professional"
    new_biz_id = data["business_id"]

    # 3. List user organizations and verify membership
    orgs_resp = client.get("/api/v1/organizations", headers={"Authorization": f"Bearer {token}"})
    assert orgs_resp.status_code == 200
    org_ids = [o["id"] for o in orgs_resp.json()]
    assert new_biz_id in org_ids

    # 4. Invite team member
    invite_resp = client.post(
        "/api/v1/organizations/current/invites",
        headers={"Authorization": f"Bearer {token}", "X-Business-Id": new_biz_id},
        json={"email": f"colleague_{uid}@scaleup.io", "role": "operator"},
    )
    assert invite_resp.status_code == 200
    assert "invite_url" in invite_resp.json()


def test_billing_plans_and_usage_quota(client: TestClient) -> None:
    # 1. List available subscription tiers
    plans_resp = client.get("/api/v1/billing/plans")
    assert plans_resp.status_code == 200
    slugs = [p["slug"] for p in plans_resp.json()]
    assert "starter" in slugs
    assert "professional" in slugs
    assert "agency" in slugs
    assert "enterprise" in slugs

    # 2. Check enterprise subscription & quota
    sub_resp = client.get(
        "/api/v1/billing/subscription",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert sub_data["status"] == "active"
    assert "usage" in sub_data

    # 3. Check quota endpoint
    quota_resp = client.get(
        "/api/v1/billing/quota",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
    )
    assert quota_resp.status_code == 200
    quota_data = quota_resp.json()
    assert quota_data["allowed"] is True
    assert quota_data["max_executions"] >= 1000


def test_in_app_notifications_and_support_flow(client: TestClient) -> None:
    # 1. Fetch notifications
    notif_resp = client.get(
        "/api/v1/notifications",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
    )
    assert notif_resp.status_code == 200
    assert isinstance(notif_resp.json(), list)

    # 2. Create customer support ticket
    tkt_resp = client.post(
        "/api/v1/support/tickets",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
        json={
            "subject": "Inquiry regarding custom Ollama model routing",
            "description": "We are planning to deploy a fine-tuned Qwen model alongside Phi-3.5.",
            "priority": "medium",
        },
    )
    assert tkt_resp.status_code == 200
    assert tkt_resp.json()["status"] == "open"
    assert "tkt_" in tkt_resp.json()["id"]


def test_privacy_gdpr_data_export_and_retention(client: TestClient) -> None:
    # 1. GDPR / CCPA data portability export
    export_resp = client.get(
        "/api/v1/privacy/export",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
    )
    assert export_resp.status_code == 200
    data = export_resp.json()
    assert "export_metadata" in data
    assert data["export_metadata"]["compliance"] == "GDPR Article 20 / CCPA Data Portability"
    assert "user_profile" in data
    assert "brand_os" in data
    assert "audit_logs" in data

