"""
Notification Engine 2.0 - Multi-channel notification system with templates and localization.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session

from models import Notification, SystemSetting


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationEngine:
    """Multi-channel notification system with templates and scheduling."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def send(
        self,
        user_id: int,
        title: str,
        message: str,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        template: str = None,
        variables: Dict[str, Any] = None,
        scheduled_at: datetime = None,
    ) -> Dict[str, Any]:
        """Send a notification through specified channel."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            channel=channel.value,
            priority=priority.value,
            template=template,
            variables=variables or {},
            scheduled_at=scheduled_at,
            status="pending",
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        return {
            "notification_id": notification.id,
            "status": "queued",
            "channel": channel.value,
        }
    
    def send_bulk(
        self,
        user_ids: List[int],
        title: str,
        message: str,
        channel: NotificationChannel = NotificationChannel.EMAIL,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
    ) -> Dict[str, Any]:
        """Send notifications to multiple users."""
        sent = []
        for user_id in user_ids:
            result = self.send(user_id, title, message, channel, priority)
            sent.append(result)
        return {"sent_count": len(sent), "notifications": sent}
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for a user."""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
        
        return [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "channel": n.channel,
                "priority": n.priority,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "read_at": n.read_at.isoformat() if n.read_at else None,
            }
            for n in notifications
        ]
    
    def mark_read(self, notification_id: int, user_id: int) -> Dict[str, Any]:
        """Mark a notification as read."""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        ).first()
        
        if not notification:
            return {"error": "Notification not found"}
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        self.db.commit()
        return {"status": "marked_read"}
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a notification template."""
        setting = self.db.query(SystemSetting).filter(
            SystemSetting.key == f"notification_template_{template_name}"
        ).first()
        if setting:
            import json
            return json.loads(setting.value)
        return None
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render a template with variables."""
        template = self.get_template(template_name)
        if not template:
            return {"title": "", "message": ""}
        
        title = template.get("title", "").format(**variables)
        message = template.get("message", "").format(**variables)
        return {"title": title, "message": message}


def get_notification_engine(db: Session) -> NotificationEngine:
    return NotificationEngine(db)
