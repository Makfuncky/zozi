"""OTP / MFA challenge store for the accounts domain."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class OtpCode(Base):
    """A short-lived one-time challenge code (email/SMS) or TOTP challenge record."""

    __tablename__ = "otp_codes"
    __table_args__ = ({"schema": "accounts"},)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False, index=True)
    purpose = Column(String(32), nullable=False)  # login | register | password_reset | device_trust
    channel = Column(String(16), nullable=False, default="email")  # email | sms
    destination = Column(String(320), nullable=True)
    code_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='RESTRICT'), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
