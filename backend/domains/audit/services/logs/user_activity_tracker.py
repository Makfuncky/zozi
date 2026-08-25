"""
User Activity Tracker Service
Tracks user sessions, actions, and activity patterns for cross-domain audit.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.audit.models.audit_schema_models import AuditLog

logger = logging.getLogger(__name__)


class UserActivityTracker:
    """Tracks and analyzes user activity across domains."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_activity(
        self,
        user_id: int,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get activity history for a specific user."""
        query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        rows = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

        return [
            {
                "id": r.id,
                "action": r.action,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "details": r.details,
                "ip_address": r.ip_address,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    def get_user_activity_summary(
        self,
        user_id: int,
        *,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get aggregated activity summary for a user over the last N days."""
        since = datetime.utcnow() - timedelta(days=days)

        total_actions = (
            self.db.query(func.count(AuditLog.id))
            .filter(AuditLog.user_id == user_id, AuditLog.created_at >= since)
            .scalar()
            or 0
        )

        action_counts = (
            self.db.query(AuditLog.action, func.count(AuditLog.id))
            .filter(AuditLog.user_id == user_id, AuditLog.created_at >= since)
            .group_by(AuditLog.action)
            .order_by(func.count(AuditLog.id).desc())
            .limit(20)
            .all()
        )

        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": total_actions,
            "top_actions": [{"action": a, "count": c} for a, c in action_counts],
        }

    def get_active_users(
        self,
        *,
        days: int = 7,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get most active users in the last N days."""
        since = datetime.utcnow() - timedelta(days=days)

        rows = (
            self.db.query(
                AuditLog.user_id,
                func.count(AuditLog.id).label("action_count"),
            )
            .filter(AuditLog.created_at >= since, AuditLog.user_id.isnot(None))
            .group_by(AuditLog.user_id)
            .order_by(func.count(AuditLog.id).desc())
            .limit(limit)
            .all()
        )

        return [
            {"user_id": r.user_id, "action_count": r.action_count, "period_days": days}
            for r in rows
        ]

    def get_action_trail(
        self,
        entity_type: str,
        entity_id: int,
        *,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Get the full action trail for a specific entity."""
        rows = (
            self.db.query(AuditLog)
            .filter(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.created_at.asc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": r.id,
                "action": r.action,
                "user_id": r.user_id,
                "username": r.username,
                "details": r.details,
                "ip_address": r.ip_address,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]


def get_user_activity_tracker(db: Session) -> UserActivityTracker:
    return UserActivityTracker(db)
