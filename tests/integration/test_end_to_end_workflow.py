from __future__ import annotations

import os

os.environ["AISMA_TEST_MODE"] = "true"

import pytest
from fastapi.testclient import TestClient

from api.deps import (
    STORE_BUSINESS_ID,
)
from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_complete_end_to_end_marketing_workflow(client):
    """
    Verification Milestone:
    Business Objective ➔ Content Engine draft ➔ Policy/Brand check ➔ Human Approval Center ➔ SHA-256 Audit Record.
    """
    # 1. Verify Brand OS & Policy Context is active
    r_brand = client.get("/api/v1/brand-os")
    assert r_brand.status_code == 200
    brand_data = r_brand.json()
    assert "authoritative" in str(brand_data["brand_voice"]).lower()

    # 2. Execute Content Engine with Business Objective
    objective = "Launch Q4 Enterprise AI Playbook: Shift from scheduled posts to intent-driven multi-agent orchestration"
    r_exec = client.post(
        "/api/v1/agents/content_engine/execute",
        json={
            "action": "content_generation",
            "objective": objective,
            "parameters": {
                "channel": "linkedin",
                "title": "Q4 Enterprise AI Playbook",
                "target_audience": "Heads of Marketing & Social Operations",
            },
            "business_id": STORE_BUSINESS_ID,
        },
    )
    assert r_exec.status_code == 200
    exec_data = r_exec.json()
    assert exec_data["agent_id"] == "content_engine"
    assert exec_data["status"] in {"completed", "pending_approval"}
    assert exec_data["requires_human_approval"] is True
    assert exec_data["approval_id"] is not None

    approval_id = exec_data["approval_id"]

    # 3. Verify the draft is enqueued in the Human Approval Center (Fail-Closed Gate)
    r_approvals = client.get("/api/v1/approvals")
    assert r_approvals.status_code == 200
    approvals = r_approvals.json()
    pending_item = next((a for a in approvals if a["id"] == approval_id), None)
    assert pending_item is not None
    assert pending_item["status"] == "pending"

    # 4. Human Admin submits Approval Decision (Authorized Signoff)
    r_decision = client.post(
        f"/api/v1/approvals/{approval_id}/decision",
        json={
            "action": "approve",
            "note": "Verified brand voice, technical rigor, and proof point accuracy. Approved for publishing queue.",
            "actor": "human_admin",
        },
    )
    assert r_decision.status_code == 200
    decision_data = r_decision.json()
    assert decision_data["status"] == "approved"
    assert decision_data["audited"] is True
    assert "entry_hash" in decision_data
    assert len(decision_data["entry_hash"]) == 64  # Valid SHA-256 hex string

    # 5. Verify the approval record has transitioned
    r_approvals_after = client.get("/api/v1/approvals")
    updated_item = next((a for a in r_approvals_after.json() if a["id"] == approval_id), None)
    assert updated_item is not None
    assert updated_item["status"] == "approved"

    # 6. Verify Cryptographic SHA-256 Audit Ledger Chain
    r_verify = client.post("/api/v1/governance/audit/verify")
    assert r_verify.status_code == 200
    verify_result = r_verify.json()
    assert verify_result["valid"] is True
    assert verify_result["verifiedCount"] >= 1
    assert "clean" in verify_result["message"].lower() or "passed" in verify_result["message"].lower() or "verified" in verify_result["message"].lower()

