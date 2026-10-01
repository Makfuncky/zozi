"""Historical password hash storage for PCI-DSS reuse prevention.

The last N password hashes for each user are retained so a password-change
endpoint can reject any new password that hashes to a value already in this
table.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, func

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class PasswordHistory(Base):
    """One historical password hash entry per user."""

    __tablename__ = "password_histories"
    __table_args__ = (
        Index("ix_password_histories_user_id", "user_id"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    country_code = Column(String(2), nullable=True, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    is_deleted = Column(Boolean, nullable=False, default=False)
