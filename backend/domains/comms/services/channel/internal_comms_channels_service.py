"""Auto-migrated service logic from routers/internal_comms_channels.py."""
from __future__ import annotations

import logging

from typing import List, Optional

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.comms.services.channel.internal_communication import get_internal_communication_service

logger = logging.getLogger("zozi.api.internal")


def list_channels(user_id: int, country_code: Optional[str], db: Session):
    """List internal comms channels visible to the user."""
    service = get_internal_communication_service(db)
    return service.list_channels(user_id, country_code)


def get_channel(channel_id: str, db: Session):
    """Fetch a single channel by id."""
    service = get_internal_communication_service(db)
    result = service.get_channel(channel_id)
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found")
    return result


def add_member(channel_id: str, user_id: int, role: str, db: Session):
    """Add a member to a channel."""
    service = get_internal_communication_service(db)
    return service.add_member(channel_id, user_id, role)


def remove_member(channel_id: str, user_id: int, db: Session):
    """Remove a member from a channel."""
    service = get_internal_communication_service(db)
    return service.remove_member(channel_id, user_id)


def send_message(channel_id: str, sender_id: int, content: str, message_type: str, db: Session):
    """Send a message to a channel."""
    service = get_internal_communication_service(db)
    return service.send_message(channel_id, sender_id, content, message_type)


def get_messages(channel_id: str, limit: int, offset: int, db: Session):
    """Fetch messages for a channel with pagination."""
    service = get_internal_communication_service(db)
    return service.get_messages(channel_id, limit, offset)
