from __future__ import annotations
import logging
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from infrastructure.utils.datetime_utils import utcnow as utcnow
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Fraud alerting and notification service.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def send_alert(
        self,
        alert_type: str,
        data: Dict[str, Any],
        priority: str = "medium",
    ) -> dict:
        """Send an alert to the fraud monitoring dashboard."""
        # Lazy import to avoid circular dependency
        from domains.governance.ports import AuditLog
        audit = AuditLog(
            event_type="fraud_alert",
            actor_id=None,
            action=alert_type,
            resource_type="security",
            details=data,
            severity=priority,
            occurred_at=utcnow(),
        )
        self.db.add(audit)
        self.db.commit()
        
        return {"status": "alert_sent", "type": alert_type, "priority": priority}
    
    def escalate_to_human(self, alert: dict) -> None:
        """Escalate high-priority alerts to security team."""
        if alert.get("priority") in ("high", "critical"):
            logger.warning(f"Security escalation: {alert}")
    
    def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        type: str = "info",
        priority: str = "medium"
    ) -> dict:
        """Send a notification to a user (wrapper for send_alert)."""
        return self.send_alert(
            alert_type=type,
            data={
                "user_id": user_id,
                "title": title,
                "message": message
            },
            priority=priority
        )
    
    def send_fulfillment_issues_notification(
        self,
        user_id: int,
        order_id: int,
        payment_id: int,
        issues: list[str]
    ) -> dict:
        """Send notification about fulfillment issues."""
        return self.send_notification(
            user_id=user_id,
            title="Order Fulfillment Issue",
            message=f"Order #{order_id} has fulfillment issues: {'; '.join(issues)}",
            type="fulfillment_issue",
            priority="high"
        )
    
    def send_fulfillment_success_notification(
        self,
        user_id: int,
        order_id: int,
        payment_id: int,
        amount: float
    ) -> dict:
        """Send notification about successful fulfillment."""
        return self.send_notification(
            user_id=user_id,
            title="Order Confirmed",
            message=f"Your order #{order_id} for ${amount} has been confirmed and is being processed.",
            type="fulfillment_success",
            priority="medium"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Standalone service functions
# ─────────────────────────────────────────────────────────────────────────────

def create_notification_service(db=None):
    """Factory function to create a NotificationService instance."""
    if db is None:
        from infrastructure.database.database import get_db
        db = next(get_db())
    return NotificationService(db)


def get_user_notifications(user_id, limit=50):
    """Get notifications for a user."""
    from domains.comms.models.communication import Notification
    from infrastructure.database.database import get_db
    db = next(get_db())
    return db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).limit(limit).all()


def mark_notification_read(notification_id):
    """Mark a notification as read."""
    from domains.comms.models.communication import Notification
    from infrastructure.database.database import get_db
    db = next(get_db())
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.is_read = True
        notification.read_at = utcnow()
        db.commit()
        return True
    return False


def mark_all_notifications_read(user_id):
    """Mark all notifications as read for a user."""
    from domains.comms.models.communication import Notification
    from infrastructure.database.database import get_db
    db = next(get_db())
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True, "read_at": utcnow()})
    db.commit()


def delete_notification(notification_id):
    """Delete a notification."""
    from domains.comms.models.communication import Notification
    from infrastructure.database.database import get_db
    db = next(get_db())
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        db.delete(notification)
        db.commit()
        return True
    return False


def get_unread_count(user_id):
    """Get unread notification count for a user."""
    from domains.comms.models.communication import Notification
    from infrastructure.database.database import get_db
    db = next(get_db())
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()

