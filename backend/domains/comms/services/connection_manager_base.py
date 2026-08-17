"""
Shared base for per-user / per-staff WebSocket connection managers.

The connection-bookkeeping methods that are byte-identical between
``services.comms.websocket_manager.UserConnectionManager`` and
``services.public.public_comms_status_service.UserConnectionManager``
are defined once here so the logic is not duplicated. The two concrete
managers inherit these and keep only their divergent ``broadcast_to_*``
helpers.
"""
from __future__ import annotations

from fastapi import WebSocket
import logging
import structlog

logger = structlog.get_logger(__name__)
logger = logging.getLogger(__name__)


class UserConnectionManagerBase:
    """Manages per-user WebSocket connections for notifications and alerts."""

    def __init__(self):
        self._user_sockets: dict[int, set[WebSocket]] = {}
        self._staff_sockets: dict[int, set[WebSocket]] = {}

    async def connect_user(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self._user_sockets.setdefault(user_id, set()).add(websocket)

    async def connect_staff(self, websocket: WebSocket, staff_id: int):
        await websocket.accept()
        self._staff_sockets.setdefault(staff_id, set()).add(websocket)

    def disconnect_user(self, websocket: WebSocket, user_id: int):
        conns = self._user_sockets.get(user_id, set())
        conns.discard(websocket)
        if not conns:
            self._user_sockets.pop(user_id, None)

    def disconnect_staff(self, websocket: WebSocket, staff_id: int):
        conns = self._staff_sockets.get(staff_id, set())
        conns.discard(websocket)
        if not conns:
            self._staff_sockets.pop(staff_id, None)

    async def broadcast_to_all_staff(self, message: dict):
        for staff_id in list(self._staff_sockets.keys()):
            await self.broadcast_to_staff(staff_id, message)
