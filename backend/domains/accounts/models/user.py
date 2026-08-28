"""User model for accounts domain (canonical home per ARCHITECTURE_DIAGRAM.md §3).

Sibling models (UserSession, UserLoginHistory, UserDevice, PasswordResetToken,
EmailVerificationToken, RevokedToken) co-located here because they are tightly
coupled to the User aggregate.

NOTE: The governance domain still has copies at ``domains/governance/models/user.py``.
Those will be removed in a follow-up migration after all cross-domain references
are rewired. Do NOT use this module and the governance module from the same
request handler until then.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_accounts_users_email", "email"),
        Index("ix_accounts_users_country_code", "country_code"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="customer")
    # Law #5: country is the orthogonal scope axis — non-null on every row.
    country_code = Column(String(2), nullable=False, default="US")
    is_active = Column(Boolean, nullable=False, default=True)
    # JSON array of country codes for staff users; non-null but may be empty.
    staff_country_codes = Column(Text, nullable=True)
    referred_by_user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    is_deleted = Column(Boolean, nullable=False, default=False)

    # Relationships — back_populates are wired in the address/cart owning tables.
    addresses = relationship("Address", back_populates="user", lazy="selectin")
    cart = relationship("Cart", back_populates="user", uselist=False, lazy="selectin")
    cart_items = relationship("CartItem", back_populates="user", lazy="selectin")
    sessions = relationship("UserSession", back_populates="user", lazy="selectin", cascade="all, delete-orphan")
    login_history = relationship(
        "UserLoginHistory", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )
    devices = relationship("UserDevice", back_populates="user", lazy="selectin", cascade="all, delete-orphan")
    password_reset_tokens = relationship(
        "PasswordResetToken", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )
    email_verification_tokens = relationship(
        "EmailVerificationToken", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )
    revoked_tokens = relationship(
        "RevokedToken", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_accounts_user_sessions_user_id", "user_id"),
        Index("ix_accounts_user_sessions_token_jti", "token_jti"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_jti = Column(String(64), nullable=False)
    refresh_token_jti = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="sessions")


class UserLoginHistory(Base):
    __tablename__ = "user_login_histories"
    __table_args__ = (
        Index("ix_accounts_user_login_history_user_id", "user_id"),
        Index("ix_accounts_user_login_history_created", "created_at"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="login_history")


class UserDevice(Base):
    __tablename__ = "user_devices"
    __table_args__ = (
        Index("ix_accounts_user_devices_user_id", "user_id"),
        Index("ix_accounts_user_devices_fingerprint", "fingerprint_hash"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_fingerprint = Column(String(255), nullable=False)
    fingerprint_hash = Column(String(255), nullable=True)
    device_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="devices")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("ix_accounts_password_reset_tokens_user_id", "user_id"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="password_reset_tokens")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    __table_args__ = (
        Index("ix_accounts_email_verification_tokens_user_id", "user_id"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="email_verification_tokens")


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    __table_args__ = (
        Index("ix_accounts_revoked_tokens_user_id", "user_id"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="revoked_tokens")


__all__ = [
    "User",
    "UserSession",
    "UserLoginHistory",
    "UserDevice",
    "PasswordResetToken",
    "EmailVerificationToken",
    "RevokedToken",
]
