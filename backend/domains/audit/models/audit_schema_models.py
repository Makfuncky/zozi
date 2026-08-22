from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

# Canonical home for the ``audit`` schema (A3 / §26 ACC-01).

__all__ = ["AuditLog", "CommandCenterView"]


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = ({"schema": "audit"},)
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=True)
    username = Column(String, nullable=True)
    user_role = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class CommandCenterView(Base):
    __tablename__ = "command_center_views"
    __table_args__ = ({"schema": "audit"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    view_name = Column(String(100), nullable=False)
    config = Column(JSON, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
