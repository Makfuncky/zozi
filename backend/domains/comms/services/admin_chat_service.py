"""Auto-migrated service logic from routers/admin_chat.py."""
from __future__ import annotations

import logging

from typing import List, Optional

from fastapi import Body, Depends, HTTPException, Path, Query, Request

from sqlalchemy import func as sqlfunc

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from _legacy.models import User

from domains.accounts.models.core import EntityChatMessage, EntityChatThread

from services.comms.chat_system import get_chat_system

from services.comms.entity_chat_service import EntityChatService

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context

logger = logging.getLogger("zozi.api.admin_chat")














from services.admin.admin_comms_messaging_service import admin_list_all_threads  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)

from services.admin.admin_comms_messaging_service import admin_list_chat_threads  # [MIGRATION COMPAT] re-export relocated symbol






















from services.admin.admin_comms_messaging_service import admin_get_chat_thread_messages  # [MIGRATION COMPAT] re-export relocated symbol














from services.admin.admin_comms_messaging_service import admin_send_chat_thread_message  # [MIGRATION COMPAT] re-export relocated symbol











from services.admin.admin_comms_messaging_service import admin_create_direct_chat  # [MIGRATION COMPAT] re-export relocated symbol













from services.admin.admin_comms_messaging_service import admin_create_group_chat  # [MIGRATION COMPAT] re-export relocated symbol














from services.admin.admin_comms_messaging_service import admin_chat_metrics  # [MIGRATION COMPAT] re-export relocated symbol
from services.admin.admin_comms_messaging_service import admin_list_threads  # [MIGRATION COMPAT] re-export relocated symbol


# === auto-wiring re-exports (migration repair) ===
from services.admin.admin_comms_messaging_service import (
    admin_create_thread,
    admin_create_thread_global,
    admin_get_thread_messages,
    admin_send_thread_message
)

from services.admin.admin_comms_messaging_service import admin_list_all_threads  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)


