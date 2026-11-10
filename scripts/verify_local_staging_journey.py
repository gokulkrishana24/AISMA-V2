from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


def wait_for_http(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(url, timeout=2.0)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main() -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR / "src")
    env["AISMA_TEST_MODE"] = "true"
    env["AISMA_ENV"] = "development"

    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BASE_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    frontend_proc = subprocess.Popen(
        ["npm.cmd" if os.name == "nt" else "npm", "run", "start", "--", "-H", "127.0.0.1", "-p", "3000"],
        cwd=str(FRONTEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    results: list[dict[str, Any]] = []
    try:
        if not wait_for_http("http://127.0.0.1:8000/api/v1/ready", timeout=25.0):
            print("ERROR: FastAPI backend failed to become ready on 127.0.0.1:8000")
            return 1
        if not wait_for_http("http://127.0.0.1:3000/login", timeout=25.0):
            print("ERROR: Next.js frontend failed to become ready on 127.0.0.1:3000")
            return 1

        client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)
        uid = uuid.uuid4().hex[:6]
        email = f"journey_{uid}@staging-local.ai"
        password = "JourneyPassword123!"

        def record(step: str, resp: httpx.Response, expected: int = 200) -> dict[str, Any]:
            ok = resp.status_code == expected
            latency_ms = round(resp.elapsed.total_seconds() * 1000, 2)
            results.append({"step": step, "status": resp.status_code, "expected": expected, "ok": ok, "latency_ms": latency_ms})
            if not ok:
                raise RuntimeError(f"Step '{step}' failed: HTTP {resp.status_code} != {expected}: {resp.text}")
            return resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}

        # 1. Register
        record(
            "1_register",
            client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": password, "full_name": "Staging Pilot", "business_name": f"Pilot Org {uid}", "role": "admin"},
            ),
        )
        # 2. Login
        login_data = record("2_login", client.post("/api/v1/auth/login", json={"email": email, "password": password}))
        token = login_data["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Profile
        record("3_auth_me", client.get("/api/v1/auth/me", headers=headers))

        # 4. Onboarding setup
        onb = record(
            "4_onboarding_setup",
            client.post(
                "/api/v1/onboarding/setup",
                headers=headers,
                json={"company_name": f"Pilot Workspace {uid}", "industry": "SaaS", "target_audience": "B2B", "primary_channels": ["linkedin"], "selected_plan": "professional"},
            ),
        )
        biz_id = onb["business_id"]
        tenant_headers = {**headers, "X-Business-Id": biz_id}

        # 5. List organizations
        orgs = record("5_organizations_list", client.get("/api/v1/organizations", headers=headers))
        assert any(o["id"] == biz_id for o in orgs)

        # 6. Brand OS
        record("6_brand_os_fetch", client.get("/api/v1/brand-os", headers=tenant_headers))

        # 7. Invite member
        record(
            "7_invite_member",
            client.post("/api/v1/organizations/current/invites", headers=tenant_headers, json={"email": f"team_{uid}@staging-local.ai", "role": "operator"}),
        )

        # 8. Sandbox OAuth flow
        oauth_start = record("8a_oauth_start", client.get("/api/v1/integrations/linkedin/oauth/start", headers=tenant_headers))
        record(
            "8b_oauth_callback",
            client.post(
                "/api/v1/integrations/linkedin/oauth/callback",
                headers=tenant_headers,
                json={"state": oauth_start["state"], "code": "sandbox_code_ok", "account_name": "Pilot LinkedIn"},
            ),
        )

        # 9. Create draft
        record(
            "9_create_draft",
            client.post("/api/v1/content/drafts", headers=tenant_headers, json={"title": "Staging Draft", "channel": "linkedin", "content": "Verified staging launch copy."}),
        )

        # 10. Approval decision
        record(
            "10_approval_decision",
            client.post(
                f"/api/v1/approvals/appr_stg_{uid}/decision",
                headers=tenant_headers,
                json={"action": "approve", "note": "Verified staging", "actor": "human_admin"},
            ),
        )

        # 11 & 12. Schedule post & verify calendar
        sched_time = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=4)).isoformat()
        record(
            "11_schedule_post",
            client.post("/api/v1/scheduler/posts", headers=tenant_headers, json={"channel": "linkedin", "content": f"Scheduled {uid}", "scheduled_time": sched_time}),
        )
        cal = record("12_scheduler_calendar", client.get("/api/v1/scheduler/calendar", headers=tenant_headers))
        assert len(cal) >= 1

        # 13. Deterministic ROI analytics
        roi = record("13_analytics_roi", client.get("/api/v1/analytics/roi", headers=tenant_headers))
        assert len(roi["deterministic_audit_hash"]) == 64

        # 14. Billing & Quota
        record("14a_billing_subscription", client.get("/api/v1/billing/subscription", headers=tenant_headers))
        record("14b_billing_quota", client.get("/api/v1/billing/quota", headers=tenant_headers))

        # 15. Notifications
        record("15_notifications", client.get("/api/v1/notifications", headers=tenant_headers))

        # 16. Next.js SSR / Static routes live check on 127.0.0.1:3000
        fe_client = httpx.Client(base_url="http://127.0.0.1:3000", timeout=10.0)
        for route in ["/", "/dashboard", "/agents", "/approvals", "/analytics", "/infrastructure", "/onboarding", "/login"]:
            record(f"16_frontend_{route}", fe_client.get(route))

        # 17. Logout & Token Revocation
        record("17a_logout", client.post("/api/v1/auth/logout", headers=headers))
        record("17b_revoked_rejected", client.get("/api/v1/auth/me", headers=headers), expected=401)

        print(json.dumps({"journey_passed": True, "steps_verified": len(results), "results": results}, indent=2))
        return 0

    finally:
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
        except Exception:
            backend_proc.kill()
        try:
            frontend_proc.wait(timeout=5)
        except Exception:
            frontend_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
