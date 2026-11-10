from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.deps import STORE_BUSINESS_ID
from api.main import app

os.environ["AISMA_TEST_MODE"] = "true"

# Ensure scripts directory is importable for backup/restore test
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_correlation_id_and_readiness_headers(client: TestClient) -> None:
    resp = client.get("/api/v1/ready")
    assert resp.status_code == 200
    assert resp.json()["ready"] is True
    assert resp.json()["database"] == "connected"
    assert "X-Correlation-ID" in resp.headers
    assert "X-Response-Time-Ms" in resp.headers


def test_refresh_token_and_logout_revocation(client: TestClient) -> None:
    # 1. Login and retrieve both access & refresh tokens
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "marcus.vance@apexmarketing.ai", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    access_token = data["token"]
    refresh_token = data["refresh_token"]
    assert access_token
    assert refresh_token

    # 2. Refresh access token
    ref_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_resp.status_code == 200
    new_access = ref_resp.json()["token"]
    assert new_access

    # 3. Logout revokes the token immediately
    logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True

    # 4. Reusing revoked access token must fail with 401
    reused_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert reused_resp.status_code == 401


def test_rate_limiter_enforces_429(client: TestClient) -> None:
    # Trigger auth route rate limit (30 requests/min)
    hit_429 = False
    for _ in range(35):
        r = client.get("/api/v1/auth/me", headers={"X-Test-Rate-Limit": "true"})
        if r.status_code == 429:
            hit_429 = True
            assert "Retry-After" in r.headers
            break
    assert hit_429 is True


def test_oauth_csrf_state_and_webhook_hmac(client: TestClient) -> None:
    # 1. Start OAuth flow
    start_resp = client.get(
        "/api/v1/integrations/linkedin/oauth/start",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
    )
    assert start_resp.status_code == 200
    state_token = start_resp.json()["state"]

    # 2. Tampered CSRF state rejects with 400
    bad_cb = client.post(
        "/api/v1/integrations/linkedin/oauth/callback",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
        json={"state": "forged_csrf_state", "code": "auth_code_123"},
    )
    assert bad_cb.status_code == 400

    # 3. Valid callback completes connection and encrypts token
    good_cb = client.post(
        "/api/v1/integrations/linkedin/oauth/callback",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
        json={"state": state_token, "code": "valid_code_xyz", "account_name": "Apex Official"},
    )
    assert good_cb.status_code == 200
    assert good_cb.json()["token_encrypted_at_rest"] is True

    # 4. Webhook HMAC signature check
    payload = json.dumps({"event": "post.published", "id": "123"}).encode("utf-8")
    secret = os.getenv("INTEGRATION_WEBHOOK_SECRET", "aisma_webhook_hmac_secret_2026")
    valid_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    bad_wh = client.post(
        "/api/v1/integrations/linkedin/webhook",
        content=payload,
        headers={"X-AISMA-Signature": "invalid_sig", "Content-Type": "application/json"},
    )
    assert bad_wh.status_code == 401

    good_wh = client.post(
        "/api/v1/integrations/linkedin/webhook",
        content=payload,
        headers={"X-AISMA-Signature": f"sha256={valid_sig}", "Content-Type": "application/json"},
    )
    assert good_wh.status_code == 200
    assert good_wh.json()["signature_verified"] is True


def test_scheduler_duplicate_prevention_and_triggers(client: TestClient) -> None:
    scheduled_dt = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)).isoformat()
    unique_content = f"Enterprise AI Automation Launch {uuid.uuid4().hex[:6]}"

    r1 = client.post(
        "/api/v1/scheduler/posts",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
        json={"channel": "linkedin", "content": unique_content, "scheduled_time": scheduled_dt},
    )
    assert r1.status_code == 200

    # Duplicate post at identical channel & time must fail with 409 Conflict
    r2 = client.post(
        "/api/v1/scheduler/posts",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
        json={"channel": "linkedin", "content": unique_content, "scheduled_time": scheduled_dt},
    )
    assert r2.status_code == 409

    # Automation trigger rule test
    rule_resp = client.post(
        "/api/v1/scheduler/rules",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
        json={
            "name": "Critical Review Escalation",
            "trigger_type": "review_alert",
            "condition": {"max_rating": 2},
            "target_agent_id": "reviews_reputation",
        },
    )
    assert rule_resp.status_code == 200

    eval_resp = client.post(
        "/api/v1/scheduler/evaluate",
        headers={"X-Business-Id": STORE_BUSINESS_ID},
        json={"event_type": "review_alert", "event_data": {"rating": 1, "author": "Unhappy User"}},
    )
    assert eval_resp.status_code == 200
    assert eval_resp.json()["triggered_count"] >= 1


