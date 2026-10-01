"""Per-user preference key-value store for the accounts domain.

Stores arbitrary JSON-encoded user settings (UI preferences, notification
toggles, locale overrides, etc.) keyed by ``(user_id, key)``.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.types import JSON

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class UserPreference(Base):
    """A single user preference setting."""

    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_user_preferences_user_key"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    key = Column(String(128), nullable=False)
    value = Column(JSON, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
