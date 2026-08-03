"""Video Conference Controller for admin and employee meetings."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query, Path
from sqlalchemy.orm import Session

from data.db import get_db
from services.video_conferencing import get_video_conference
from data.models import User
from utils.dependencies import require_admin, require_employee
from utils.config import settings

logger = logging.getLogger("zozi.api.video")
router = APIRouter()


@router.post("/rooms")
def create_room(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_boardroom: bool = Body(False, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    employee_id: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.create_room(name, participants, is_boardroom, country_code, employee_id)


@router.get("/rooms")
def list_rooms(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.list_rooms()


@router.get("/rooms/{room_id}")
def get_room(
    room_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.get_room_details(room_id)


@router.post("/rooms/{room_id}/token")
def generate_token(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    ip_address: Optional[str] = Body(None, embed=True),
    device_fingerprint: Optional[str] = Body(None, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.generate_token(room_id, employee_id, ip_address, device_fingerprint, country_code)


@router.post("/rooms/{room_id}/recording/start")
def start_recording(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.start_recording(room_id, employee_id)


@router.post("/rooms/{room_id}/recording/end")
def end_recording(
    room_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.end_room(room_id)


@router.get("/rooms/{room_id}/transcript")
def get_transcript(
    room_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.get_transcript(room_id)


@router.post("/rooms/{room_id}/action-items")
def extract_action_items(
    room_id: str,
    entity_type: str = Body(..., embed=True),
    entity_id: int = Body(..., embed=True),
    action: str = Body(..., embed=True),
    metadata: Optional[dict] = Body(None, embed=True),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.extract_action_items(room_id, entity_type, entity_id, action, metadata)


@router.post("/rooms/{room_id}/transcript/segment")
async def add_transcript_segment(
    room_id: str,
    speaker_id: int = Body(..., embed=True),
    content: Optional[str] = Body(None, embed=True),
    timestamp: str = Body(..., embed=True),
    language: str = Body("en", embed=True),
    audio_bytes: Optional[bytes] = Body(None, embed=True),
    target_language: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    from datetime import datetime
    return await vc.add_transcript_segment(
        room_id, speaker_id, content, 
        datetime.fromisoformat(timestamp) if timestamp else None,
        language, audio_bytes, target_language
    )
