"""Social (OAuth/OIDC) identity links for the accounts domain."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.types import JSON

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


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
