from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index, JSON, LargeBinary
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["OnboardingPipeline", "OnboardingStep", "DocumentVerification", "OCRResult", "KYCVerification"]


class OnboardingPipeline(Base):
    __tablename__ = "onboarding_pipelines"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    pipeline_type = Column(String, nullable=False)
    status = Column(String, default="pending")
    current_step = Column(Integer, default=0)
    steps_data = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)
    user = relationship("User")
    steps = relationship("OnboardingStep", back_populates="pipeline", cascade="all, delete-orphan")
    documents = relationship("DocumentVerification", back_populates="pipeline", cascade="all, delete-orphan")


class OnboardingStep(Base):
    __tablename__ = "onboarding_steps"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("hr.onboarding_pipelines.id"), nullable=False)
    step_name = Column(String, nullable=False)
    status = Column(String, default="pending")
    data = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)
    pipeline = relationship("OnboardingPipeline", back_populates="steps")


class DocumentVerification(Base):
    __tablename__ = "document_verifications"
    __table_args__ = ({"schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("hr.onboarding_pipelines.id"), nullable=False)
    document_type = Column(String, nullable=False)
    document_data = Column(JSON, nullable=True)
    status = Column(String, default="pending")
    verified_at = Column(DateTime, nullable=True)
    verifier_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    pipeline = relationship("OnboardingPipeline", back_populates="documents")
    verifier = relationship("User")


class OCRResult(Base):
    __tablename__ = "ocr_results"
    __table_args__ = ({"schema": "media"},)
    id = Column(Integer, primary_key=True, index=True)
    document_verification_id = Column(Integer, ForeignKey("security.document_verifications.id"), nullable=False, unique=True)
    extracted_text = Column(Text, nullable=True)
    confidence_score = Column(String, nullable=True)
    fields = Column(JSON, nullable=True)
    processed_at = Column(DateTime, default=_utcnow)
    document_verification = relationship("DocumentVerification", backref="ocr_result", uselist=False)


class KYCVerification(Base):
    __tablename__ = "kyc_verifications"
    __table_args__ = ({"schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    status = Column(String, default="pending")
    provider = Column(String, nullable=True)
    verification_data = Column(JSON, nullable=True)
    document_types = Column(JSON, nullable=True)
    submitted_at = Column(DateTime, default=_utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
