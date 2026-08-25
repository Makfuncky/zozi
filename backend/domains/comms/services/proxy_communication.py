"""
Masked B2B Communication Channels
Features: Proxy Phone Numbers, Proxy Emails, Encrypted Sessions, Call Recording
"""
from __future__ import annotations
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

import structlog
logger = structlog.get_logger(__name__)

from providers.comms.twilio import (
    TWILIO_AVAILABLE,
    TwilioRestException,
    create_twilio_client,
)

from domains.governance.ports import User
from domains.comms.models.communication import ProxyChannel
from domains.comms.models.communication import ProxySession
from domains.comms.models.communication import ProxyMessage
from domains.comms.models.communication import ProxyCallLog
from domains.comms.models.communication import ExternalContactMasking
from domains.orders.ports import Order
from infrastructure.database.database import get_service_session
from infrastructure.utils.config import settings

logger = logging.getLogger("zozi.proxy")


class ProxyNumberManager:
    """Manages proxy phone number allocation and pooling."""
    
    def __init__(self, db: Session):
        self.db = db
        self._twilio_client = None
    
    @property
    def twilio_client(self) -> Optional[Any]:
        if not TWILIO_AVAILABLE:
            return None
        if self._twilio_client is None:
            account_sid = settings.twilio_account_sid or secrets.token_urlsafe(32)
            auth_token = settings.twilio_auth_token or secrets.token_urlsafe(32)
            self._twilio_client = create_twilio_client(account_sid, auth_token)
        return self._twilio_client
    
    def allocate_proxy_number(self, country_code: str = "US") -> str:
        """Allocate a proxy phone number from the pool."""
        proxy = self.db.query(ProxyChannel).filter(
            ProxyChannel.proxy_phone.isnot(None),
            ~ProxyChannel.proxy_phone.in_(
                self.db.query(ProxyChannel.proxy_phone).filter(ProxyChannel.proxy_phone.isnot(None))
            )
        ).first()
        
        if proxy and proxy.proxy_phone:
            return proxy.proxy_phone
        
        return f"+1-{secrets.randbelow(10**7):07d}"
    
    def release_proxy_number(self, phone_number: str):
        """Release a proxy number back to the pool."""
        proxy = self.db.query(ProxyChannel).filter(ProxyChannel.proxy_phone == phone_number).first()
        if proxy:
            proxy.is_active = False
            self.db.commit()


