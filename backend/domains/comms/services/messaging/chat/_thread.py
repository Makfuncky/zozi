"""Auto-split from chat_system.py: ChatThread model."""

import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from domains.governance.ports import DirectChatRoom
from domains.governance.ports import DirectChatMessage
from domains.governance.ports import GroupChatRoom
from domains.governance.ports import GroupChatMember
from domains.governance.ports import GroupChatMessage
from domains.governance.ports import User
from domains.comms.models.communication import ChatAttachment
from infrastructure.utils.storage import storage as _storage

logger = logging.getLogger("zozi.chat")


@dataclass


class ChatThread:
    thread_id: str
    entity_type: str
    entity_id: int
    participants: List[int] = field(default_factory=list)
    name: str = ""
    is_external: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    channel_type: str = "entity"
