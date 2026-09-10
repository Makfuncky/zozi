from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Numeric, func
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

# Canonical home for the ``security`` schema (A3 / §26 ACC-01). Note: ``media``
# schema's ``OCRResult`` keeps a FK to ``security.document_verifications`` and a
# string-based relationship back to ``DocumentVerification``.

__all__ = ["AlertEscalationRule", "DocumentVerification", "KYCVerification"]


class AlertEscalationRule(Base):
    __tablename__ = "alert_escalation_rules"
    __table_args__ = ({"extend_existing": True, "schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")
    threshold_value = Column(Numeric(15, 2), nullable=True)
    current_tier = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class DocumentVerification(Base):
    __tablename__ = "document_verifications"
    __table_args__ = ({"extend_existing": True, "schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("hr.onboarding_pipelines.id", ondelete='CASCADE'), nullable=False, index=True)
    document_type = Column(String, nullable=False)
    document_data = Column(JSON, nullable=True)
    status = Column(String, default="pending")
    verified_at = Column(DateTime, nullable=True)
    verifier_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    pipeline = relationship("OnboardingPipeline", back_populates="documents")
    verifier = relationship("User")


class KYCVerification(Base):
    __tablename__ = "kyc_verifications"
    __table_args__ = ({"extend_existing": True, "schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False, index=True)
    status = Column(String, default="pending")
    provider = Column(String, nullable=True)
    verification_data = Column(JSON, nullable=True)
    document_types = Column(JSON, nullable=True)
    submitted_at = Column(DateTime, default=_utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

