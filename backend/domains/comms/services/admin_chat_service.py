"""Auto-migrated service logic from routers/admin_chat.py."""
from __future__ import annotations

import logging

from typing import List, Optional

from fastapi import Body, Depends, HTTPException, Path, Query, Request

from sqlalchemy import func as sqlfunc

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.accounts.ports import User

from domains.accounts.ports import EntityChatMessage, EntityChatThread

from domains.comms.services.chat_system import get_chat_system

from domains.comms.services.entity_chat_service import EntityChatService

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context

logger = logging.getLogger("zozi.api.admin_chat")















from domains.governance.services.admin_comms_messaging_service import admin_list_chat_threads






















from domains.governance.services.admin_comms_messaging_service import admin_get_chat_thread_messages














from domains.governance.services.admin_comms_messaging_service import admin_send_chat_thread_message











from domains.governance.services.admin_comms_messaging_service import admin_create_direct_chat













from domains.governance.services.admin_comms_messaging_service import admin_create_group_chat














from domains.governance.services.admin_comms_messaging_service import admin_chat_metrics
from domains.governance.services.admin_comms_messaging_service import admin_list_threads


# === auto-wiring re-exports (migration repair) ===
from domains.governance.services.admin_comms_messaging_service import admin_create_thread
from domains.governance.services.admin_comms_messaging_service import admin_create_thread_global
from domains.governance.services.admin_comms_messaging_service import admin_get_thread_messages
from domains.governance.services.admin_comms_messaging_service import admin_send_thread_message



