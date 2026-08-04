"""WebSocket Manager for Real-Time Updates.

Also exposes `broadcast_activity_event`, a sync → async bridge so that
sync code (e.g. `log_activity`) can fire-and-forget WebSocket broadcasts
without depending on the router layer.
"""

import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket
from collections import defaultdict

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.user_connections: Dict[int, List[str]] = defaultdict(list)
    
    async def connect(self, websocket: WebSocket, room: str, user_id: int = None):
        self.active_connections[room].append(websocket)
        if user_id:
            self.user_connections[user_id].append(room)
    
    def disconnect(self, websocket: WebSocket, room: str):
        if websocket in self.active_connections[room]:
            self.active_connections[room].remove(websocket)
        for user_id, rooms in self.user_connections.items():
            if room in rooms:
                rooms.remove(room)
    
    async def broadcast_to_room(self, room: str, message: dict):
        """Broadcast a message to all connections in a room."""
        if room not in self.active_connections:
            return
        for connection in self.active_connections[room][:]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                self.active_connections[room].remove(connection)
    
    async def send_to_user(self, user_id: int, message: dict):
        """Send a message to all rooms a user is connected to."""
        for room in self.user_connections.get(user_id, []):
            await self.broadcast_to_room(room, message)
    
    async def send_employee_update(self, employee_id: int, event: str, data: dict):
        """Send an employee-specific update."""
        await self.broadcast_to_room(f"employee:{employee_id}", {
            "event": event,
            "data": data,
            "timestamp": json.dumps({"$date": "2024-01-01T00:00:00Z"})
        })
    
    async def send_country_update(self, country_code: str, event: str, data: dict):
        """Send a country-wide update."""
        await self.broadcast_to_room(f"country:{country_code}", {
            "event": event,
            "data": data,
        })


manager = WebSocketManager()
ws_manager = manager


ACTIVITY_ROOM = "activity:hr"
BACKGROUND_JOBS_ROOM = "admin:background-jobs"


def _broadcast_to_room(room: str, event_data: dict) -> None:
    """Fire-and-forget broadcast a message to a WebSocket room.

    Called from sync code. Schedules the async broadcast on the running
    event loop if one exists; silently no-ops when no loop is available
    (e.g. in tests or CLI).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                manager.broadcast_to_room(room, event_data),
                loop,
            )
    except RuntimeError:
        pass


def broadcast_activity_event(event_data: dict) -> None:
    """Fire-and-forget broadcast an activity event to the HR activity room."""
    _broadcast_to_room(ACTIVITY_ROOM, event_data)


def broadcast_background_job_update(event_data: dict) -> None:
    """Fire-and-forget broadcast a background-job status update to the admin
    dashboard room so connected UIs update in real-time after a sweep.

    Called from sync code (e.g. ``auto_payout_scheduler._update_after_sweep``)
    after each sweep completes.
    """
    _broadcast_to_room(BACKGROUND_JOBS_ROOM, event_data)

