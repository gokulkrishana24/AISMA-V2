from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, require_tenant_access
from services.notifications import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["In-App Customer Notifications"])


@router.get("")
def list_notifications(
    unread_only: bool = False,
    business_id: str = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return NotificationService.list_notifications(db, business_id, unread_only=unread_only)


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    business_id: str = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ok = NotificationService.mark_read(db, business_id, notification_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"id": notification_id, "read": True}

