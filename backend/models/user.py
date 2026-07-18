"""User model for authentication and authorization."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow
from utils.encryption import EncryptedString

__all__ = [
    "User", "UserDevice", "Referral", "ReferralPointEvent",
    "PasswordResetToken", "EmailVerificationToken", "RevokedToken", "UserLoginHistory"
]


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_role", "role"),
    )
    
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
    referred_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    referral_points = Column(Integer, default=0)
    sharing_points = Column(Integer, default=0)
    totp_enabled = Column(Boolean, default=False)
    totp_secret = Column(String, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True, index=True)
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
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=_utcnow)
    success = Column(Boolean, default=True)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User")


class UserDevice(Base):
    __tablename__ = "user_devices"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=True)
    last_seen_at = Column(DateTime, default=_utcnow)
    is_current = Column(Boolean, default=True)
    is_trusted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User", back_populates="devices")


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_given")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referred_by")


class ReferralPointEvent(Base):
    __tablename__ = "referral_point_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(40), nullable=False)
    points = Column(Integer, nullable=False)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User", foreign_keys=[user_id])
    referred_user = relationship("User", foreign_keys=[referred_user_id])


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User")


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    user = relationship("User")
