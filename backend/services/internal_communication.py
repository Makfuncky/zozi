import logging
import secrets
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from models.communication import (
    InternalChannel,
    InternalChannelMember,
    InternalMessage,
)
from models.employee_models import EmailFolder, InternalEmail

logger = logging.getLogger("zozi.internal_comm")


@dataclass
class ChannelMember:
    user_id: int
    role: str = "member"
    joined_at: datetime = field(default_factory=datetime.utcnow)


class InternalCommunicationService:
    def __init__(self, db: Session):
        self.db = db

    def create_channel(
        self,
        name: str,
        description: Optional[str] = None,
        is_public: bool = True,
        created_by: Optional[int] = None,
        country_code: Optional[str] = None,
        allowed_roles: Optional[List[str]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
    ) -> dict:
        channel_id = secrets.token_urlsafe(16)
        channel = InternalChannel(
            channel_id=channel_id,
            name=name,
            description=description,
            entity_type=entity_type or "global",
            entity_id=entity_id or 0,
            is_public=is_public,
            created_by=created_by,
            country_code=country_code,
            allowed_roles=allowed_roles or [],
        )
        self.db.add(channel)
        self.db.flush()

        if created_by:
            member = InternalChannelMember(
                channel_id=channel.id,
                user_id=created_by,
                role="admin",
            )
            self.db.add(member)
        self.db.commit()
        self.db.refresh(channel)

        return {
            "id": channel.id,
            "channel_id": channel.channel_id,
            "name": channel.name,
            "description": channel.description,
            "entity_type": channel.entity_type,
            "entity_id": channel.entity_id,
            "is_public": channel.is_public,
            "created_by": channel.created_by,
            "country_code": channel.country_code,
            "allowed_roles": channel.allowed_roles,
            "created_at": channel.created_at.isoformat(),
        }

    def get_channel(self, channel_id: str) -> Optional[dict]:
        channel = (
            self.db.query(InternalChannel)
            .filter(InternalChannel.channel_id == channel_id)
            .first()
        )
        if not channel:
            return None

        return {
            "id": channel.id,
            "channel_id": channel.channel_id,
            "name": channel.name,
            "description": channel.description,
            "is_public": channel.is_public,
            "created_by": channel.created_by,
            "country_code": channel.country_code,
            "allowed_roles": channel.allowed_roles,
            "created_at": channel.created_at.isoformat(),
        }

    def list_channels(
        self, user_id: int, country_code: Optional[str] = None
    ) -> List[dict]:
        channels = (
            self.db.query(InternalChannel)
            .filter(InternalChannel.is_active == True)
            .order_by(InternalChannel.created_at.desc())
            .all()
        )
        result = []

        for channel in channels:
            if country_code and channel.country_code and channel.country_code != country_code:
                continue
            member = (
                self.db.query(InternalChannelMember)
                .filter(
                    InternalChannelMember.channel_id == channel.id,
                    InternalChannelMember.user_id == user_id,
                )
                .first()
            )
            if member or channel.is_public:
                result.append({
                    "id": channel.id,
                    "channel_id": channel.channel_id,
                    "name": channel.name,
                    "description": channel.description,
                    "is_public": channel.is_public,
                    "member_role": member.role if member else None,
                    "country_code": channel.country_code,
                    "created_at": channel.created_at.isoformat(),
                })

        return result

    def add_member(
        self, channel_id: str, user_id: int, role: str = "member"
    ) -> dict:
        channel = (
            self.db.query(InternalChannel)
            .filter(InternalChannel.channel_id == channel_id)
            .first()
        )
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        existing = (
            self.db.query(InternalChannelMember)
            .filter(
                InternalChannelMember.channel_id == channel.id,
                InternalChannelMember.user_id == user_id,
            )
            .first()
        )
        if existing:
            return {
                "channel_id": channel_id,
                "user_id": user_id,
                "role": existing.role,
                "status": "already_member",
            }

        member = InternalChannelMember(
            channel_id=channel.id, user_id=user_id, role=role
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)

        return {
            "channel_id": channel_id,
            "user_id": user_id,
            "role": role,
            "status": "added",
        }

    def remove_member(self, channel_id: str, user_id: int) -> dict:
        channel = (
            self.db.query(InternalChannel)
            .filter(InternalChannel.channel_id == channel_id)
            .first()
        )
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        member = (
            self.db.query(InternalChannelMember)
            .filter(
                InternalChannelMember.channel_id == channel.id,
                InternalChannelMember.user_id == user_id,
            )
            .first()
        )
        if not member:
            raise ValueError(f"User {user_id} is not a member")

        self.db.delete(member)
        self.db.commit()

        return {"channel_id": channel_id, "user_id": user_id, "status": "removed"}

    def send_message(
        self,
        channel_id: str,
        sender_id: int,
        content: str,
        message_type: str = "text",
        is_masked: bool = True,
    ) -> dict:
        channel = (
            self.db.query(InternalChannel)
            .filter(InternalChannel.channel_id == channel_id)
            .first()
        )
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        member = (
            self.db.query(InternalChannelMember)
            .filter(
                InternalChannelMember.channel_id == channel.id,
                InternalChannelMember.user_id == sender_id,
            )
            .first()
        )
        if not member:
            raise ValueError(f"User {sender_id} is not a member of this channel")

        message = InternalMessage(
            channel_id=channel.id,
            user_id=sender_id,
            message=content,
            message_type=message_type,
            is_masked=is_masked,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return {
            "id": message.id,
            "channel_id": channel_id,
            "sender_id": sender_id,
            "content": content,
            "message_type": message_type,
            "is_masked": is_masked,
            "created_at": message.created_at.isoformat(),
        }

    def get_messages(
        self, channel_id: str, limit: int = 50, offset: int = 0
    ) -> List[dict]:
        channel = (
            self.db.query(InternalChannel)
            .filter(InternalChannel.channel_id == channel_id)
            .first()
        )
        if not channel:
            return []

        messages = (
            self.db.query(InternalMessage)
            .filter(InternalMessage.channel_id == channel.id)
            .order_by(InternalMessage.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            {
                "id": m.id,
                "sender_id": m.user_id,
                "content": m.message,
                "message_type": m.message_type,
                "is_masked": m.is_masked,
                "created_at": m.created_at.isoformat(),
            }
            for m in reversed(messages)
        ]


def get_internal_communication_service(db: Session) -> InternalCommunicationService:
    return InternalCommunicationService(db)
