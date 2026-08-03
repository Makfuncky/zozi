"""Enterprise Communication Router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket
from sqlalchemy.orm import Session

from controllers.comm_controller import (
    create_video_room, create_chat_thread, send_masked_message,
    create_incident_room, get_command_center_metrics
)
from data.db import get_db
from utils.websocket_manager import manager

router = APIRouter()


@router.post("/video")
def create_room(room_data: dict, db: Session = Depends(get_db)):
    return create_video_room(room_data, db)


@router.post("/chat")
def create_thread(thread_data: dict, db: Session = Depends(get_db)):
    return create_chat_thread(thread_data, db)


@router.post("/message")
def send_message(sender_id: int = Query(...), recipient_ref: str = Query(...), message: str = Query(...), db: Session = Depends(get_db)):
    return send_masked_message(sender_id, recipient_ref, message, db)


@router.post("/incident")
def create_incident(alert_data: dict, db: Session = Depends(get_db)):
    return create_incident_room(alert_data, db)


@router.get("/metrics")
def comm_metrics(db: Session = Depends(get_db)):
    return get_command_center_metrics(db)


@router.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast_to_room(room, {"data": data})
    except Exception:
        manager.disconnect(websocket, room)

