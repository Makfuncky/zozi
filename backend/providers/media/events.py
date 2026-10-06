from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

EVENT_MEDIA_ASSET_CREATED = "media.asset.created"
EVENT_MEDIA_ASSET_DELETED = "media.asset.deleted"
EVENT_UPLOAD_SESSION_COMPLETED = "media.upload_session.completed"


@dataclass(frozen=True)
class MediaEvent:
    event_type: str = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), init=False
    )

    def serialize(self) -> Dict[str, Any]:
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d


@dataclass(frozen=True)
class MediaAssetCreated(MediaEvent):
    asset_id: int = 0
    storage_key: str = ""
    country_code: str = ""
    event_type: str = field(default=EVENT_MEDIA_ASSET_CREATED, init=False)


@dataclass(frozen=True)
class MediaAssetDeleted(MediaEvent):
    asset_id: int = 0
    event_type: str = field(default=EVENT_MEDIA_ASSET_DELETED, init=False)


@dataclass(frozen=True)
class UploadSessionCompleted(MediaEvent):
    session_id: int = 0
    event_type: str = field(default=EVENT_UPLOAD_SESSION_COMPLETED, init=False)


__all__ = [
    "EVENT_MEDIA_ASSET_CREATED",
    "EVENT_MEDIA_ASSET_DELETED",
    "EVENT_UPLOAD_SESSION_COMPLETED",
    "MediaEvent",
    "MediaAssetCreated",
    "MediaAssetDeleted",
    "UploadSessionCompleted",
]
