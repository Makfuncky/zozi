from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = [
    "PermissionCategory",
    "Permission",
    "RolePermissionAssignment",
    "UserPermissionOverride",
    "PermissionAuditLog",
]


class PermissionCategory(Base):
    __tablename__ = "permission_categories"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    country_code = Column(String(10), nullable=False, server_default="OM")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    permissions = relationship("Permission", back_populates="category", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("permission_categories.id"), nullable=False)
    name = Column(String(150), nullable=False)
    slug = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    scope = Column(String(20), nullable=False, server_default="global")
    is_active = Column(Boolean, default=True)
    country_code = Column(String(10), nullable=False, server_default="OM")
    created_at = Column(DateTime, default=_utcnow)

    category = relationship("PermissionCategory", back_populates="permissions")


class RolePermissionAssignment(Base):
    __tablename__ = "role_permission_assignments"
    __table_args__ = (
        UniqueConstraint("role_name", "permission_id", "country_code", name="uq_role_permission_country"), {"schema": "core"})
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(80), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_granted = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class UserPermissionOverride(Base):
    __tablename__ = "user_permission_overrides"
    __table_args__ = (
        UniqueConstraint("user_id", "permission_id", "country_code", name="uq_user_perm_override_country"), {"schema": "core"})
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    is_granted = Column(Boolean, default=True)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class PermissionAuditLog(Base):
    __tablename__ = "permission_audit_log"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    target_role = Column(String(80), nullable=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=True)
    country_code = Column(String(10), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

