"""
Audit logging utility
Persists audit events to the audit_logs table.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session
import structlog

from models.core import AuditLog
from utils.logging_config import get_request_id

logger = structlog.get_logger(__name__)


class AuditAction(str):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PUBLISH = "publish"
    ROLLBACK = "rollback"
    APPROVE = "approve"
    REJECT = "reject"
    CREATE_DRAFT = "create_draft"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    VIEW = "view"


def audit_log(
    db: Session,
    actor_id: int,
    action: str,
    entity: str,
    entity_key: str,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> bool:
    try:
        entry = AuditLog(
            action=action,
            entity_type=entity,
            entity_id=int(entity_key) if entity_key and entity_key.isdigit() else None,
            user_id=actor_id if actor_id > 0 else None,
            username=details.get("username") if details else None,
            user_role=details.get("role") if details else None,
            details={
                "before": before,
                "after": after,
                "details": details,
                "request_id": get_request_id(),
            },
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()
        return True
    except Exception as exc:
        logger.error("audit_log_failed", action=action, entity=entity, error=str(exc))
        db.rollback()
        return False