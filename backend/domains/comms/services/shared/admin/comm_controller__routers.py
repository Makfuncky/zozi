"""controllers.comms.comm_controller controller.

Coordinates communication business rules and delegates ALL persistence to
``services.comms.comm_service``. It must not issue ``db.query`` directly
and must not perform commits.

The HTTP contract is declared with ``infrastructure.routing.route_contract`` decorators
so the auto-router emits ``routers/public_comms_comm.py``.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from infrastructure.routing.route_contract import get, post

from domains.comms.services.shared.admin.comm_service import (
    create_chat_thread as service_create_chat_thread,
    create_incident_room as service_create_incident_room,
    create_video_room as service_create_video_room,
    get_command_center_metrics as service_get_command_center_metrics,
    send_masked_message as service_send_masked_message,
)


@get("/metrics", deps=["db"], tags=["comm"])
def get_command_center_metrics(db: Session) -> dict:
    return service_get_command_center_metrics(db)


@post("/video", deps=["db"], tags=["comm"])
def create_video_room(room_data: dict, db: Session) -> dict:
    return service_create_video_room(room_data, db)


@post("/chat", deps=["db"], tags=["comm"])
def create_chat_thread(thread_data: dict, db: Session) -> dict:
    return service_create_chat_thread(thread_data, db)


@post("/message", deps=["db"], query=["sender_id", "recipient_ref", "message"], tags=["comm"])
def send_message(sender_id: int, recipient_ref: str, message: str, db: Session) -> dict:
    return service_send_masked_message(sender_id, recipient_ref, message, db)


@post("/incident", deps=["db"], tags=["comm"])
def create_incident_room(alert_data: dict, db: Session) -> dict:
    return service_create_incident_room(alert_data, db)
