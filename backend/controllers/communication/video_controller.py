"""
Video Conferencing Controller
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from dependencies.db import get_db
from services.communication.video_conferencing import VideoConferenceRoom, get_video_conference

logger = logging.getLogger("zozi.api.video")


def create_room(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_boardroom: bool = Body(False, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.create_room(name, participants, is_boardroom, country_code)


def list_rooms(db: Session = Depends(get_db)):
    vc = get_video_conference(db)
    return vc.list_rooms()


def generate_token(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    ip_address: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.generate_token(room_id, employee_id, ip_address)


def start_recording(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.start_recording(room_id, employee_id)


def end_room(
    room_id: str,
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.end_room(room_id)


def get_room_details(room_id: str, db: Session = Depends(get_db)):
    vc = get_video_conference(db)
    return vc.get_room_details(room_id)
