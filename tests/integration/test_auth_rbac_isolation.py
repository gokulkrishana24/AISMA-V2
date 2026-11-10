from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from api.main import app

os.environ["AISMA_TEST_MODE"] = "true"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_auth_login_success_and_jwt_issuance(client: TestClient) -> None:
    payload = {
        "email": "marcus.vance@apexmarketing.ai",
        "password": "Password123!",
    }
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "marcus.vance@apexmarketing.ai"
    assert data["user"]["role"] == "admin"


def test_auth_login_invalid_credentials(client: TestClient) -> None:
    payload = {
        "email": "marcus.vance@apexmarketing.ai",
        "password": "WrongPassword123!",
    }
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 401
    assert "Incorrect email or password" in resp.json()["detail"]


def test_auth_me_authenticated_and_invalid_token(client: TestClient) -> None:
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "marcus.vance@apexmarketing.ai", "password": "Password123!"},
    )
    token = login_resp.json()["token"]

    # Valid token
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "marcus.vance@apexmarketing.ai"

    # Invalid / forged token
    bad_resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_forged_token"})
    assert bad_resp.status_code == 401


def test_tenant_registration_and_cross_tenant_isolation(client: TestClient) -> None:
    import uuid
    uid_a = uuid.uuid4().hex[:8]
    uid_b = uuid.uuid4().hex[:8]

    # 1. Register Tenant A
    reg_a = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"sarah_{uid_a}@innovate-tech.ai",
            "password": "SecurePasswordA123!",
            "full_name": "Sarah Connor",
            "business_name": f"Innovate Tech AI {uid_a}",
            "role": "operator",
        },
    )
    assert reg_a.status_code == 200
    token_a = reg_a.json()["token"]
    biz_a_id = reg_a.json()["user"]["businessId"]

    # 2. Register Tenant B
    reg_b = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"dave_{uid_b}@synergy-corp.io",
            "password": "SecurePasswordB456!",
            "full_name": "Dave Bowman",
            "business_name": f"Synergy Corp IO {uid_b}",
            "role": "operator",
        },
    )
    assert reg_b.status_code == 200
    token_b = reg_b.json()["token"]
    biz_b_id = reg_b.json()["user"]["businessId"]

    assert biz_a_id != biz_b_id

    # 3. Tenant A accessing Tenant A's approvals -> 200 OK
    resp_a_own = client.get(
        "/api/v1/approvals",
        headers={"Authorization": f"Bearer {token_a}", "X-Business-Id": biz_a_id},
    )
    assert resp_a_own.status_code == 200

    # 4. Tenant A attempting to access Tenant B's approvals -> 403 Forbidden!
    resp_cross_a = client.get(
        "/api/v1/approvals",
        headers={"Authorization": f"Bearer {token_a}", "X-Business-Id": biz_b_id},
    )
    assert resp_cross_a.status_code == 403
    assert "Access denied" in resp_cross_a.json()["detail"]

    # 5. Tenant B attempting to access Tenant A's governance killswitch -> 403 Forbidden!
    resp_cross_b = client.get(
        "/api/v1/governance/killswitch",
        headers={"Authorization": f"Bearer {token_b}", "X-Business-Id": biz_a_id},
    )
    assert resp_cross_b.status_code == 403
    assert "Access denied" in resp_cross_b.json()["detail"]

    # 6. Tenant B accessing Tenant B's own governance killswitch -> 200 OK
    resp_b_own = client.get(
        "/api/v1/governance/killswitch",
        headers={"Authorization": f"Bearer {token_b}", "X-Business-Id": biz_b_id},
    )
    assert resp_b_own.status_code == 200
    assert "engaged" in resp_b_own.json()
