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
        event_type: str,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        audit = CommunicationAuditTrail(
            event_type=event_type,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)

        return {
            "id": audit.id,
            "event_type": event_type,
            "user_id": user_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metadata": audit.metadata,
            "ip_address": ip_address,
            "timestamp": audit.timestamp.isoformat() if audit.timestamp else None,
        }

    def get_audit_trail(
        self,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        event_type: Optional[str] = None,
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
        if event_type is not None:
            query = query.filter(CommunicationAuditTrail.event_type == event_type)

        audits = query.order_by(CommunicationAuditTrail.timestamp.desc()).offset(offset).limit(limit).all()

        return [
            {
                "id": a.id,
                "event_type": a.event_type,
                "user_id": a.user_id,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "metadata": a.metadata,
                "ip_address": a.ip_address,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
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
            query = query.filter(CommunicationAuditTrail.timestamp >= date_from)
        if date_to is not None:
            query = query.filter(CommunicationAuditTrail.timestamp <= date_to)

        audits = query.order_by(CommunicationAuditTrail.timestamp.asc()).all()

        return [
            {
                "id": a.id,
                "event_type": a.event_type,
                "user_id": a.user_id,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "metadata": a.metadata,
                "ip_address": a.ip_address,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            }
            for a in audits
        ]


def get_communication_audit_service(db: Session) -> CommunicationAuditService:
    return CommunicationAuditService(db)
