"""
WebSocket Connection Manager Service.

Moved out of routers/ws_chat.py to break the
services -> routers forbidden dependency edge.
"""

from fastapi import WebSocket


class UserConnectionManager:
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

    async def broadcast_to_user(self, user_id: int, message: dict):
        dead = set()
        for ws in self._user_sockets.get(user_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._user_sockets.get(user_id, set()).discard(ws)

    async def broadcast_to_staff(self, staff_id: int, message: dict):
        dead = set()
        for ws in self._staff_sockets.get(staff_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._staff_sockets.get(staff_id, set()).discard(ws)

    async def broadcast_to_all_staff(self, message: dict):
        for staff_id in list(self._staff_sockets.keys()):
            await self.broadcast_to_staff(staff_id, message)


user_manager = UserConnectionManager()
