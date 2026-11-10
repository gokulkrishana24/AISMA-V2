from __future__ import annotations

import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, require_tenant_access
from db.models import Business, Membership, OrganizationInvite, User

router = APIRouter(prefix="/api/v1/organizations", tags=["Multi-Tenant Workspace & Organization Management"])


class CreateOrgPayload(BaseModel):
    name: str
    industry: str = "Technology"


class InviteMemberPayload(BaseModel):
    email: EmailStr
    role: str = "operator"  # admin, operator, viewer


@router.get("")
def list_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    memberships = db.query(Membership).filter(Membership.user_id == current_user.id).all()
    results = []
    for m in memberships:
        biz = db.query(Business).filter(Business.id == m.business_id).first()
        if biz:
            results.append(
                {
                    "id": biz.id,
                    "name": biz.name,
                    "slug": biz.slug,
                    "industry": biz.industry,
                    "user_role": m.role,
                }
            )
    return results


@router.post("")
def create_organization(
    payload: CreateOrgPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    biz_id = f"biz_{uuid.uuid4().hex[:12]}"
    biz_slug = payload.name.lower().replace(" ", "-")[:40]
    biz = Business(id=biz_id, name=payload.name, slug=biz_slug, industry=payload.industry)
    db.add(biz)
    db.flush()

    membership = Membership(id=f"mem_{uuid.uuid4().hex[:12]}", user_id=current_user.id, business_id=biz.id, role="admin")
    db.add(membership)
    db.commit()

    return {
        "id": biz.id,
        "name": biz.name,
        "slug": biz.slug,
        "role": "admin",
    }


@router.get("/current/members")
def list_organization_members(
    business_id: str = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    memberships = db.query(Membership).filter(Membership.business_id == business_id).all()
    results = []
    for m in memberships:
        u = db.query(User).filter(User.id == m.user_id).first()
        if u:
            results.append(
                {
                    "membership_id": m.id,
                    "user_id": u.id,
                    "name": u.full_name,
                    "email": u.email,
                    "role": m.role,
                    "joined_at": m.created_at.isoformat(),
                }
            )
    return results


@router.post("/current/invites")
def invite_member(
    payload: InviteMemberPayload,
    business_id: str = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    invite_token = uuid.uuid4().hex
    invite = OrganizationInvite(
        id=f"inv_{uuid.uuid4().hex[:12]}",
        business_id=business_id,
        email=payload.email.lower(),
        role=payload.role,
        token=invite_token,
        status="pending",
        expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=7),
    )
    db.add(invite)
    db.commit()

    return {
        "invite_id": invite.id,
        "email": invite.email,
        "role": invite.role,
        "status": "pending",
        "invite_url": f"https://aisma.app/invite/{invite_token}",
        "expires_at": invite.expires_at.isoformat(),
    }

