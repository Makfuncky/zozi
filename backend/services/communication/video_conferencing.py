import logging
import secrets
import hashlib
import json
import httpx
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from models.core import VideoRoom, VideoRoomParticipant, VideoRoomRecording
from utils.config import settings

logger = logging.getLogger("zozi.video_conferencing")


@dataclass
class MeetingTranscript:
    meeting_id: str
    language: str
    segments: List[Dict[str, Any]] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""


@dataclass
class WatermarkedFrame:
    frame_hash: str
    employee_id: int
    ip_address: str
    timestamp: datetime
    watermarked_url: str


class VideoConferenceRoom:
    def __init__(self, db: Session):
        self.db = db
        self._cache_rooms: Dict[str, Dict[str, Any]] = {}
        self.transcripts: Dict[str, MeetingTranscript] = {}
        self.watermarks: Dict[str, List[WatermarkedFrame]] = {}

    def _load_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        if room_id in self._cache_rooms:
            return self._cache_rooms[room_id]
        room = self.db.query(VideoRoom).filter(VideoRoom.room_id == room_id).first()
        if not room:
            return None
        data = {
            "room_id": room.room_id,
            "room_uuid": room.room_uuid,
            "name": room.name,
            "country_code": room.country_code,
            "created_by": room.created_by,
            "is_boardroom": room.is_boardroom,
            "status": room.status,
            "max_participants": room.max_participants,
            "recording_enabled": room.recording_enabled,
            "watermark_enabled": room.watermark_enabled,
            "transcription_enabled": room.transcription_enabled,
            "started_at": room.started_at,
            "ended_at": room.ended_at,
            "created_at": room.created_at,
            "db_id": room.id,
        }
        self._cache_rooms[room_id] = data
        return data

    def create_room(
        self,
        name: str,
        participants: List[int],
        is_boardroom: bool = False,
        country_code: Optional[str] = None,
        employee_id: Optional[int] = None,
    ) -> dict:
        room_id = secrets.token_urlsafe(16)
        room_uuid = f"room_{secrets.token_hex(8)}"

        db_room = VideoRoom(
            room_id=room_id,
            room_uuid=room_uuid,
            name=name,
            country_code=country_code,
            created_by=employee_id,
            is_boardroom=is_boardroom,
            status="waiting",
            max_participants=100,
            watermark_enabled=True,
            transcription_enabled=True,
        )
        self.db.add(db_room)
        self.db.flush()

        for uid in participants:
            participant = VideoRoomParticipant(
                room_id=db_room.id,
                user_id=uid,
                role="participant",
            )
            self.db.add(participant)

        db_created_at = db_room.created_at
        db_id = db_room.id

        self.db.commit()

        cached = {
            "room_id": room_id,
            "room_uuid": room_uuid,
            "name": name,
            "country_code": country_code,
            "created_by": employee_id,
            "is_boardroom": is_boardroom,
            "status": "waiting",
            "max_participants": 100,
            "recording_enabled": False,
            "watermark_enabled": True,
            "transcription_enabled": True,
            "started_at": None,
            "ended_at": None,
            "created_at": db_created_at,
            "db_id": db_id,
        }
        self._cache_rooms[room_id] = cached

        self.transcripts[room_id] = MeetingTranscript(
            meeting_id=room_id,
            language="en",
            segments=[],
            action_items=[],
            summary=""
        )
        self.watermarks[room_id] = []

        return {
            "room_id": room_id,
            "room_uuid": room_uuid,
            "status": "created",
            "requires_approval": is_boardroom,
        }

    def list_rooms(self) -> list[dict]:
        rooms = self.db.query(VideoRoom).order_by(VideoRoom.created_at.desc()).limit(100).all()
        return [
            {
                "room_id": r.room_id,
                "name": r.name,
                "is_boardroom": r.is_boardroom,
                "status": r.status,
                "participant_count": len(r.participants) if r.participants else 0,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rooms
        ]

    def generate_token(
        self,
        room_id: str,
        employee_id: int,
        ip_address: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> dict:
        room = self._load_room(room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")

        db_room = self.db.query(VideoRoom).filter(VideoRoom.room_id == room_id).first()
        if not db_room:
            raise ValueError(f"Room {room_id} not found")

        participant_ids = [p.user_id for p in db_room.participants]
        if employee_id not in participant_ids:
            raise ValueError(f"Employee {employee_id} not authorized for this room")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc).timestamp() + 3600

        return {
            "token": token,
            "room_id": room_id,
            "employee_id": employee_id,
            "expires_at": expires_at,
            "ip_address": ip_address,
            "device_fingerprint": device_fingerprint,
            "watermark_enabled": room.get("watermark_enabled", True),
        }

    def generate_watermark(
        self,
        room_id: str,
        employee_id: int,
        ip_address: str,
        frame_data: bytes,
    ) -> str:
        timestamp = datetime.now(timezone.utc)
        content_hash = hashlib.sha256(frame_data).hexdigest()[:16]
        frame_hash = hashlib.sha256(
            f"{room_id}:{employee_id}:{ip_address}:{timestamp.isoformat()}:{content_hash}".encode()
        ).hexdigest()

        watermark = WatermarkedFrame(
            frame_hash=frame_hash,
            employee_id=employee_id,
            ip_address=ip_address,
            timestamp=timestamp,
            watermarked_url=f"/watermarked/{frame_hash}.png"
        )
        if room_id in self.watermarks:
            self.watermarks[room_id].append(watermark)
        return watermark.watermarked_url

    async def _transcribe_audio(self, audio_bytes: bytes, source_language: str = "en") -> str:
        """Transcribe audio using OpenAI Whisper API or fallback."""
        api_key = settings.openai_api_key
        if not api_key:
            return "[transcription unavailable - no API key]"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                data = {"model": "whisper-1", "language": source_language}
                resp = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files=files,
                    data=data,
                )
                if resp.status_code == 200:
                    return resp.json().get("text", "")
                logger.warning("Whisper API returned %s: %s", resp.status_code, resp.text)
                return "[transcription error]"
        except Exception as e:
            logger.error("Transcription failed: %s", e)
            return "[transcription failed]"

    async def _translate_text(self, text: str, target_language: str) -> str:
        """Translate text using OpenAI or fallback."""
        if target_language == "en":
            return text
        api_key = settings.openai_api_key
        if not api_key:
            return text
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": f"Translate the following text to {target_language}. Return only the translation."},
                            {"role": "user", "content": text},
                        ],
                        "temperature": 0,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                return text
        except Exception as e:
            logger.error("Translation failed: %s", e)
            return text

    async def add_transcript_segment(
        self,
        room_id: str,
        speaker_id: int,
        content: str,
        timestamp: datetime,
        language: str = "en",
        audio_bytes: Optional[bytes] = None,
        target_language: Optional[str] = None,
    ) -> dict:
        transcript = self.transcripts.get(room_id)
        if not transcript:
            transcript = MeetingTranscript(meeting_id=room_id, language=language)
            self.transcripts[room_id] = transcript

        # Transcribe audio if provided (real ASR)
        if audio_bytes and not content:
            content = await self._transcribe_audio(audio_bytes, language)

        # Translate if target differs from source
        final_content = content
        if target_language and target_language != language:
            translated = await self._translate_text(content, target_language)
            segment = {
                "speaker_id": speaker_id,
                "content": content,
                "translated_content": translated,
                "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
                "source_language": language,
                "target_language": target_language,
            }
        else:
            segment = {
                "speaker_id": speaker_id,
                "content": content,
                "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
                "language": language,
            }
        transcript.segments.append(segment)
        return segment

    def extract_action_items(
        self,
        room_id: str,
        entity_type: str,
        entity_id: int,
        action: str,
        metadata: Optional[Dict] = None,
    ) -> dict:
        transcript = self.transcripts.get(room_id)
        if not transcript:
            return {}
        action_item = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        }
        transcript.action_items.append(action_item)
        return action_item

    def get_transcript(self, room_id: str) -> dict:
        transcript = self.transcripts.get(room_id)
        if not transcript:
            return {"segments": [], "action_items": [], "summary": ""}
        return {
            "meeting_id": transcript.meeting_id,
            "language": transcript.language,
            "segments": transcript.segments,
            "action_items": transcript.action_items,
            "summary": transcript.summary,
            "word_count": sum(len(s["content"].split()) for s in transcript.segments),
        }

    def start_recording(self, room_id: str, employee_id: int) -> dict:
        room = self._load_room(room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")

        db_room = self.db.query(VideoRoom).filter(VideoRoom.room_id == room_id).first()
        if db_room:
            db_room.recording_enabled = True
            db_room.status = "recording"
            db_room.started_at = datetime.now(timezone.utc)

        recording = VideoRoomRecording(
            room_id=room["db_id"],
            started_by=employee_id,
            status="recording",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(recording)
        self.db.commit()

        room["recording_enabled"] = True
        room["status"] = "recording"
        room["started_at"] = datetime.now(timezone.utc)

        return {
            "room_id": room_id,
            "status": "recording",
            "started_at": room["started_at"].isoformat(),
        }

    def end_room(self, room_id: str) -> dict:
        room = self._load_room(room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")

        db_room = self.db.query(VideoRoom).filter(VideoRoom.room_id == room_id).first()
        if db_room:
            db_room.status = "ended"
            db_room.ended_at = datetime.now(timezone.utc)
            self.db.commit()

        room["status"] = "ended"
        room["ended_at"] = datetime.now(timezone.utc)

        transcript = self.transcripts.get(room_id)
        if transcript and transcript.segments:
            transcript.summary = self._generate_summary(transcript.segments)

        return {
            "room_id": room_id,
            "status": "ended",
            "ended_at": room["ended_at"].isoformat(),
            "total_segments": len(transcript.segments) if transcript else 0,
            "action_items_count": len(transcript.action_items) if transcript else 0,
        }

    def get_room_details(self, room_id: str) -> dict:
        room = self._load_room(room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")
        db_room = self.db.query(VideoRoom).filter(VideoRoom.room_id == room_id).first()
        participants_list = []
        if db_room and db_room.participants:
            for p in db_room.participants:
                participants_list.append({
                    "user_id": p.user_id,
                    "role": p.role,
                    "joined_at": p.joined_at.isoformat() if p.joined_at else None,
                })
        return {
            "room_id": room["room_id"],
            "room_uuid": room.get("room_uuid"),
            "name": room["name"],
            "is_boardroom": room["is_boardroom"],
            "status": room["status"],
            "country_code": room["country_code"],
            "max_participants": room["max_participants"],
            "recording_enabled": room["recording_enabled"],
            "watermark_enabled": room["watermark_enabled"],
            "transcription_enabled": room["transcription_enabled"],
            "participants": participants_list,
            "started_at": room["started_at"].isoformat() if room["started_at"] else None,
            "ended_at": room["ended_at"].isoformat() if room["ended_at"] else None,
            "created_at": room["created_at"].isoformat() if room["created_at"] else None,
        }

    def _generate_summary(self, segments: List[Dict]) -> str:
        return f"Meeting recorded {len(segments)} segments of discussion."


def get_video_conference(db: Session) -> VideoConferenceRoom:
    return VideoConferenceRoom(db)
