"""Multi-factor authentication factor enrollment for the accounts domain.

One user may have multiple factors enrolled (TOTP, SMS, email, biometric).
``secret`` is the field-encrypted TOTP seed or the SMS-delivered challenge
key — never stored in plaintext.
"""
from __future__ import annotations

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.types import JSON

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class MfaFactorType(str, enum.Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BIOMETRIC = "biometric"


class MfaFactor(Base):
    """An enrolled second factor for a user."""

    __tablename__ = "mfa_factors"
    __table_args__ = (
        Index("ix_mfa_factors_user_id", "user_id"),
        Index("ix_mfa_factors_factor_type", "factor_type"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    factor_type = Column(
        Enum(MfaFactorType, name="mfa_factor_type", schema="accounts"),
        nullable=False,
    )
    secret = Column(String(512), nullable=False)  # field-encrypted via infrastructure.security
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    backup_codes = Column(JSON, nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    is_deleted = Column(Boolean, nullable=False, default=False)
