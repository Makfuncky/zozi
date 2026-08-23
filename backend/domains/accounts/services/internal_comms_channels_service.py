"""Auto-migrated service logic from routers/internal_comms_channels.py."""
from __future__ import annotations

import logging

from typing import List, Optional

from fastapi import Body, Depends, Query, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.comms.services.internal_communication import get_internal_communication_service

logger = logging.getLogger("zozi.api.internal")









from domains.accounts.services.internal_channels_service import list_channels






















from domains.accounts.services.internal_channels_service import get_channel













from domains.accounts.services.internal_channels_service import add_member











from domains.accounts.services.internal_channels_service import remove_member













from domains.accounts.services.internal_channels_service import send_message














from domains.accounts.services.internal_channels_service import get_messages


