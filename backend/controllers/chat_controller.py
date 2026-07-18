"""
Chat System Controller
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from db.database import get_db
from services.chat_system import ChatSystem, get_chat_system

logger = logging.getLogger("zozi.api.chat")
router = APIRouter()


@router.post("/direct")
def create_direct_chat(
    participants: List[int] = Body(..., embed=True),
    name: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    chat = get_chat_system(db)
    return chat.create_direct_chat(participants, name)


@router.post("/group")
def create_group_chat(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_encrypted: bool = Body(False, embed=True),
    db: Session = Depends(get_db)
):
    chat = get_chat_system(db)
    return chat.create_group_chat(name, participants, is_encrypted)


@router.post("/message")
def send_message(
    chat_id: str = Body(..., embed=True),
    sender_id: int = Body(..., embed=True),
    content: str = Body(..., embed=True),
    message_type: str = Body("text", embed=True),
    db: Session = Depends(get_db)
):
    chat = get_chat_system(db)
    return chat.send_message(chat_id, sender_id, content, message_type)


@router.get("/history/{chat_id}")
def get_history(chat_id: str, limit: int = 100, db: Session = Depends(get_db)):
    chat = get_chat_system(db)
    return chat.get_chat_history(chat_id, limit)


@router.get("/threads")
def list_threads(db: Session = Depends(get_db)):
    chat = get_chat_system(db)
    return chat.list_threads()


@router.post("/threads")
def create_thread(
    title: str = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    chat = get_chat_system(db)
    return chat.create_thread(title, entity_type, entity_id)


@router.get("/threads/{thread_id}/messages")
def get_thread_messages(thread_id: int, limit: int = 100, db: Session = Depends(get_db)):
    chat = get_chat_system(db)
    return {"messages": chat.get_thread_messages(thread_id, limit)}


@router.post("/threads/{thread_id}/messages")
def send_thread_message(
    thread_id: int,
    sender_id: int = Body(..., embed=True),
    message: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    chat = get_chat_system(db)
    result = chat.send_message(str(thread_id), sender_id, message)
    return result


@router.post("/read")
def mark_read(
    chat_id: str = Body(..., embed=True),
    user_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    chat = get_chat_system(db)
    return chat.mark_read(chat_id, user_id)

