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

