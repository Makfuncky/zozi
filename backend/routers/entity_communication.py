"""
Entity Communication Router
Links emails, chats, and calls to business entities
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import EntityChatThread, EntityChatMessage, User
from services.entity_chat_service import get_chat_service, EntityChatService
from services.email_gateway import EmailGateway, get_email_gateway
from db.database import get_db
from controllers.auth_controller import get_current_user

router = APIRouter()


@router.get("/threads/{entity_type}/{entity_id}", response_model=dict)
async def get_entity_thread(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat_service = get_chat_service(db)
    thread = chat_service.get_entity_thread(entity_type, entity_id)
    if not thread:
        thread = chat_service.create_or_get_thread(entity_type, entity_id)
    return thread


@router.post("/threads/{thread_id}/messages", response_model=dict)
async def send_thread_message(
    thread_id: int,
    message: str,
    sender_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat_service = get_chat_service(db)
    msg = chat_service.send_message(thread_id, sender_id, message)
    return {
        "id": msg.id,
        "thread_id": msg.thread_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at.isoformat()
    }


@router.get("/threads/{thread_id}/messages", response_model=List[dict])
async def get_thread_messages(
    thread_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat_service = get_chat_service(db)
    return chat_service.get_thread_messages(thread_id, limit, offset)


@router.post("/email/send", response_model=dict)
async def send_entity_email(
    entity_type: str,
    entity_id: int,
    to_email: str,
    subject: str,
    body: str,
    sender_id: int,
    template_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    email_gateway = get_email_gateway(db)
    result = email_gateway.send_external_email(
        to_email=to_email,
        subject=subject,
        body=body,
        sender_id=sender_id,
        template_id=template_id
    )
    return result
