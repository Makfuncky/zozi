"""Auto-migrated service logic from routers/internal_comms_channels.py."""
from __future__ import annotations

import logging

from typing import List, Optional

from fastapi import Body, Depends, Query, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from services.comms.internal_communication import get_internal_communication_service

logger = logging.getLogger("zozi.api.internal")








from services.core.internal_channels_service import create_channel  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)

from services.core.internal_channels_service import list_channels  # [MIGRATION COMPAT] re-export relocated symbol






















from services.core.internal_channels_service import get_channel  # [MIGRATION COMPAT] re-export relocated symbol













from services.core.internal_channels_service import add_member  # [MIGRATION COMPAT] re-export relocated symbol











from services.core.internal_channels_service import remove_member  # [MIGRATION COMPAT] re-export relocated symbol













from services.core.internal_channels_service import send_message  # [MIGRATION COMPAT] re-export relocated symbol














from services.core.internal_channels_service import get_messages  # [MIGRATION COMPAT] re-export relocated symbol

from services.core.internal_channels_service import create_channel  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)

