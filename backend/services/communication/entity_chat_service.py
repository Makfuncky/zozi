"""
Entity-Attached Contextual Chat Service
Features: Context-aware threads, Entity-specific conversations
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from data.models import EntityChatThread, EntityChatMessage, User
from data.db import get_service_session

logger = logging.getLogger("zozi.chat")


class EntityChatService:
    """Service for managing entity-attached chat threads."""
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
    
    def create_or_get_thread(
        self,
        entity_type: str,
        entity_id: int,
        title: Optional[str] = None
    ) -> EntityChatThread:
        """Create or retrieve a chat thread for an entity."""
        thread = self.db.query(EntityChatThread).filter(
            EntityChatThread.entity_type == entity_type,
            EntityChatThread.entity_id == entity_id
        ).first()
        
        if thread:
            return thread
        
        thread = EntityChatThread(
            entity_type=entity_type,
            entity_id=entity_id,
            title=title or f"{entity_type}:{entity_id} Chat"
        )
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)
        return thread
    
    def send_message(
        self,
        thread_id: int,
        sender_id: int,
        message: str
    ) -> EntityChatMessage:
        """Send a message in a chat thread."""
        msg = EntityChatMessage(
            thread_id=thread_id,
            sender_id=sender_id,
            message=message
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg
    
    def get_thread_messages(
        self,
        thread_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a thread."""
        messages = self.db.query(EntityChatMessage).filter(
            EntityChatMessage.thread_id == thread_id
        ).order_by(EntityChatMessage.created_at.desc()).limit(limit).offset(offset).all()
        
        return [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "message": m.message,
                "created_at": m.created_at.isoformat()
            }
            for m in reversed(messages)
        ]
    
    def get_entity_thread(
        self,
        entity_type: str,
        entity_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get thread details for an entity."""
        thread = self.db.query(EntityChatThread).filter(
            EntityChatThread.entity_type == entity_type,
            EntityChatThread.entity_id == entity_id
        ).first()
        
        if not thread:
            return None
        
        return {
            "id": thread.id,
            "entity_type": thread.entity_type,
            "entity_id": thread.entity_id,
            "title": thread.title,
            "is_active": thread.is_active,
            "message_count": len(thread.messages)
        }


def get_chat_service(db: Session = None) -> EntityChatService:
    return EntityChatService(db or get_service_session())