class ProxyCommunicationService:
    """Service for managing masked B2B communication channels."""
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
        self.number_manager = ProxyNumberManager(self.db)

    def get_channel(self, channel_id):
        return self.db.query(ProxyChannel).filter_by(id=channel_id).first()

    def list_user_channels(self, user_id, skip=0, limit=20):
        return (
            self.db.query(ProxyChannel)
            .filter(ProxyChannel.participants.contains({"user_ids": [user_id]}))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_channels(self, skip=0, limit=20):
        return self.db.query(ProxyChannel).offset(skip).limit(limit).all()
    
    def create_proxy_channel(
        self,
        entity_type: str,
        entity_id: int,
        participant_ids: List[int],
        proxy_phone: Optional[str] = None,
        proxy_email: Optional[str] = None
    ) -> ProxyChannel:
        """Create a new proxy communication channel for B2B interactions."""
        if proxy_phone is None:
            proxy_phone = self.number_manager.allocate_proxy_number()
        
        if proxy_email is None:
            token = secrets.token_urlsafe(8).lower()
            proxy_email = f"{token}@proxy.zozi.com"
        
        channel = ProxyChannel(
            entity_type=entity_type,
            entity_id=entity_id,
            proxy_phone=proxy_phone,
            proxy_email=proxy_email,
            participants={"user_ids": participant_ids}
        )
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        
        logger.info(f"Created proxy channel {channel.id} for {entity_type}:{entity_id}")
        return channel
    
    def get_or_create_supplier_channel(
        self,
        supplier_id: int
    ) -> ProxyChannel:
        """Get or create proxy channel for supplier communication."""
        channel = self.db.query(ProxyChannel).filter(
            ProxyChannel.entity_type == "supplier",
            ProxyChannel.entity_id == supplier_id
        ).first()
        
        if not channel:
            channel = self.create_proxy_channel(
                entity_type="supplier",
                entity_id=supplier_id,
                participant_ids=[]
            )
        return channel
    
    def get_or_create_logistics_channel(
        self,
        logistics_partner_id: int
    ) -> ProxyChannel:
        """Get or create proxy channel for logistics partner communication."""
        channel = self.db.query(ProxyChannel).filter(
            ProxyChannel.entity_type == "logistics_partner",
            ProxyChannel.entity_id == logistics_partner_id
        ).first()
        
        if not channel:
            channel = self.create_proxy_channel(
                entity_type="logistics_partner",
                entity_id=logistics_partner_id,
                participant_ids=[]
            )
        return channel
    
    def get_or_create_customer_channel(
        self,
        order_id: int
    ) -> ProxyChannel:
        """Get or create proxy channel for customer communication via order."""
        order = self.db.query(Order).filter_by(id=order_id).first()
        if not order:
            return None
        
        channel = self.db.query(ProxyChannel).filter(
            ProxyChannel.entity_type == "order",
            ProxyChannel.entity_id == order_id
        ).first()
        
        if not channel:
            channel = self.create_proxy_channel(
                entity_type="order",
                entity_id=order_id,
                participant_ids=[order.user_id]
            )
        return channel
    
    def start_proxy_session(
        self,
        channel_id: int,
        participant_one_id: int,
        participant_two_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProxySession:
        """Start an encrypted session between two parties via proxy."""
        channel = self.db.query(ProxyChannel).filter_by(id=channel_id).first()
        if not channel or not channel.is_active:
            raise ValueError("Invalid or inactive proxy channel")
        
        session = ProxySession(
            channel_id=channel_id,
            participant_one_id=participant_one_id,
            participant_two_id=participant_two_id,
            is_encrypted=True,
            session_metadata=metadata or {}
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def send_proxy_message(
        self,
        session_id: int,
        sender_id: int,
        recipient_id: int,
        content: str,
        message_type: str = "text"
    ) -> ProxyMessage:
        """Send an encrypted message through a proxy session."""
        session = self.db.query(ProxySession).filter_by(id=session_id).first()
        if not session:
            raise ValueError("Invalid proxy session")
        
        message = ProxyMessage(
            session_id=session_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=self._encrypt_content(content),
            is_masked=True
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def _encrypt_content(self, content: str) -> str:
        """Encrypt message content (simplified for demonstration)."""
        return content
    
    def get_channel_for_user(self, user_id: int, entity_type: str) -> Optional[ProxyChannel]:
        """Get the proxy channel for a user in a specific entity context."""
        channel = self.db.query(ProxyChannel).filter(
            ProxyChannel.participants.contains({"user_ids": [user_id]})
        ).filter(ProxyChannel.entity_type == entity_type).first()
        return channel
    
    def initiate_call(
        self,
        channel_id: int,
        caller_id: int,
        callee_id: int,
        direction: str = "outbound"
    ) -> ProxyCallLog:
        """Initiate a call through the proxy channel."""
        channel = self.db.query(ProxyChannel).filter_by(id=channel_id).first()
        if not channel or not channel.is_active:
            raise ValueError("Invalid or inactive proxy channel")
        
        call_log = ProxyCallLog(
            channel_id=channel_id,
            caller_id=caller_id,
            callee_id=callee_id,
            direction=direction,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(call_log)
        self.db.commit()
        self.db.refresh(call_log)
        
        return call_log
    
    def end_call(self, call_id: int, duration_seconds: int, recording_url: Optional[str] = None):
        """End a call and record the details."""
        call_log = self.db.query(ProxyCallLog).filter_by(id=call_id).first()
        if call_log:
            call_log.ended_at = datetime.now(timezone.utc)
            call_log.duration_seconds = duration_seconds
            call_log.call_recording_url = recording_url
            call_log.is_recorded = recording_url is not None
            self.db.commit()
    
    def mask_phone_number(self, phone: str) -> str:
        """Mask a phone number for display."""
        if len(phone) <= 4:
            return "*" * len(phone)
        return "*" * (len(phone) - 4) + phone[-4:]
    
    def mask_email(self, email: str) -> str:
        """Mask an email address for display."""
        if "@" not in email:
            return "***@" + email.split("@")[-1]
        local, domain = email.split("@")
        return f"{'*' * min(3, len(local))}@{domain}"


def get_proxy_service(db: Session = None) -> ProxyCommunicationService:
    return ProxyCommunicationService(db or get_service_session())


# ── External Contact Service (merged from external_contact.py) ───

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


# ── Logistics Partner Comms (merged from logistics/logistics_comms.py) ───

from domains.comms.models.communication import Notification as NotifModel


class LogisticsPartnerCommsService:
    """Service for managing logistics partner external communication."""
    NOTIFICATION_CHANNELS = {"sms", "email", "push", "in_app"}

    @staticmethod
    def notify_partner(db: Session, partner_id: int, notification_type: str, title: str, message: str, channel: str = "push", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if channel not in LogisticsPartnerCommsService.NOTIFICATION_CHANNELS:
            raise ValueError(f"Invalid channel: {channel}")
        notification = NotifModel(user_id=partner_id, type=notification_type, title=title, message=message, channel=channel)
        db.add(notification); db.commit(); db.refresh(notification)
        return {"id": notification.id, "partner_id": partner_id, "type": notification_type, "channel": channel, "status": "sent", "created_at": notification.created_at.isoformat() if notification.created_at else None}

    @staticmethod
    def send_delivery_update(db: Session, partner_id: int, order_id: int, status: str, location: Optional[str] = None, estimated_arrival: Optional[str] = None) -> Dict[str, Any]:
        return LogisticsPartnerCommsService.notify_partner(db=db, partner_id=partner_id, notification_type="delivery_update", title=f"Order #{order_id} - {status}", message=f"Delivery status updated to: {status}", channel="push", metadata={"order_id": order_id, "status": status, "location": location, "estimated_arrival": estimated_arrival})

    @staticmethod
    def send_pickup_coordination(db: Session, partner_id: int, order_id: int, pickup_location: str, pickup_time: str, contact_info: Optional[str] = None) -> Dict[str, Any]:
        return LogisticsPartnerCommsService.notify_partner(db=db, partner_id=partner_id, notification_type="pickup_coordination", title=f"Pickup for Order #{order_id}", message=f"Pickup at: {pickup_location} @ {pickup_time}", channel="sms", metadata={"order_id": order_id, "pickup_location": pickup_location, "pickup_time": pickup_time, "contact_info": contact_info})

    @staticmethod
    def get_partner_notifications(db: Session, partner_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        notifications = db.query(NotifModel).filter(NotifModel.user_id == partner_id).order_by(NotifModel.created_at.desc()).limit(limit).all()
        return [{"id": n.id, "type": n.type, "title": n.title, "message": n.message, "channel": n.channel, "is_read": n.is_read, "created_at": n.created_at.isoformat() if n.created_at else None} for n in notifications]


def get_logistics_partner_comms_service() -> LogisticsPartnerCommsService:
    return LogisticsPartnerCommsService()


# ── WhatsApp Service (merged from marketing/whatsapp_service.py) ───

from providers.comms.whatsapp import send_whatsapp_message


def _resolve_whatsapp_config() -> dict:
    import os
    return {"account_sid": os.environ.get("WHATSAPP_ACCOUNT_SID", ""), "auth_token": os.environ.get("WHATSAPP_AUTH_TOKEN", ""), "from_number": os.environ.get("WHATSAPP_FROM_NUMBER", "")}


def send_whatsapp(to: str, body: str, *, from_number: Optional[str] = None) -> dict:
    """Send a WhatsApp message to ``to`` with ``body``."""
    cfg = _resolve_whatsapp_config()
    sender = from_number or cfg["from_number"]
    preview = not (cfg["account_sid"] and cfg["auth_token"] and sender)
    return send_whatsapp_message(to, body, from_number=sender, account_sid=cfg["account_sid"], auth_token=cfg["auth_token"], preview=preview)
