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
    # TODO(migration): governance.users is a cross-domain FK (Law 3). After the User
    # model is migrated into the accounts domain, this must become ``accounts.users.id``.
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False, index=True)
    purpose = Column(String(32), nullable=False)  # login | register | password_reset | device_trust
    channel = Column(String(16), nullable=False, default="email")  # email | sms
    # destination is the address the OTP was delivered to — required to deliver/verify.
    destination = Column(String(320), nullable=False)
    # Indexed for the verify-lookup path (SELECT … WHERE code_hash = ?).
    code_hash = Column(String, nullable=False, index=True)
    # Indexed for the cleanup job (DELETE … WHERE expires_at < now()).
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    attempts = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    # Cross-domain FK to the country domain — Law #5 says country is the orthogonal
    # scope axis; the ``country.country_configs`` row is the canonical reference.
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='RESTRICT'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
