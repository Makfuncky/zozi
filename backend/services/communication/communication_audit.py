
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from models.communication import CommunicationAuditTrail

logger = logging.getLogger("zozi.communication_audit")


class CommunicationAuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        action: str,
        channel: str,
        content_preview: Optional[str] = None,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> dict:
        audit = CommunicationAuditTrail(
            action=action,
            channel=channel,
            content_preview=content_preview,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata_json or {},
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)

        return {
            "id": audit.id,
            "action": audit.action,
            "channel": audit.channel,
            "content_preview": audit.content_preview,
            "user_id": user_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metadata_json": audit.metadata_json,
            "created_at": audit.created_at.isoformat() if audit.created_at else None,
        }

    def get_audit_trail(
        self,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        query = self.db.query(CommunicationAuditTrail)

        if user_id is not None:
            query = query.filter(CommunicationAuditTrail.user_id == user_id)
        if entity_type is not None:
            query = query.filter(CommunicationAuditTrail.entity_type == entity_type)
        if entity_id is not None:
            query = query.filter(CommunicationAuditTrail.entity_id == entity_id)
        if action is not None:
            query = query.filter(CommunicationAuditTrail.action == action)

        audits = query.order_by(CommunicationAuditTrail.created_at.desc()).offset(offset).limit(limit).all()

        return [
            {
                "id": a.id,
                "action": a.action,
                "channel": a.channel,
                "content_preview": a.content_preview,
                "user_id": a.user_id,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "metadata_json": a.metadata_json,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in audits
        ]


    def export_for_ediscovery(
        self,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[dict]:
        query = self.db.query(CommunicationAuditTrail)

        if user_id is not None:
            query = query.filter(CommunicationAuditTrail.user_id == user_id)
        if date_from is not None:
            query = query.filter(CommunicationAuditTrail.created_at >= date_from)
        if date_to is not None:
            query = query.filter(CommunicationAuditTrail.created_at <= date_to)

        audits = query.order_by(CommunicationAuditTrail.created_at.asc()).all()

        return [
            {
                "id": a.id,
                "action": a.action,
                "channel": a.channel,
                "content_preview": a.content_preview,
                "user_id": a.user_id,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "metadata_json": a.metadata_json,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in audits
        ]


def get_communication_audit_service(db: Session) -> CommunicationAuditService:
    return CommunicationAuditService(db)
