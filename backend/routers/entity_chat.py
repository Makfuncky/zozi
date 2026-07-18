"""
Entity Chat API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import EntityChatThread, User
from services.entity_chat_service import get_chat_service, EntityChatService
from db.database import get_db
from controllers.auth_controller import get_current_user

router = APIRouter()


@router.post("/threads", response_model=dict)
async def create_thread(
    entity_type: str,
    entity_id: int,
    title: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_chat_service(db)
    thread = service.create_or_get_thread(entity_type, entity_id, title)
    return {
        "id": thread.id,
        "entity_type": thread.entity_type,
        "entity_id": thread.entity_id,
        "title": thread.title
    }


@router.post("/threads/{thread_id}/messages", response_model=dict)
async def send_message(
    thread_id: int,
    message: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == int(current_user["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    service = get_chat_service(db)
    msg = service.send_message(thread_id, user.id, message)
    return {
        "id": msg.id,
        "thread_id": msg.thread_id,
        "sender_id": msg.sender_id,
        "created_at": msg.created_at.isoformat()
    }


@router.get("/threads/{thread_id}/messages", response_model=dict)
async def get_messages(
    thread_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_chat_service(db)
    messages = service.get_thread_messages(thread_id, limit, offset)
    return {"messages": messages}


@router.get("/entities/{entity_type}/{entity_id}", response_model=dict)
async def get_entity_thread(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_chat_service(db)
    thread = service.get_entity_thread(entity_type, entity_id)
    return thread or {"exists": False}
