"""Auto-migrated service logic from routers/internal_channels.py."""
from __future__ import annotations

import logging

from typing import List, Optional

from fastapi import Body, Depends, HTTPException, Query

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.comms.services.internal_communication import get_internal_communication_service

logger = logging.getLogger("zozi.api.internal")

def create_channel(name: str, description: Optional[str], is_public: bool, created_by: Optional[int], country_code: Optional[str], allowed_roles: Optional[List[str]], entity_type: Optional[str], entity_id: Optional[int], db: Session):
    service = get_internal_communication_service(db)
    return service.create_channel(
        name=name,
        description=description,
        is_public=is_public,
        created_by=created_by,
        country_code=country_code,
        allowed_roles=allowed_roles,
        entity_type=entity_type,
        entity_id=entity_id,
    )

def list_channels(user_id: int, country_code: Optional[str], db: Session):
    service = get_internal_communication_service(db)
    return service.list_channels(user_id, country_code)

def get_channel(channel_id: str, db: Session):
    service = get_internal_communication_service(db)
    result = service.get_channel(channel_id)
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found")
    return result

def add_member(channel_id: str, user_id: int, role: str, db: Session):
    service = get_internal_communication_service(db)
    return service.add_member(channel_id, user_id, role)

def remove_member(channel_id: str, user_id: int, db: Session):
    service = get_internal_communication_service(db)
    return service.remove_member(channel_id, user_id)

def send_message(channel_id: str, sender_id: int, content: str, message_type: str, is_masked: bool, db: Session):
    service = get_internal_communication_service(db)
    return service.send_message(channel_id, sender_id, content, message_type, is_masked)

def get_messages(channel_id: str, limit: int, offset: int, db: Session):
    service = get_internal_communication_service(db)
    return service.get_messages(channel_id, limit, offset)

