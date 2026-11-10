from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy.orm import Session

from db.models import Notification


class NotificationService:
    @staticmethod
    def send(
        db: Session,
        business_id: str,
        title: str,
        message: str,
        category: str = "system",
        user_id: str | None = None,
    ) -> Notification:
        notif = Notification(
            id=f"notif_{uuid.uuid4().hex[:12]}",
            business_id=business_id,
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            read=False,
            created_at=datetime.datetime.now(datetime.UTC),
        )
        db.add(notif)
        db.commit()
        return notif

    @staticmethod
    def list_notifications(
        db: Session,
        business_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query = db.query(Notification).filter(Notification.business_id == business_id)
        if unread_only:
            query = query.filter(Notification.read == False)  # noqa: E712
        items = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return [
            {
                "id": n.id,
                "business_id": n.business_id,
                "title": n.title,
                "message": n.message,
                "category": n.category,
                "read": n.read,
                "created_at": n.created_at.isoformat(),
            }
            for n in items
        ]

    @staticmethod
    def mark_read(db: Session, business_id: str, notification_id: str) -> bool:
        notif = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.business_id == business_id)
            .first()
        )
        if notif:
            notif.read = True
            db.commit()
            return True
        return False

