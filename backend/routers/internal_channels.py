import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from data.db import get_db
from services.internal_communication import get_internal_communication_service

logger = logging.getLogger("zozi.api.internal")
router = APIRouter()


@router.post("/channels")
def create_channel(
    name: str = Body(..., embed=True),
    description: Optional[str] = Body(None, embed=True),
    is_public: bool = Body(False, embed=True),
    created_by: Optional[int] = Body(None, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    allowed_roles: Optional[List[str]] = Body(None, embed=True),
    entity_type: Optional[str] = Body(None, embed=True),
    entity_id: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db),
):
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


@router.get("/channels")
def list_channels(
    user_id: int = Query(...),
    country_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.list_channels(user_id, country_code)


@router.get("/channels/{channel_id}")
def get_channel(channel_id: str, db: Session = Depends(get_db)):
    service = get_internal_communication_service(db)
    result = service.get_channel(channel_id)
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found")
    return result


@router.post("/channels/{channel_id}/members")
def add_member(
    channel_id: str,
    user_id: int = Body(..., embed=True),
    role: str = Body("member", embed=True),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.add_member(channel_id, user_id, role)


@router.delete("/channels/{channel_id}/members/{user_id}")
def remove_member(channel_id: str, user_id: int, db: Session = Depends(get_db)):
    service = get_internal_communication_service(db)
    return service.remove_member(channel_id, user_id)


@router.post("/channels/{channel_id}/messages")
def send_message(
    channel_id: str,
    sender_id: int = Body(..., embed=True),
    content: str = Body(..., embed=True),
    message_type: str = Body("text", embed=True),
    is_masked: bool = Body(True, embed=True),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.send_message(channel_id, sender_id, content, message_type, is_masked)


@router.get("/channels/{channel_id}/messages")
def get_messages(
    channel_id: str,
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.get_messages(channel_id, limit, offset)
