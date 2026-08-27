from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index, JSON, LargeBinary, Numeric, func
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

# DocumentVerification and KYCVerification are canonical in security domain.
# Use the security ports surface (Law 3: cross-domain reads via owning domain).
from domains.security.ports import DocumentVerification, KYCVerification

__all__ = ["OnboardingPipeline", "OnboardingStep", "DocumentVerification", "OCRResult", "KYCVerification"]


class OnboardingPipeline(Base):
    __tablename__ = "onboarding_pipelines"
    __table_args__ = ({"schema": "accounts"},)
    id = Column(Integer, primary_key=True, index=True)
    # TODO(migration): governance.users is a cross-domain FK (Law 3). After the User
    # model is migrated into the accounts domain, this must become ``accounts.users.id``.
    user_id = Column(Integer, ForeignKey("governance.users.id", ondelete='SET NULL'), nullable=False, index=True)
    pipeline_type = Column(String(50), nullable=False)
    pipeline_status = Column("status", String, default="pending")
    current_step = Column(Integer, default=0)
    steps_data = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    # Law #5: country is the orthogonal scope axis — must be non-null on every row.
    country_code = Column(String(2), nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    user = relationship("User")
    steps = relationship("OnboardingStep", back_populates="pipeline", cascade="all, delete-orphan")
    documents = relationship("DocumentVerification", back_populates="pipeline", cascade="all, delete-orphan")


class OnboardingStep(Base):
    __tablename__ = "onboarding_steps"
    __table_args__ = ({"schema": "accounts"},)
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("accounts.onboarding_pipelines.id", ondelete='CASCADE'), nullable=False, index=True)
    step_name = Column(String(255), nullable=False)
    step_status = Column("status", String, default="pending")
    data = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    # Law #5: country is the orthogonal scope axis — must be non-null on every row.
    country_code = Column(String(2), nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    pipeline = relationship("OnboardingPipeline", back_populates="steps")


class OCRResult(Base):
    __tablename__ = "ocr_results"
    __table_args__ = ({"schema": "accounts"},)
    id = Column(Integer, primary_key=True, index=True)
    # Cross-domain FK: document_verifications lives in the security domain. Law 3
    # says cross-domain writes flow through events and reads through ports; this
    # raw FK is a known migration target and must remain consistent with the
    # canonical ``security.document_verifications.id``.
    document_verification_id = Column(Integer, ForeignKey("security.document_verifications.id", ondelete='CASCADE'), nullable=False, unique=True, index=True)
    extracted_text = Column(Text, nullable=True)
    # Confidence is a 0.00–1.00 ratio; Numeric(4,2) is the right precision.
    confidence_score = Column(Numeric(4, 2), nullable=True)
    fields = Column(JSON, nullable=True)
    processed_at = Column(DateTime(timezone=True), default=_utcnow)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    # Law #5: country is the orthogonal scope axis — must be non-null on every row.
    country_code = Column(String(2), nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    document_verification = relationship("DocumentVerification", backref="ocr_result", uselist=False)

