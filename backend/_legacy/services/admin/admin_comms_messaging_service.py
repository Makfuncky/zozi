"""Admin Chat Router — consolidated + country-scoped wrapper around EntityChatThread endpoints with admin auth."""
import logging
from typing import List, Optional
from fastapi import Body, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from db.database import get_db
from models import User
from models.core import EntityChatThread, EntityChatMessage
from services.comms.chat_system import ChatSystem, get_chat_system
from services.comms.entity_chat_service import EntityChatService, get_chat_service
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
logger = logging.getLogger('zozi.api.admin_chat')

def admin_chat_metrics(_: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Chat metrics across all countries."""
    total_threads = db.query(sqlfunc.count(EntityChatThread.id)).scalar() or 0
    total_messages = db.query(sqlfunc.count(EntityChatMessage.id)).scalar() or 0
    return {'total_threads': total_threads, 'total_messages': total_messages}
