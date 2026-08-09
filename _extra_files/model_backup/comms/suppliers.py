from __future__ import annotations
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index, JSON, CheckConstraint, text
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as utcnow
from ..mixins import TenantMixin
from db.mixins import VersionMixin

__all__ = ["SupplierProfile", "SupplierDocument", "SupplierNotificationPreference"]

class SupplierProfile(Base, TenantMixin):
    __tablename__ = "supplier_profiles"
    __table_args__ = (
        CheckConstraint("verification_status IN ('pending', 'documents_submitted', 'under_review', 'approved', 'rejected')", name="chk_supplier_verification_status_valid"),
        CheckConstraint("business_type IN ('retailer', 'wholesaler', 'manufacturer', 'distributor', 'service_provider', 'individual')", name="chk_supplier_business_type_valid"), {"schema": "supplier"})
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    business_name = Column(String, nullable=False, default="")
    slug = Column(String, unique=True, index=True)
    business_type = Column(String, nullable=True)

    website = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    region = Column(String, nullable=True)
    is_terms_accepted = Column(Boolean, default=False)
    terms_version = Column(String, nullable=True)
    verification_status = Column(String, default="pending")
    verified_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, nullable=True)

    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    bio = Column(Text, nullable=True)
    about_us = Column(Text, nullable=True)
    postal_code = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    banner_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    certifications = Column(JSON, nullable=True)
    social_links_json = Column(JSON, nullable=True)
    established_year = Column(Integer, nullable=True)
    operating_regions = Column(JSON, nullable=True)
    verified_documents = Column(JSON, nullable=True)
    document_expires_at = Column(DateTime, nullable=True)
    terms_accepted_at = Column(DateTime, nullable=True)
    badge_level = Column(String, nullable=True)
    credibility_score = Column(Integer, nullable=True)
    badge_granted_at = Column(DateTime, nullable=True)
    country_code = Column(String(3), nullable=True)

    country = relationship("CountryConfig", foreign_keys="SupplierProfile.country_code", primaryjoin="foreign(SupplierProfile.country_code) == CountryConfig.code")
    documents = relationship("SupplierDocument", back_populates="supplier", cascade="all, delete-orphan")

class SupplierDocument(VersionMixin, Base):
    __tablename__ = "supplier_documents"
    __table_args__ = ({"schema": "supplier"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("supplier.supplier_profiles.id", ondelete="RESTRICT"), nullable=False, index=True)
    doc_type = Column(String, nullable=False)
    document_name = Column(String, nullable=True)
    file_url = Column(String, nullable=False)
    status = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, nullable=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    supplier = relationship("SupplierProfile", back_populates="documents")
    verifier = relationship("User", primaryjoin="foreign(SupplierDocument.verified_by) == User.id")
    reviewer = relationship("User", primaryjoin="foreign(SupplierDocument.reviewed_by) == User.id")

class SupplierNotificationPreference(Base, TenantMixin):
    __tablename__ = "supplier_notification_preferences"
    __table_args__ = ({"schema": "supplier"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("supplier.supplier_profiles.id", ondelete="RESTRICT"), nullable=False, index=True)
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

# DBA09: GIN expression index for JSON/JSONB column(s)
Index("ix_supplier_profiles_certifications", text("(certifications::jsonb)"), postgresql_using="gin")
Index("ix_supplier_profiles_social_links_json", text("(social_links_json::jsonb)"), postgresql_using="gin")
Index("ix_supplier_profiles_operating_regions", text("(operating_regions::jsonb)"), postgresql_using="gin")
Index("ix_supplier_profiles_verified_documents", text("(verified_documents::jsonb)"), postgresql_using="gin")
