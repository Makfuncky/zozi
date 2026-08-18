"""Admin Chat Router — consolidated + country-scoped wrapper around EntityChatThread endpoints with admin auth."""
import logging
from typing import List, Optional
from fastapi import Body, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from infrastructure.database.database import get_db
from domains.accounts.models.user import User
from domains.accounts.models.core import EntityChatThread
from domains.accounts.models.core import EntityChatMessage
from domains.comms.services.chat_system import ChatSystem
from domains.comms.services.chat_system import get_chat_system
from domains.comms.services.entity_chat_service import EntityChatService
from domains.comms.services.entity_chat_service import get_chat_service
from infrastructure.utils.dependencies import require_admin
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
logger = logging.getLogger('zozi.api.admin_chat')

def admin_chat_metrics(_: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Chat metrics across all countries."""
    total_threads = db.query(sqlfunc.count(EntityChatThread.id)).scalar() or 0
    total_messages = db.query(sqlfunc.count(EntityChatMessage.id)).scalar() or 0
    return {'total_threads': total_threads, 'total_messages': total_messages}
