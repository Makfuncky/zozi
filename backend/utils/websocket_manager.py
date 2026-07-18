"""WebSocket Manager for Real-Time Updates."""
from __future__ import annotations
import json
from typing import Dict, List, Set
from fastapi import WebSocket
from collections import defaultdict


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

