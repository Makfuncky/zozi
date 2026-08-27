"""Refresh token family tracking for the accounts domain.

Detects refresh token reuse — when a previously-rotated token is presented
again, every family member is revoked and the incident is recorded here.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, TypeDecorator

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class GUID(TypeDecorator):
    """Cross-dialect UUID column (PostgreSQL UUID, else CHAR(32))."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        if dialect.name == "postgresql":
            return value
        return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class RefreshTokenFamily(Base):
    """A chain of refresh tokens issued for a single login session.

    Rotation: when a refresh token is exchanged for a new one, the new
    refresh token is recorded as a new row in the same family. If an old
    token is ever reused, ``reused_at`` is stamped and the family is
    revoked (every row gets ``revoked_at``).
    """

    __tablename__ = "refresh_token_families"
    __table_args__ = (
        Index("ix_refresh_token_families_user_id", "user_id"),
        Index("ix_refresh_token_families_family_id", "family_id"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id = Column(GUID(), nullable=False, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    reused_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(512), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
