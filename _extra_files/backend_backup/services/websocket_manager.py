"""Backward-compatible re-export shim.

The canonical WebSocket connection manager lives in
``services/comms/websocket_manager`` and the HR activity-room helpers
(``ACTIVITY_ROOM``, ``manager``) live in ``utils/websocket_manager``.
This module exists so legacy imports such as
``from services.websocket_manager import user_manager`` and
``from services.websocket_manager import ACTIVITY_ROOM`` continue to
resolve. Do not add business logic here.
"""
from __future__ import annotations

from services.comms.websocket_manager import (  # noqa: F401
    user_manager,
    UserConnectionManager,
)
from utils.websocket_manager import (  # noqa: F401
    ACTIVITY_ROOM,
    manager,
)

__all__ = [
    "user_manager",
    "UserConnectionManager",
    "ACTIVITY_ROOM",
    "manager",
]
