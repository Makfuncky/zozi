from __future__ import annotations
from uuid import uuid4
from decimal import Decimal
from sqlalchemy import func, UUID
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index, JSON, CheckConstraint, text, Numeric, Float
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as utcnow
from ..mixins import TenantMixin
from models.mixins import VersionMixin
__all__ = ['SupplierProfile', 'SupplierDocument', 'SupplierNotificationPreference',
           'SupplierBadgeCatalog', 'SupplierBadge', 'SupplierBadgeBillingHistory']


class SupplierProfile(Base, TenantMixin):
    __tablename__ = 'supplier_profiles'
    __table_args__ = ({'schema': 'supplier'},)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('core.users.id', ondelete='RESTRICT'), nullable=False, index=True)
    business_name = Column(String(200), nullable=False)
    country_code = Column(String(3), nullable=True, index=True)
    address = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    about_us = Column(Text, nullable=True)
    business_type = Column(String(50), nullable=True)
    verified_documents = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_status = Column(String(30), default='unverified')
    credibility_score = Column(Numeric(5, 2), default=Decimal('0'))
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    user = relationship('User', foreign_keys=[user_id])


class SupplierDocument(Base, TenantMixin):
    __tablename__ = 'supplier_documents'
    __table_args__ = ({'schema': 'supplier'},)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey('supplier.supplier_profiles.id', ondelete='RESTRICT'), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False)
    document_name = Column(String(255), nullable=True)
    file_url = Column(String(500), nullable=False)
    status = Column(String(30), default='pending', nullable=True)
    expires_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    verified = Column(Boolean, default=False)
    verified_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    supplier = relationship('SupplierProfile', foreign_keys=[supplier_id])


class SupplierNotificationPreference(Base, TenantMixin):
    __tablename__ = 'supplier_notification_preferences'
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_supplier_notification_preferences_country_created', 'country_code', 'created_at'), {'schema': 'supplier'})
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey('supplier.supplier_profiles.id', ondelete='RESTRICT'), nullable=False, index=True)
    notify_new_order = Column(Boolean, default=True)
    notify_low_stock = Column(Boolean, default=True)
    notify_payout_processed = Column(Boolean, default=True)
    notify_doc_expiry = Column(Boolean, default=True)
    notify_return_updates = Column(Boolean, default=True)
    notify_dispute_updates = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class SupplierBadgeCatalog(Base):
    """Catalogue of badge levels a supplier can purchase/earn."""

    __tablename__ = 'supplier_badge_catalog'
    __table_args__ = (
        Index('ix_supplier_badge_catalog_country_created', 'country_code', 'created_at'),
        Index('ix_supplier_badge_catalog_benefits_gin', 'benefits', postgresql_using='gin'),
        {'schema': 'supplier'},
    )
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    badge_level = Column(String(30), nullable=False, default='bronze')
    description = Column(Text, nullable=True)
    benefits = Column(JSON, nullable=True)
    price = Column(Numeric(12, 2), nullable=False, default=Decimal('0'))
    currency = Column(String(3), nullable=False, default='USD')
    validity_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    credibility_weight = Column(Float, nullable=False, default=10.0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class SupplierBadge(Base):
    """A badge held by a supplier (purchased or admin-assigned)."""

    __tablename__ = 'supplier_badges'
    __table_args__ = (
        UniqueConstraint('supplier_id', 'catalog_id', name='uq_supplier_badge'),
        Index('ix_supplier_badges_country_created', 'country_code', 'created_at'),
        {'schema': 'supplier'},
    )
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey('supplier.supplier_profiles.id', ondelete='RESTRICT'), nullable=False, index=True)
    catalog_id = Column(Integer, ForeignKey('supplier.supplier_badge_catalog.id', ondelete='RESTRICT'), nullable=True, index=True)
    badge_name = Column(String(100), nullable=False)
    badge_level = Column(String(30), nullable=False, default='bronze')
    status = Column(String(20), nullable=False, default='active')
    issued_at = Column(DateTime, default=utcnow)
    expires_at = Column(DateTime, nullable=True)
    assigned_by = Column(Integer, nullable=True, index=True)
    billing_reference = Column(String(120), nullable=True)
    credibility_weight = Column(Float, nullable=False, default=10.0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    supplier = relationship('SupplierProfile', foreign_keys=[supplier_id])
    catalog = relationship('SupplierBadgeCatalog', foreign_keys=[catalog_id])


class SupplierBadgeBillingHistory(Base):
    """Billing events generated when a supplier purchases a badge."""

    __tablename__ = 'supplier_badge_billing_history'
    __table_args__ = (
        Index('ix_supplier_badge_billing_country_created', 'country_code', 'created_at'),
        {'schema': 'supplier'},
    )
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey('supplier.supplier_profiles.id', ondelete='RESTRICT'), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey('supplier.supplier_badges.id', ondelete='RESTRICT'), nullable=True, index=True)
    catalog_id = Column(Integer, ForeignKey('supplier.supplier_badge_catalog.id', ondelete='RESTRICT'), nullable=True, index=True)
    billing_reference = Column(String(120), unique=True, nullable=True)
    charge_type = Column(String(30), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False, default=Decimal('0'))
    currency = Column(String(3), nullable=False, default='USD')
    status = Column(String(20), nullable=False, default='pending')
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)
    billed_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    payment_method = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    supplier = relationship('SupplierProfile', foreign_keys=[supplier_id])
Index('ix_supplier_profiles_certifications', text('(certifications::jsonb)'), postgresql_using='gin')
Index('ix_supplier_profiles_social_links_json', text('(social_links_json::jsonb)'), postgresql_using='gin')
Index('ix_supplier_profiles_operating_regions', text('(operating_regions::jsonb)'), postgresql_using='gin')
Index('ix_supplier_profiles_verified_documents', text('(verified_documents::jsonb)'), postgresql_using='gin')
