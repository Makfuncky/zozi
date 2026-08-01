"""Canonical platform tables required by DB29.

These tables support platform-wide functionality:
- feature_flags: Feature toggle management
- worm_audit: Write-once audit trail for data integrity
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Index
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["FeatureFlag", "WormAudit"]


class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    __table_args__ = (
        Index("ix_feature_flags_key_active", "flag_key", "is_active"),
        {"schema": "configuration"},
    )
    id = Column(Integer, primary_key=True, index=True)
    flag_key = Column(String(100), nullable=False, unique=True)
    flag_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)
    enabled_for = Column(JSON, nullable=True)
    disabled_for = Column(JSON, nullable=True)
    rollout_percentage = Column(Integer, default=0)
    country_code = Column(String(3), nullable=True, index=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class WormAudit(Base):
    __tablename__ = "worm_audit"
    __table_args__ = (
        Index("ix_worm_audit_entity_action", "entity_type", "action"),
        Index("ix_worm_audit_timestamp", "timestamp"),
        {"schema": "audit"},
    )
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    actor_id = Column(Integer, nullable=True)
    actor_type = Column(String(50), nullable=True)
    country_code = Column(String(3), nullable=True, index=True)
    timestamp = Column(DateTime, default=_utcnow, nullable=False, index=True)
    payload_json = Column(JSON, nullable=True)
    signature = Column(String(255), nullable=True)
    is_valid = Column(Boolean, default=True)
    previous_state_hash = Column(String(255), nullable=True)
    new_state_hash = Column(String(255), nullable=True)