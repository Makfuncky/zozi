"""Service methods for entity chat data access."""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from data.models_core import EntityChatThread, EntityChatMessage


class EntityChatService:
    """Service for managing entity-attached chat threads and messages."""

    def __init__(self, db: Session = None):
        from data.db import get_service_session
        self.db = db or get_service_session()

    def create_or_get_thread(
        self, entity_type: str, entity_id: int, title: Optional[str] = None
    ) -> EntityChatThread:
        """Create or retrieve a chat thread for an entity."""
        thread = (
            self.db.query(EntityChatThread)
            .filter(
                EntityChatThread.entity_type == entity_type,
                EntityChatThread.entity_id == entity_id,
            )
            .first()
        )
        if thread:
            return thread
        thread = EntityChatThread(
            entity_type=entity_type,
            entity_id=entity_id,
            title=title or f"{entity_type}:{entity_id} Chat",
        )
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)
        return thread

    def send_message(self, thread_id: int, sender_id: int, message: str) -> EntityChatMessage:
        """Send a message in a chat thread."""
        msg = EntityChatMessage(thread_id=thread_id, sender_id=sender_id, message=message)
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_thread_messages(
        self, thread_id: int, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a thread, newest first, returned chronological."""
        messages = (
            self.db.query(EntityChatMessage)
            .filter(EntityChatMessage.thread_id == thread_id)
            .order_by(EntityChatMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "message": m.message,
                "created_at": m.created_at.isoformat(),
            }
            for m in reversed(messages)
        ]

    def get_entity_thread(self, entity_type: str, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get thread details for an entity."""
        thread = (
            self.db.query(EntityChatThread)
            .filter(
                EntityChatThread.entity_type == entity_type,
                EntityChatThread.entity_id == entity_id,
            )
            .first()
        )
        if not thread:
            return None
        return {
            "id": thread.id,
            "entity_type": thread.entity_type,
            "entity_id": thread.entity_id,
            "title": thread.title,
            "is_active": getattr(thread, "is_active", True),
            "message_count": len(thread.messages),
        }


def get_chat_service(db: Session = None) -> EntityChatService:
    """Factory returning an EntityChatService instance."""
    return EntityChatService(db)


def get_entity_threads(db: Session, entity_type: str, entity_id: int) -> list[EntityChatThread]:
    """Get chat threads for an entity."""
    return (
        db.query(EntityChatThread)
        .filter(
            EntityChatThread.entity_type == entity_type,
            EntityChatThread.entity_id == entity_id,
        )
        .all()
    )


def get_entity_thread_by_id(db: Session, thread_id: int) -> EntityChatThread | None:
    """Get an entity chat thread by ID."""
    return db.query(EntityChatThread).filter(EntityChatThread.id == thread_id).first()


def get_entity_thread_messages(db: Session, thread_id: int) -> list[EntityChatMessage]:
    """Get messages for an entity chat thread."""
    return (
        db.query(EntityChatMessage)
        .filter(EntityChatMessage.thread_id == thread_id)
        .order_by(EntityChatMessage.created_at)
        .all()
    )


def get_entity_participants(db: Session, thread_id: int) -> list:
    """Get participants for an entity thread."""
    thread = get_entity_thread_by_id(db, thread_id)
    if not thread:
        return []
    return []
