from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_audit_logger, get_db, require_tenant_access
from db.models import SocialAccount
from integrations import (
    CredentialVault,
    GA4Adapter,
    GSCAdapter,
    LinkedInAdapter,
    MetaAdapter,
    PublishPayload,
    ReviewsAdapter,
    XTwitterAdapter,
)

router = APIRouter(prefix="/api/v1/integrations", tags=["External Social & Analytics Integrations"])

# In-memory CSRF state validation store: state -> {business_id, platform}
_OAUTH_STATE_STORE: dict[str, dict[str, str]] = {}
_WEBHOOK_SECRET = os.getenv("INTEGRATION_WEBHOOK_SECRET", "aisma_webhook_hmac_secret_2026")


def _get_adapters() -> dict[str, Any]:
    return {
        "linkedin": LinkedInAdapter(is_sandbox=True),
        "meta": MetaAdapter(is_sandbox=True),
        "twitter": XTwitterAdapter(is_sandbox=True),
        "gsc": GSCAdapter(is_sandbox=True),
        "ga4": GA4Adapter(is_sandbox=True),
        "reviews": ReviewsAdapter(is_sandbox=True),
    }


class DirectPublishRequest(BaseModel):
    content: str
    media_urls: list[str] = []


class OAuthCallbackPayload(BaseModel):
    state: str
    code: str
    account_name: str = "Connected Enterprise Page"


@router.get("")
def list_connected_integrations(business_id: str = Depends(require_tenant_access)) -> list[dict[str, Any]]:
    adapters = _get_adapters()
    results = []
    for name, adapter in adapters.items():
        health = adapter.health_check()
        results.append(
            {
                "platform": name,
                "connected": health.connected,
                "status": health.message,
                "is_sandbox": adapter.is_sandbox,
                "latency_ms": health.latency_ms,
            }
        )
    return results


@router.get("/{platform}/health")
def check_platform_health(platform: str, business_id: str = Depends(require_tenant_access)) -> dict[str, Any]:
    adapters = _get_adapters()
    adapter = adapters.get(platform.lower())
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Unsupported platform '{platform}'")
    health = adapter.health_check()
    return health.model_dump()


@router.get("/{platform}/oauth/start")
def start_oauth_flow(
    platform: str,
    business_id: str = Depends(require_tenant_access),
) -> dict[str, Any]:
    adapters = _get_adapters()
    if platform.lower() not in adapters:
        raise HTTPException(status_code=404, detail=f"Unsupported platform '{platform}'")

    state_token = secrets.token_urlsafe(32)
    _OAUTH_STATE_STORE[state_token] = {
        "business_id": business_id,
        "platform": platform.lower(),
    }

    return {
        "platform": platform.lower(),
        "state": state_token,
        "authorization_url": f"https://auth.platform.sandbox/{platform.lower()}/authorize?state={state_token}",
        "is_sandbox": True,
    }


@router.post("/{platform}/oauth/callback")
def complete_oauth_callback(
    platform: str,
    payload: OAuthCallbackPayload,
    business_id: str = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    state_record = _OAUTH_STATE_STORE.pop(payload.state, None)
    if not state_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth CSRF state parameter.",
        )

    if state_record["business_id"] != business_id or state_record["platform"] != platform.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OAuth state tenant or platform mismatch.",
        )

    vault = CredentialVault()
    # Sandbox token exchange representation
    simulated_access_token = f"sandbox_oauth_tok_{platform.lower()}_{payload.code[:8]}"
    encrypted_token = vault.encrypt(simulated_access_token)

    acc = SocialAccount(
        id=f"soc_{uuid.uuid4().hex[:12]}",
        business_id=business_id,
        platform=platform.lower(),
        account_name=payload.account_name,
        account_id=f"acct_{uuid.uuid4().hex[:8]}",
        status="connected",
        encrypted_access_token=encrypted_token,
    )
    db.add(acc)
    db.commit()

    audit = get_audit_logger()
    audit.log(
        business_id=business_id,
        actor="oauth_system",
        action="oauth_account_connected",
        resource=f"social_account:{acc.id}",
        outcome="ok",
        details={"platform": platform.lower(), "account_name": payload.account_name},
    )

    return {
        "connected": True,
        "account_id": acc.id,
        "platform": acc.platform,
        "account_name": acc.account_name,
        "token_encrypted_at_rest": True,
    }


@router.post("/{platform}/webhook")
async def verify_platform_webhook(
    platform: str,
    request: Request,
    x_aisma_signature: str | None = Header(None, alias="X-AISMA-Signature"),
) -> dict[str, Any]:
    raw_body = await request.body()
    if not x_aisma_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-AISMA-Signature HMAC header",
        )

    expected_sig = hmac.new(
        _WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(x_aisma_signature.replace("sha256=", ""), expected_sig):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook HMAC-SHA256 signature",
        )

    return {
        "received": True,
        "platform": platform.lower(),
        "signature_verified": True,
    }


@router.post("/{platform}/publish")
def publish_to_platform(
    platform: str,
    payload: DirectPublishRequest,
    business_id: str = Depends(require_tenant_access),
) -> dict[str, Any]:
    adapters = _get_adapters()
    adapter = adapters.get(platform.lower())
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Unsupported platform '{platform}'")

    pub_payload = PublishPayload(
        content=payload.content,
        channel=platform,
        media_urls=payload.media_urls,
    )
    result = adapter.publish(pub_payload)
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return result.model_dump()


@router.get("/{platform}/analytics")
def get_platform_analytics(
    platform: str,
    days: int = 30,
    business_id: str = Depends(require_tenant_access),
) -> dict[str, Any]:
    adapters = _get_adapters()
    adapter = adapters.get(platform.lower())
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Unsupported platform '{platform}'")
    analytics = adapter.fetch_analytics(days=days)
    return analytics.model_dump()
