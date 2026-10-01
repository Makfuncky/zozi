"""GDPR / privacy consent tracking for the accounts domain.

Every consent grant or revocation by a user is recorded here for audit
and to support right-to-erasure / right-to-be-informed requests.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, func

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class UserConsent(Base):
    """A single grant or revocation of a specific consent type.

    One row per state-change; historical grants are retained (do not
    delete on revoke) so the consent trail is auditable.
    """

    __tablename__ = "user_consents"
    __table_args__ = (
        Index("ix_user_consents_user_id", "user_id"),
        Index("ix_user_consents_consent_type", "consent_type"),
        {"schema": "accounts"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("accounts.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    consent_type = Column(String(64), nullable=False)
    granted = Column(Boolean, nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    consent_version = Column(String(32), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    is_deleted = Column(Boolean, nullable=False, default=False)
