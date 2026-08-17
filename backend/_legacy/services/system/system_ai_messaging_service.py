"""Chatbot router — AI product assistant."""
from __future__ import annotations
from typing import Optional
from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from controllers.comms.chatbot_controller import handle_message, record_product_click
from db.database import get_db
from _legacy.models import User
from utils.dependencies import get_current_user_optional

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = None
    lang: Optional[str] = 'en'

class ProductClickRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
