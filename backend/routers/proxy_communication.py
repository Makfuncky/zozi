"""
Proxy Communication Channels API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from data.models import ProxyChannel, ProxySession, ProxyMessage, User
from services.proxy_communication import get_proxy_service, ProxyCommunicationService
from data.db import get_db
from data.dependencies_auth import get_current_user
from data.controllers_admin_controller import require_admin

router = APIRouter()


@router.post("/channels", response_model=dict)
async def create_proxy_channel(
    entity_type: str,
    entity_id: int,
    participant_ids: List[int],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    channel = proxy_service.create_proxy_channel(
        entity_type=entity_type,
        entity_id=entity_id,
        participant_ids=participant_ids
    )
    return {
        "id": channel.id,
        "proxy_phone": proxy_service.mask_phone_number(channel.proxy_phone) if channel.proxy_phone else None,
        "proxy_email": channel.proxy_email,
        "is_active": channel.is_active
    }


@router.get("/channels/{channel_id}", response_model=dict)
async def get_proxy_channel(
    channel_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    channel = db.query(ProxyChannel).filter_by(id=channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Proxy channel not found")
    proxy_service = get_proxy_service(db)
    return {
        "id": channel.id,
        "entity_type": channel.entity_type,
        "entity_id": channel.entity_id,
        "proxy_phone": proxy_service.mask_phone_number(channel.proxy_phone) if channel.proxy_phone else None,
        "proxy_email": channel.proxy_email,
        "is_active": channel.is_active,
        "participants": channel.participants
    }


@router.post("/sessions", response_model=dict)
async def start_proxy_session(
    channel_id: int,
    participant_one_id: int,
    participant_two_id: int,
    metadata: Optional[dict] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    try:
        session = proxy_service.start_proxy_session(
            channel_id=channel_id,
            participant_one_id=participant_one_id,
            participant_two_id=participant_two_id,
            metadata=metadata
        )
        return {
            "id": session.id,
            "channel_id": session.channel_id,
            "started_at": session.started_at.isoformat(),
            "is_encrypted": session.is_encrypted
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/messages", response_model=dict)
async def send_proxy_message(
    session_id: int,
    sender_id: int,
    recipient_id: int,
    content: str,
    message_type: str = "text",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    message = proxy_service.send_proxy_message(
        session_id=session_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=content,
        message_type=message_type
    )
    return {
        "id": message.id,
        "session_id": message.session_id,
        "sender_id": message.sender_id,
        "created_at": message.created_at.isoformat()
    }


@router.post("/calls/initiate", response_model=dict)
async def initiate_call(
    channel_id: int,
    caller_id: int,
    callee_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    call_log = proxy_service.initiate_call(
        channel_id=channel_id,
        caller_id=caller_id,
        callee_id=callee_id
    )
    return {
        "call_id": call_log.id,
        "channel_id": call_log.channel_id,
        "direction": call_log.direction,
        "started_at": call_log.started_at.isoformat()
    }


@router.post("/calls/{call_id}/end", response_model=dict)
async def end_call(
    call_id: int,
    duration_seconds: int,
    recording_url: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    proxy_service.end_call(call_id, duration_seconds, recording_url)
    return {"status": "ended"}


@router.get("/users/{user_id}/channels", response_model=List[dict])
async def get_user_channels(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    channels = db.query(ProxyChannel).filter(
        ProxyChannel.participants.contains({"user_ids": [user_id]})
    ).offset(skip).limit(limit).all()
    proxy_service = get_proxy_service(db)
    return [
        {
            "id": c.id,
            "proxy_phone": proxy_service.mask_phone_number(c.proxy_phone) if c.proxy_phone else None,
            "proxy_email": c.proxy_email,
            "is_active": c.is_active
        }
        for c in channels
    ]


@router.get("/admin/channels", response_model=List[dict])
async def admin_list_channels(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    channels = db.query(ProxyChannel).offset(skip).limit(limit).all()
    proxy_service = get_proxy_service(db)
    return [
        {
            "id": c.id,
            "entity_type": c.entity_type,
            "entity_id": c.entity_id,
            "proxy_phone": c.proxy_phone,
            "proxy_email": c.proxy_email,
            "is_active": c.is_active
        }
        for c in channels
    ]
