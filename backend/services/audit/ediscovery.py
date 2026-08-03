"""
eDiscovery Service
Features: WORM-compliant audit trail, entity-based search, export
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from data.models import AuditLog
from data.models_core import DirectChatMessage, GroupChatMessage, EntityChatMessage, VideoRoom
from models.countries import CountryCommunication
from models.treasury.finance import JournalEntry
from data.db import get_service_session

logger = logging.getLogger("zozi.ediscovery")


class EDiscoveryService:
    """eDiscovery portal for compliance audits."""
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
    
    def search_audit_trail(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search immutable audit trail."""
        query = self.db.query(AuditLog)
        
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action.like(f"%{action}%"))
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        results = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "action": r.action,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "user_id": r.user_id,
                "username": r.username,
                "details": r.details,
                "ip_address": r.ip_address,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
    
    def get_entity_timeline(
        self,
        entity_type: str,
        entity_id: int
    ) -> List[Dict[str, Any]]:
        """Get complete timeline for an entity."""
        return self.search_audit_trail(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=500
        )
    
    def export_for_legal(
        self,
        entity_type: str,
        entity_id: int,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export audit trail for legal proceedings."""
        timeline = self.get_entity_timeline(entity_type, entity_id)
        
        return {
            "export_format": format,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "record_count": len(timeline),
            "records": timeline
        }

    # ── Communication Search (Chats, Emails, Meetings) ──────────────

    def search_communications(
        self,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Search across all communication channels for eDiscovery."""
        results = {"chats": [], "emails": [], "meetings": [], "journal_entries": []}

        # Direct/Group chat messages
        for model_cls, name in [(DirectChatMessage, "direct_chat"), (GroupChatMessage, "group_chat"), (EntityChatMessage, "entity_chat")]:
            q = self.db.query(model_cls)
            if user_id:
                q = q.filter(model_cls.sender_id == user_id)
            if keyword:
                q = q.filter(model_cls.message.ilike(f"%{keyword}%"))
            msgs = q.order_by(model_cls.created_at.desc()).limit(limit).all()
            for m in msgs:
                results["chats"].append({
                    "source": name,
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "content": getattr(m, "message", getattr(m, "content", "")),
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })

        # Country communications (internal emails)
        q = self.db.query(CountryCommunication)
        if user_id:
            q = q.filter((CountryCommunication.from_user_id == user_id) | (CountryCommunication.to_user_id == user_id))
        if entity_type and entity_id:
            q = q.filter(CountryCommunication.related_entity_type == entity_type, CountryCommunication.related_entity_id == entity_id)
        if keyword:
            q = q.filter(CountryCommunication.body.ilike(f"%{keyword}%"))
        comms = q.order_by(CountryCommunication.created_at.desc()).limit(limit).all()
        for c in comms:
            results["emails"].append({
                "id": c.id,
                "subject": c.subject,
                "body": c.body,
                "from_user_id": c.from_user_id,
                "to_user_id": c.to_user_id,
                "priority": c.priority,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })

        # Video meetings
        q = self.db.query(VideoRoom)
        if user_id:
            q = q.filter(VideoRoom.created_by == user_id)
        if keyword:
            q = q.filter(VideoRoom.name.ilike(f"%{keyword}%"))
        rooms = q.order_by(VideoRoom.created_at.desc()).limit(limit).all()
        for r in rooms:
            results["meetings"].append({
                "id": r.id,
                "room_id": r.room_id,
                "name": r.name,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        # Journal entries (financial communications)
        q = self.db.query(JournalEntry)
        if keyword:
            q = q.filter(JournalEntry.description.ilike(f"%{keyword}%"))
        entries = q.order_by(JournalEntry.entry_date.desc()).limit(limit).all()
        for e in entries:
            results["journal_entries"].append({
                "id": e.id,
                "reference_number": e.reference_number,
                "description": e.description,
                "source": e.source,
                "entry_date": e.entry_date.isoformat() if e.entry_date else None,
            })

        total = sum(len(v) for v in results.values())
        return {"total": total, "results": results}


def get_ediscovery_service(db: Session = None) -> EDiscoveryService:
    return EDiscoveryService(db or get_service_session())
