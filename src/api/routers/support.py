from __future__ import annotations

import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, require_tenant_access
from db.models import SupportTicket, User

router = APIRouter(prefix="/api/v1/support", tags=["Customer Support & Help Center"])


class CreateTicketPayload(BaseModel):
    subject: str
    description: str
    priority: str = "medium"  # low, medium, high, urgent


@router.get("/tickets")
def list_tickets(
    business_id: str = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    tickets = db.query(SupportTicket).filter(SupportTicket.business_id == business_id).order_by(SupportTicket.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "subject": t.subject,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
        }
        for t in tickets
    ]


@router.post("/tickets")
def open_support_ticket(
    payload: CreateTicketPayload,
    business_id: str = Depends(require_tenant_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ticket = SupportTicket(
        id=f"tkt_{uuid.uuid4().hex[:10]}",
        business_id=business_id,
        user_id=current_user.id,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        status="open",
        created_at=datetime.datetime.now(datetime.UTC),
    )
    db.add(ticket)
    db.commit()

    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "priority": ticket.priority,
        "status": "open",
        "message": "Support ticket created. An engineer will respond within SLA.",
    }

