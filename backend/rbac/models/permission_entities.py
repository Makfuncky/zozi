from __future__ import annotations
from uuid import uuid4
from sqlalchemy import func, UUID
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from infrastructure.database.base import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow
__all__ = ['PermissionCategory', 'Permission', 'RolePermissionAssignment', 'UserPermissionOverride', 'PermissionAuditLog']

class PermissionCategory(Base):
    __tablename__ = 'permission_categories'
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_permission_categories_country_created', 'country_code', 'created_at'), {'schema': 'security'})
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    country_code = Column(String(2), nullable=False, server_default='OM')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    permissions = relationship('Permission', back_populates='category', cascade='all, delete-orphan')

class Permission(Base):
    __tablename__ = 'permissions'
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_permissions_country_created', 'country_code', 'created_at'), {'schema': 'security'})
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey('security.permission_categories.id', ondelete='RESTRICT'), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    slug = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    scope = Column(String(20), nullable=False, server_default='global')
    is_active = Column(Boolean, default=True)
    country_code = Column(String(2), nullable=False, server_default='OM')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    category = relationship('PermissionCategory', back_populates='permissions')

class RolePermissionAssignment(Base):
    __tablename__ = 'role_permission_assignments'
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (UniqueConstraint('role_name', 'permission_id', 'country_code', name='uq_role_permission_country'), Index('ix_role_permission_assignments_country_created', 'country_code', 'created_at'), {'schema': 'security'})
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(80), nullable=False)
    permission_id = Column(Integer, ForeignKey('security.permissions.id', ondelete='RESTRICT'), nullable=False, index=True)
    country_code = Column(String(2), ForeignKey('country.country_configs.code', ondelete='RESTRICT'), nullable=True, index=True)
    granted_by = Column(Integer, ForeignKey('governance.users.id', ondelete='RESTRICT'), nullable=True, index=True)
    is_granted = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

class UserPermissionOverride(Base):
    __tablename__ = 'user_permission_overrides'
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (UniqueConstraint('user_id', 'permission_id', 'country_code', name='uq_user_perm_override_country'), Index('ix_user_permission_overrides_country_created', 'country_code', 'created_at'), {'schema': 'security'})
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('governance.users.id', ondelete='RESTRICT'), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey('security.permissions.id', ondelete='RESTRICT'), nullable=False, index=True)
    country_code = Column(String(2), ForeignKey('country.country_configs.code', ondelete='RESTRICT'), nullable=True, index=True)
    is_granted = Column(Boolean, default=True)
    granted_by = Column(Integer, ForeignKey('governance.users.id', ondelete='RESTRICT'), nullable=True, index=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

class PermissionAuditLog(Base):
    __tablename__ = 'permission_audit_log'
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_permission_audit_log_country_created', 'country_code', 'created_at'), {'schema': 'security'})
    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey('governance.users.id', ondelete='RESTRICT'), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    target_user_id = Column(Integer, ForeignKey('governance.users.id', ondelete='RESTRICT'), nullable=True, index=True)
    target_role = Column(String(80), nullable=True)
    permission_id = Column(Integer, ForeignKey('security.permissions.id', ondelete='RESTRICT'), nullable=True, index=True)
    country_code = Column(String(2), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
