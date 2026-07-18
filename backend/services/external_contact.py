import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from models.communication import (
    ExternalContactMasking,
    ProxyChannel,
    ProxySession,
    ProxyMessage,
    ProxyCallLog,
)

logger = logging.getLogger("zozi.external_contact")


class ExternalContactService:
    def __init__(self, db: Session):
        self.db = db

    def create_mask(
        self,
        employee_id: int,
        external_contact_id: int,
        masking_type: str = "external",
    ) -> dict:
        existing = (
            self.db.query(ExternalContactMasking)
            .filter(
                ExternalContactMasking.employee_id == employee_id,
                ExternalContactMasking.external_contact_id == external_contact_id,
            )
            .first()
        )
        if existing:
            return {
                "mask_id": existing.mask_id,
                "employee_id": employee_id,
                "external_contact_id": external_contact_id,
                "is_active": existing.is_active,
                "created_at": existing.created_at.isoformat() if existing.created_at else None,
            }

        mask = ExternalContactMasking(
            employee_id=employee_id,
            external_contact_id=external_contact_id,
            mask_id=f"mask_{secrets.token_hex(8)}",
            masking_type=masking_type,
            is_active=True,
        )
        self.db.add(mask)
        self.db.commit()
        self.db.refresh(mask)

        return {
            "mask_id": mask.mask_id,
            "employee_id": employee_id,
            "external_contact_id": external_contact_id,
            "is_active": mask.is_active,
            "created_at": mask.created_at.isoformat() if mask.created_at else None,
        }

    def get_mask(self, mask_id: str) -> Optional[dict]:
        mask = (
            self.db.query(ExternalContactMasking)
            .filter(ExternalContactMasking.mask_id == mask_id)
            .first()
        )
        if not mask:
            return None

        return {
            "mask_id": mask.mask_id,
            "employee_id": mask.employee_id,
            "external_contact_id": mask.external_contact_id,
            "masking_type": mask.masking_type,
            "is_active": mask.is_active,
            "created_at": mask.created_at.isoformat() if mask.created_at else None,
        }

    def create_proxy_channel(
        self,
        mask_id: str,
        channel_type: str = "email",
    ) -> dict:
        mask = (
            self.db.query(ExternalContactMasking)
            .filter(ExternalContactMasking.mask_id == mask_id)
            .first()
        )
        if not mask:
            raise ValueError(f"Mask {mask_id} not found")

        channel = ProxyChannel(
            mask_id=mask.id,
            channel_type=channel_type,
            channel_identifier=f"{channel_type}_{secrets.token_hex(8)}",
            is_active=True,
        )
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)

        return {
            "channel_id": channel.channel_id,
            "mask_id": mask_id,
            "channel_type": channel_type,
            "channel_identifier": channel.channel_identifier,
            "is_active": channel.is_active,
            "created_at": channel.created_at.isoformat() if channel.created_at else None,
        }

    def send_message(
        self,
        proxy_channel_id: int,
        content: str,
        direction: str = "outbound",
    ) -> dict:
        message = ProxyMessage(
            proxy_channel_id=proxy_channel_id,
            content=content,
            direction=direction,
            sent_at=datetime.now(timezone.utc),
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return {
            "message_id": message.id,
            "proxy_channel_id": proxy_channel_id,
            "content": content,
            "direction": direction,
            "sent_at": message.sent_at.isoformat() if message.sent_at else None,
        }

    def log_call(
        self,
        proxy_channel_id: int,
        direction: str,
        duration: Optional[int] = None,
        status: str = "completed",
    ) -> dict:
        call_log = ProxyCallLog(
            proxy_channel_id=proxy_channel_id,
            direction=direction,
            duration=duration,
            status=status,
            called_at=datetime.now(timezone.utc),
        )
        self.db.add(call_log)
        self.db.commit()
        self.db.refresh(call_log)

        return {
            "call_id": call_log.id,
            "proxy_channel_id": proxy_channel_id,
            "direction": direction,
            "duration": duration,
            "status": status,
            "called_at": call_log.called_at.isoformat() if call_log.called_at else None,
        }


def get_external_contact_service(db: Session) -> ExternalContactService:
    return ExternalContactService(db)
