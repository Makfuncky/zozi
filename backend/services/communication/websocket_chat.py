"""
WebSocket Real-Time Chat Service
Features: Entity-scoped rooms, live messaging, typing indicators, read receipts
"""
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from collections import defaultdict

from sqlalchemy.orm import Session

from data.models_core import (
    EntityChatThread, EntityChatMessage, DirectChatRoom, DirectChatMessage,
    GroupChatRoom, GroupChatMember,
)
from data.db import get_service_session
from data.services_write_helpers import add_and_flush, commit_and_refresh, commit_only

logger = logging.getLogger("zozi.websocket_chat")


def create_direct_message(
    db: Session,
    room_id: str,
    sender_id: int,
    content: str,
    msg_type: str = "text"
) -> Tuple[Optional[int], Optional[str]]:
    """Create a direct message and return (id, created_at_iso) or (None, None)."""
    room = db.query(DirectChatRoom).filter(DirectChatRoom.chat_id == room_id).first()
    if not room:
        return None, None
    msg = DirectChatMessage(room_id=room.id, sender_id=sender_id, message=content, message_type=msg_type)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg.id, msg.created_at.isoformat()


def create_group_message(
    db: Session,
    room_id: str,
    sender_id: int,
    content: str,
    msg_type: str = "text"
) -> Tuple[Optional[int], Optional[str]]:
    """Create a group message and return (id, created_at_iso) or (None, None)."""
    room = db.query(GroupChatRoom).filter(GroupChatRoom.chat_id == room_id).first()
    if not room:
        return None, None
    msg = GroupChatMessage(room_id=room.id, sender_id=sender_id, message=content, message_type=msg_type)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg.id, msg.created_at.isoformat()


def create_entity_message(
    db: Session,
    thread_id: int,
    sender_id: int,
    content: str,
    msg_type: str = "text"
) -> Tuple[Optional[int], Optional[str]]:
    """Create an entity message and return (id, created_at_iso) or (None, None)."""
    thread = db.query(EntityChatThread).filter(EntityChatThread.id == thread_id).first()
    if not thread:
        return None, None
    msg = EntityChatMessage(thread_id=thread.id, sender_id=sender_id, message=content, message_type=msg_type)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg.id, msg.created_at.isoformat()


def commit_read_receipts(db: Session, messages: list) -> int:
    """Commit read_at timestamps on messages."""
    if messages:
        db.commit()
    return len(messages)


class WebSocketChatService:
    """Real-time chat service with WebSocket support."""
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
        self._typing_indicators: Dict[str, Dict[int, datetime]] = defaultdict(dict)
        self._room_participants: Dict[str, set] = defaultdict(set)
    
    def get_or_create_room(
        self,
        entity_type: str,
        entity_id: int,
        participants: List[int] = None
    ) -> EntityChatThread:
        """Get or create a chat room for an entity."""
        thread = self.db.query(EntityChatThread).filter(
            EntityChatThread.entity_type == entity_type,
            EntityChatThread.entity_id == entity_id
        ).first()
        
        if not thread:
            thread = EntityChatThread(
                entity_type=entity_type,
                entity_id=entity_id,
                title=f"{entity_type}:{entity_id} Chat"
            )
            self.db.add(thread)
            self.db.commit()
            self.db.refresh(thread)
        
        if participants:
            self._room_participants[f"{entity_type}:{entity_id}"] = set(participants)
        
        return thread
    
    def add_message(
        self,
        entity_type: str,
        entity_id: int,
        sender_id: int,
        message: str,
        message_type: str = "text"
    ) -> EntityChatMessage:
        """Add a message to an entity chat room."""
        thread = self.get_or_create_room(entity_type, entity_id)
        
        msg = EntityChatMessage(
            thread_id=thread.id,
            sender_id=sender_id,
            message=message
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        
        return msg
    
    def set_typing_indicator(
        self,
        entity_type: str,
        entity_id: int,
        user_id: int,
        is_typing: bool
    ):
        """Set typing indicator for a user in a room."""
        room_key = f"{entity_type}:{entity_id}"
        if is_typing:
            self._typing_indicators[room_key][user_id] = datetime.now(timezone.utc)
        else:
            self._typing_indicators[room_key].pop(user_id, None)
    
    def get_typing_users(self, entity_type: str, entity_id: int) -> List[int]:
        """Get users currently typing in a room."""
        room_key = f"{entity_type}:{entity_id}"
        return list(self._typing_indicators[room_key].keys())
    
    def mark_as_read(
        self,
        thread_id: int,
        user_id: int
    ) -> bool:
        """Mark messages as read (placeholder)."""
        return True
    
    def get_recent_messages(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent messages for a room."""
        thread = self.db.query(EntityChatThread).filter(
            EntityChatThread.entity_type == entity_type,
            EntityChatThread.entity_id == entity_id
        ).first()
        
        if not thread:
            return []
        
        messages = self.db.query(EntityChatMessage).filter(
            EntityChatMessage.thread_id == thread.id
        ).order_by(EntityChatMessage.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "message": m.message,
                "created_at": m.created_at.isoformat()
            }
            for m in reversed(messages)
        ]


def persist_direct_message(db: Session, room_id: str, sender_id: int, content: str, msg_type: str = "text") -> tuple[Optional[int], Optional[str]]:
    """Store a direct message in the database."""
    room = db.query(DirectChatRoom).filter(DirectChatRoom.chat_id == room_id).first()
    if not room:
        return None, None
    msg = DirectChatMessage(room_id=room.id, sender_id=sender_id, message=content, message_type=msg_type)
    add_and_flush(db, msg)
    commit_and_refresh(db, msg)
    return msg.id, msg.created_at.isoformat()


def persist_group_message(db: Session, room_id: str, sender_id: int, content: str, msg_type: str = "text") -> tuple[Optional[int], Optional[str]]:
    """Store a group message in the database."""
    room = db.query(GroupChatRoom).filter(GroupChatRoom.chat_id == room_id).first()
    if not room:
        return None, None
    msg = GroupChatMessage(room_id=room.id, sender_id=sender_id, message=content, message_type=msg_type)
    add_and_flush(db, msg)
    commit_and_refresh(db, msg)
    return msg.id, msg.created_at.isoformat()


def persist_entity_message(db: Session, thread_id: int, sender_id: int, content: str, msg_type: str = "text") -> tuple[Optional[int], Optional[str]]:
    """Store an entity chat message in the database."""
    thread = db.query(EntityChatThread).filter(EntityChatThread.id == thread_id).first()
    if not thread:
        return None, None
    msg = EntityChatMessage(thread_id=thread.id, sender_id=sender_id, message=content, message_type=msg_type)
    add_and_flush(db, msg)
    commit_and_refresh(db, msg)
    return msg.id, msg.created_at.isoformat()


def commit_read_receipts_messages(db: Session, messages: list) -> int:
    """Commit read_at timestamps on messages."""
    count = 0
    now = datetime.now(timezone.utc)
    for m in messages:
        m.read_at = now
        count += 1
    commit_only(db)
    return count


def get_websocket_chat_service(db: Session = None) -> WebSocketChatService:
    return WebSocketChatService(db or get_service_session())
