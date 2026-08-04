"""Admin Chat Router — consolidated + country-scoped wrapper around EntityChatThread endpoints with admin auth."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session

from data.db import get_db
from data.models import User
from services.chat_system import ChatSystem, get_chat_system
from services.communication.entity_chat_service import EntityChatService, get_chat_service
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

logger = logging.getLogger("zozi.api.admin_chat")
router = APIRouter()


def _resolve_country(request: Request, default: str = "AE") -> str:
    raw = (request.headers.get("X-Country-Code") or "").strip().upper()
    return raw or default


@router.get("/chat")
def admin_list_all_threads(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all chat threads across all countries (consolidated view)."""
    chat = get_chat_system(db)
    return chat.list_threads()


@router.get("/chat/threads")
def admin_list_chat_threads(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all chat threads (consolidated; Communication hub + employee comms)."""
    chat = get_chat_system(db)
    return chat.list_threads()


@router.get("/chat/threads/{thread_id}/messages")
def admin_get_chat_thread_messages(
    thread_id: int = Path(...),
    limit: int = Query(100, ge=1, le=500),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    chat = get_chat_system(db)
    return {"messages": chat.get_thread_messages(thread_id, limit)}


@router.post("/chat/threads/{thread_id}/messages")
def admin_send_chat_thread_message(
    thread_id: int = Path(...),
    sender_id: int = Body(...),
    message: str = Body(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    svc = EntityChatService(db)
    msg = svc.send_message(thread_id, sender_id, message)
    return {
        "id": msg.id,
        "thread_id": msg.thread_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


@router.post("/chat/direct")
def admin_create_direct_chat(
    participants: List[int] = Body(..., embed=True),
    name: Optional[str] = Body(None, embed=True),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    chat = get_chat_system(db)
    return chat.create_direct_chat(participants, name)


@router.post("/chat/group")
def admin_create_group_chat(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_encrypted: bool = Body(False, embed=True),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    chat = get_chat_system(db)
    return chat.create_group_chat(name, participants, is_encrypted)


@router.get("/chat/metrics")
def admin_chat_metrics(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Chat metrics across all countries."""
    chat = get_chat_system(db)
    return chat.get_chat_metrics()


@router.get("/chat/threads/{country_code}")
def admin_list_threads(
    country_code: str = Path(..., description="ISO country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        chat = get_chat_system(db)
        return chat.list_threads()
    finally:
        clear_rls_context()


@router.post("/chat/threads/{country_code}")
def admin_create_thread(
    country_code: str = Path(..., description="ISO country code"),
    title: str = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        from services.chat_system import ChatSystem
        resolved_type = entity_type or "admin"
        resolved_id = entity_id or 0
        try:
            chat = ChatSystem(db)
            result = chat.create_thread(title, resolved_type, resolved_id)
            return result
        except Exception as e:
            logger.exception("create_thread failed")
            raise HTTPException(status_code=500, detail=str(e))
    finally:
        clear_rls_context()


@router.post("/chat/threads")
def admin_create_thread_global(
    title: str = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    country_code: Optional[str] = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a chat thread (global — defaults to AE when no country provided)."""
    cc = (country_code or "AE").upper()
    get_country_or_404(cc, db)
    set_rls_context({cc}, is_restricted=True)
    try:
        from services.chat_system import ChatSystem

        resolved_type = entity_type or "admin"
        resolved_id = entity_id or 0
        chat = ChatSystem(db)
        return chat.create_thread(title, resolved_type, resolved_id)
    finally:
        clear_rls_context()


@router.get("/chat/threads/{country_code}/{thread_id}/messages")
def admin_get_thread_messages(
    country_code: str = Path(..., description="ISO country code"),
    thread_id: int = Path(...),
    limit: int = Query(100, ge=1, le=500),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        chat = get_chat_system(db)
        return {"messages": chat.get_thread_messages(thread_id, limit)}
    finally:
        clear_rls_context()


@router.post("/chat/threads/{country_code}/{thread_id}/messages")
def admin_send_thread_message(
    country_code: str = Path(..., description="ISO country code"),
    thread_id: int = Path(...),
    sender_id: int = Body(...),
    message: str = Body(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        svc = EntityChatService(db)
        msg = svc.send_message(thread_id, sender_id, message)
        return {
            "id": msg.id,
            "thread_id": msg.thread_id,
            "sender_id": msg.sender_id,
            "message": msg.message,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
    finally:
        clear_rls_context()

