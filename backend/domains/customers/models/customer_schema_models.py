"""customers domain models — canonical home for customer-schema ORM entities.

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain reads happen only through
``ports.py``; models/ holds only this domain's own schema entities. The
``customer``-schema tables live here; tables whose canonical home is another
domain are imported only via ``customers.ports`` (never re-exported here).
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from infrastructure.database.base import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

__all__ = [
    "Referral",
    "ReferralPointEvent",
]


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (
        Index("ix_referrals_referrer", "referrer_id"),
        Index("ix_referrals_referred", "referred_id"),
        Index("ix_referrals_code", "referral_code"),
        {"schema": "customers"},
    )
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("governance.users.id", ondelete='SET NULL'), nullable=False)
    referred_id = Column(Integer, ForeignKey("governance.users.id", ondelete='SET NULL'), nullable=False, unique=True)
    referral_code = Column(String(64), unique=True, nullable=True)
    status = Column(String, default="pending")
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(2), nullable=True, index=True)

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_given")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referred_by")


class ReferralPointEvent(Base):
    __tablename__ = "referral_point_events"
    __table_args__ = (
        Index("ix_referral_point_events_user", "user_id"),
        Index("ix_referral_point_events_type", "event_type"),
        {"schema": "customers"},
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id", ondelete='SET NULL'), nullable=False)
    event_type = Column(String(40), nullable=False)
    points = Column(Integer, nullable=False)
    referred_user_id = Column(Integer, ForeignKey("governance.users.id", ondelete='SET NULL'), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(2), nullable=True, index=True)

    user = relationship("User", foreign_keys=[user_id])
    referred_user = relationship("User", foreign_keys=[referred_user_id])
