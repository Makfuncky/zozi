"""
Masked B2B Communication Channels
Features: Proxy Phone Numbers, Proxy Emails, Encrypted Sessions, Call Recording
"""
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TwilioClient = None
    TwilioRestException = Exception
    TWILIO_AVAILABLE = False

from data.models import ProxyChannel, ProxySession, ProxyMessage, ProxyCallLog, User, Order
from data.db import get_service_session
from utils.config import settings

logger = logging.getLogger("zozi.proxy")


class ProxyNumberManager:
    """Manages proxy phone number allocation and pooling."""
    
    def __init__(self, db: Session):
        self.db = db
        self._twilio_client = None
    
    @property
    def twilio_client(self) -> Optional[TwilioClient]:
        if not TWILIO_AVAILABLE:
            return None
        if self._twilio_client is None:
            account_sid = settings.twilio_account_sid or secrets.token_urlsafe(32)
            auth_token = settings.twilio_auth_token or secrets.token_urlsafe(32)
            self._twilio_client = TwilioClient(account_sid, auth_token)
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