def test_admin_rbac_and_feature_flags(client: TestClient) -> None:
    # 1. Register non-admin operator
    uid = uuid.uuid4().hex[:6]
    reg_op = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"op_{uid}@example.com",
            "password": "OpPassword123!",
            "full_name": "Regular Operator",
            "role": "operator",
        },
    )
    op_token = reg_op.json()["token"]

    # Operator blocked from platform admin overview
    forbidden = client.get("/api/v1/admin/overview", headers={"Authorization": f"Bearer {op_token}"})
    assert forbidden.status_code == 403

    # Admin accesses overview and feature flags
    login_admin = client.post(
        "/api/v1/auth/login",
        json={"email": "marcus.vance@apexmarketing.ai", "password": "Password123!"},
    )
    admin_token = login_admin.json()["token"]

    admin_ov = client.get("/api/v1/admin/overview", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_ov.status_code == 200
    assert admin_ov.json()["metrics"]["total_organizations"] >= 1

    flag_resp = client.put(
        "/api/v1/admin/feature-flags/beta_predictive_roi",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"enabled": True},
    )
    assert flag_resp.status_code == 200
    assert flag_resp.json()["enabled"] is True


def test_database_backup_and_restore_integrity(tmp_path: Path) -> None:
    from backup_restore import backup_sqlite, verify_and_restore_sqlite

    backup_dir = tmp_path / "backups"
    restored_db = tmp_path / "restored.db"

    manifest = backup_sqlite(output_dir=backup_dir)
    backup_file = Path(manifest["backup_file"])
    manifest_file = backup_dir / f"aisma_backup_{manifest['timestamp_utc']}.manifest.json"

    assert backup_file.exists()
    assert len(manifest["sha256"]) == 64

    ok = verify_and_restore_sqlite(backup_file, manifest_file, restored_db)
    assert ok is True
    assert restored_db.exists()


def test_billing_webhook_hmac_and_idempotency(client: TestClient) -> None:
    event_id = f"evt_{uuid.uuid4().hex[:10]}"
    payload = json.dumps(
        {
            "event_id": event_id,
            "event_type": "invoice.payment_failed",
            "business_id": STORE_BUSINESS_ID,
        }
    ).encode("utf-8")
    secret = os.getenv("BILLING_WEBHOOK_SECRET", "aisma_billing_webhook_hmac_secret_2026")
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    # 1. Invalid signature rejects with 401
    bad = client.post(
        "/api/v1/billing/webhook",
        content=payload,
        headers={"X-Billing-Signature": "forged", "Content-Type": "application/json"},
    )
    assert bad.status_code == 401

    # 2. First valid delivery transitions subscription to past_due
    r1 = client.post(
        "/api/v1/billing/webhook",
        content=payload,
        headers={"X-Billing-Signature": f"sha256={sig}", "Content-Type": "application/json"},
    )
    assert r1.status_code == 200
    assert r1.json()["duplicate_ignored"] is False
    assert r1.json()["subscription_status"] == "past_due"

    # 3. Duplicate delivery is idempotently ignored
    r2 = client.post(
        "/api/v1/billing/webhook",
        content=payload,
        headers={"X-Billing-Signature": f"sha256={sig}", "Content-Type": "application/json"},
    )
    assert r2.status_code == 200
    assert r2.json()["duplicate_ignored"] is True

    # Restore active status via invoice.paid event
    restore_payload = json.dumps(
        {
            "event_id": f"evt_restore_{uuid.uuid4().hex[:8]}",
            "event_type": "invoice.paid",
            "business_id": STORE_BUSINESS_ID,
        }
    ).encode("utf-8")
    restore_sig = hmac.new(secret.encode("utf-8"), restore_payload, hashlib.sha256).hexdigest()
    r3 = client.post(
        "/api/v1/billing/webhook",
        content=restore_payload,
        headers={"X-Billing-Signature": restore_sig, "Content-Type": "application/json"},
    )
    assert r3.status_code == 200
    assert r3.json()["subscription_status"] == "active"


def test_production_security_fail_closed_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    from api.main import validate_production_security

    monkeypatch.setenv("AISMA_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "short_dev")
    with pytest.raises(RuntimeError, match="SECURITY BLOCK"):
        validate_production_security()

    monkeypatch.setenv("JWT_SECRET_KEY", "a_very_strong_random_production_secret_key_over_32_characters_long")
    monkeypatch.setenv("INTEGRATION_VAULT_SECRET", "aisma_vault_enterprise_encryption_key_32_bytes_safe")
    with pytest.raises(RuntimeError, match="INTEGRATION_VAULT_SECRET"):
        validate_production_security()

    monkeypatch.setenv("INTEGRATION_VAULT_SECRET", "prod_unique_vault_encryption_secret_32_bytes_verified")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")
    with pytest.raises(RuntimeError, match="Wildcard CORS"):
        validate_production_security()

    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.aisma.example")
    validate_production_security()  # Should pass cleanly


