from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from models import AuditLog
from utils.datetime_utils import utcnow as _utcnow

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
        audit = AuditLog(
            event_type="fraud_alert",
            actor_id=None,
            action=alert_type,
            resource_type="security",
            details=data,
            severity=priority,
            occurred_at=_utcnow(),
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

