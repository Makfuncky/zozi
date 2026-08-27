from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, func
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

# Canonical home for the ``audit`` schema (A3 / §26 ACC-01).

__all__ = ["AuditLog", "CommandCenterView"]


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = ({"extend_existing": True, "schema": "audit"},)
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True)
    username = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class CommandCenterView(Base):
    __tablename__ = "command_center_views"
    __table_args__ = ({"extend_existing": True, "schema": "audit"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    view_name = Column(String(100), nullable=False)
    config = Column(JSON, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
