"""
Entity-Linked Messaging System for internal communications.

Allows linking messages to specific entities like orders, suppliers, tickets, or payouts.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from db.database import get_db
from models import Message, ShiftHandoverLog


class MessagingService:
    """Service for entity-linked messaging operations."""
    
    @staticmethod
    def create_message(
        country_code: str,
        from_user_id: int,
        to_user_id: int,
        subject: str,
        body: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        priority: str = "normal",
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new entity-linked message."""
        with get_db() as db:
            msg = Message(
                country_code=country_code,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                subject=subject,
                body=body,
                entity_type=entity_type,
                entity_id=entity_id,
                priority=priority,
                category=category,
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return {
                "id": msg.id,
                "subject": msg.subject,
                "status": msg.status,
                "created_at": msg.created_at.isoformat(),
            }
    
    @staticmethod
    def get_messages_for_user(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get messages for a specific user."""
        with get_db() as db:
            messages = db.query(Message).filter(
                Message.to_user_id == user_id,
                Message.status != "archived"
            ).order_by(Message.created_at.desc()).limit(limit).offset(offset).all()
            
            return [
                {
                    "id": m.id,
                    "subject": m.subject,
                    "body": m.body,
                    "priority": m.priority,
                    "category": m.category,
                    "entity_type": m.entity_type,
                    "entity_id": m.entity_id,
                    "status": m.status,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ]
    
    @staticmethod
    def mark_as_read(message_id: int, user_id: int) -> bool:
        """Mark a message as read."""
        with get_db() as db:
            msg = db.query(Message).filter(
                Message.id == message_id,
                Message.to_user_id == user_id
            ).first()
            
            if msg:
                msg.status = "read"
                msg.read_at = datetime.utcnow()
                db.commit()
                return True
            return False
    
    @staticmethod
    def create_shift_handover(
        user_id: int,
        country_code: str,
        shift_date: datetime,
        shift_type: str,
        handover_notes: str,
        pending_tickets: List[int],
        unresolved_approvals: List[int],
    ) -> Dict[str, Any]:
        """Create a shift handover log."""
        import json
        
        with get_db() as db:
            handover = ShiftHandoverLog(
                user_id=user_id,
                country_code=country_code,
                shift_date=shift_date,
                shift_type=shift_type,
                handover_notes=handover_notes,
                pending_tickets=json.dumps(pending_tickets),
                unresolved_approvals=json.dumps(unresolved_approvals),
            )
            db.add(handover)
            db.commit()
            db.refresh(handover)
            return {"id": handover.id, "status": handover.status}
