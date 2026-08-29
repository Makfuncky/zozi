"""Social (OAuth/OIDC) identity links for the accounts domain."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
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
    # TODO(migration): governance.users is a cross-domain FK (Law 3). After the User
    # model is migrated into the accounts domain, this must become ``accounts.users.id``.
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False, index=True)
    provider = Column(String(32), nullable=False)  # google | apple | facebook
    provider_user_id = Column(String(255), nullable=False)
    # Every supported provider (google | apple | facebook) returns an email — make
    # it required at the storage layer so the column can be trusted downstream.
    email = Column(String(320), nullable=False)
    full_name = Column(String(160), nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    # Law #5: country is the orthogonal scope axis — must be non-null on every row.
    country_code = Column(String(2), nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
