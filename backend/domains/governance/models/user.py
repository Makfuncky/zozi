"""User model for governance domain."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="customer")
    country_code = Column(String(2))
    is_active = Column(Boolean, default=True)
    staff_country_codes = Column(Text)  # JSON array of country codes
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class UserLoginHistory(Base):
    __tablename__ = "user_login_history"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id"), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class UserDevice(Base):
    __tablename__ = "user_devices"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id"), nullable=False)
    device_fingerprint = Column(String(255), nullable=False)
    fingerprint_hash = Column(String(255))
    device_id = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime)


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime)


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, server_default=func.now())


class ReferralPointEvent(Base):
    __tablename__ = "referral_point_events"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id"), nullable=False)
    points = Column(Integer, default=0)
    event_type = Column(String(50))
    reference_id = Column(Integer)
    created_at = Column(DateTime)
