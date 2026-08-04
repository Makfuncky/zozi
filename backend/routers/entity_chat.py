"""Entity-Attached Contextual Chat Router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from data.dependencies_auth import get_current_user
from services.communication.entity_chat_service import get_entity_threads, get_entity_thread_by_id, get_entity_thread_messages, get_entity_participants
from data.services_communication_entity_chat_service import (
    get_chat_service,
)

router = APIRouter()


@router.post("/threads", response_model=dict)
async def create_thread(
    entity_type: str,
    entity_id: int,
    title: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    service = get_chat_service()
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
):
    from data.db import get_db_context
    from services.core.users_write_service import get_user_by_id

    with get_db_context() as db:
        user = get_user_by_id(db, int(current_user["sub"]))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    service = get_chat_service()
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
):
    service = get_chat_service()
    messages = service.get_thread_messages(thread_id, limit, offset)
    return {"messages": messages}


@router.get("/entities/{entity_type}/{entity_id}", response_model=dict)
async def get_entity_thread(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(get_current_user),
):
    service = get_chat_service()
    thread = service.get_entity_thread(entity_type, entity_id)
    return thread or {"exists": False}
