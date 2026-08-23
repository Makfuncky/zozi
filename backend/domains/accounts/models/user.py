"""User model for authentication and authorization."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow
from infrastructure.utils.encryption import EncryptedString

__all__ = [
    "User", "UserDevice", "Referral", "ReferralPointEvent",
    "PasswordResetToken", "EmailVerificationToken", "RevokedToken", "UserLoginHistory"
]


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_role", "role"), {"schema": "core"})
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=True)
    username = Column(String, unique=True, nullable=True)
    full_name = Column(String(160), nullable=True)
    hashed_password = Column(String)
    role = Column(String, default="customer")
    is_active = Column(Boolean, default=True)
    phone = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    preferred_language = Column(String, default="en")
    preferred_currency = Column(String(10), default="OMR")
    preferred_country = Column(String(10), default="OM")
    email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)
    staff_role_label = Column(String(120), nullable=True)
    staff_title = Column(String(120), nullable=True)
    staff_department = Column(String(120), nullable=True)
    staff_country_codes = Column(Text, nullable=True)
    staff_permissions = Column(Text, nullable=True)
    staff_area_of_operation = Column(Text, nullable=True)
    staff_hire_date = Column(DateTime, nullable=True)
    staff_experience_level = Column(String(50), nullable=True)
    staff_performance_summary = Column(Text, nullable=True)
    staff_assigned_tasks = Column(JSON, nullable=True)
    staff_assigned_projects = Column(JSON, nullable=True)
    staff_notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    referral_code = Column(String, unique=True, nullable=True, index=True)
    referred_by_user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    referral_points = Column(Integer, default=0)
    sharing_points = Column(Integer, default=0)
    totp_enabled = Column(Boolean, default=False)
    totp_secret = Column(String, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    country = relationship("CountryConfig", foreign_keys=[country_code])
    # Encrypted at-rest JSON store for the customer's saved delivery profile(s).
    address_book = Column(EncryptedString(length=4000), nullable=True)
    
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="supplier", cascade="all, delete-orphan")
    referrals_given = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer", cascade="all, delete-orphan")
    referred_by = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred", cascade="all, delete-orphan")
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    cart = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    wishlist_items = relationship("WishlistItem", back_populates="user", cascade="all, delete-orphan")
    wishlists = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")


class UserLoginHistory(Base):
    __tablename__ = "user_login_history"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=_utcnow)
    success = Column(Boolean, default=True)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User")


class UserDevice(Base):
    __tablename__ = "user_devices"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    device_id = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=True)
    last_seen_at = Column(DateTime, default=_utcnow)
    is_current = Column(Boolean, default=True)
    is_trusted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User", back_populates="devices")


# Referral / ReferralPointEvent: canonical home is domains.customers.models (schema=customer).
# Imported here so legacy ``from domains.accounts.models.user import Referral`` imports resolve.

from domains.customers.models.customer_schema_models import (  # noqa: F401
    Referral as Referral,
    ReferralPointEvent as ReferralPointEvent,
)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User")


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User")


class OtpCode(Base):
    """A short-lived one-time challenge code (email/SMS) or TOTP challenge record."""

    __tablename__ = "otp_codes"
    __table_args__ = ({"schema": "accounts"},)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False, index=True)
    purpose = Column(String(32), nullable=False)  # login | register | password_reset | device_trust
    channel = Column(String(16), nullable=False, default="email")  # email | sms
    destination = Column(String(320), nullable=True)
    code_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", foreign_keys=[user_id])

class SocialIdentity(Base):
    """A link between a local ``User`` and an external provider identity."""

    __tablename__ = "social_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_social_provider_account"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False, index=True)
    provider = Column(String(32), nullable=False)  # google | apple | facebook
    provider_user_id = Column(String(255), nullable=False)
    email = Column(String(320), nullable=True)
    full_name = Column(String(160), nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

