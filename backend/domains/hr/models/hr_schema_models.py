"""hr-schema ORM models that were historically defined inside the accounts
God-domain (``domains.governance.models.core``) but belong to the ``hr`` bounded
context.

A3 (RESOLVER.md §26 ACC-01): re-home non-``accounts`` tables out of
``domains/accounts/models`` into their owning domain. ``shift_handover_tasks``
lives under the ``hr`` schema, so its canonical definition now resides here.
``domains.governance.models.core`` keeps a re-export so legacy imports keep
resolving (no-delete rule).
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class ShiftHandoverTask(Base):
    __tablename__ = "shift_handover_tasks"
    __table_args__ = ({"extend_existing": True, "schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("customer.shift_handover_sessions.id"), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")
    status = Column(String(20), default="open")
    assigned_to = Column(Integer, ForeignKey("accounts.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    session = relationship("ShiftHandoverSession", back_populates="tasks")


class OnboardingPipeline(Base):
    __tablename__ = "onboarding_pipelines"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False, index=True)
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


__all__ = ["ShiftHandoverTask", "OnboardingPipeline", "OnboardingStep"]
