"""Chatbot router — AI product assistant."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from controllers.chatbot_controller import handle_message, record_product_click
from data.db import get_db
from data.models import User
from utils.dependencies import get_current_user_optional

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = None
    lang: Optional[str] = "en"


class ProductClickRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


@router.post("/message")
def chat_message(
    payload: ChatRequest,
    supplier_id: Optional[int] = Query(default=None, ge=1),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) if current_user else None
    return handle_message(
        db=db,
        message=payload.message,
        user_id=user_id,
        session_id=payload.session_id,
        supplier_id=supplier_id,
        lang=payload.lang or "en",
    )


@router.post("")
def chat_message_root(
    payload: ChatRequest,
    supplier_id: Optional[int] = Query(default=None, ge=1),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    return chat_message(payload, supplier_id, current_user, db)


@router.post("/record-click/{product_id}")
def chat_record_click(
    product_id: int,
    payload: ProductClickRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) if current_user else None
    record_product_click(
        db=db,
        session_id=payload.session_id,
        product_id=product_id,
        user_id=user_id,
    )
    return {"status": "recorded"}

