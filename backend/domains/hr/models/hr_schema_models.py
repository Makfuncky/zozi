"""hr-schema ORM models.

A3 (RESOLVER.md §26 ACC-01): re-home non-``accounts`` tables out of
``domains/accounts/models`` into their owning domain.

OnboardingPipeline / OnboardingStep: canonical definitions live in
``domains.accounts.models.onboarding`` (Law 6: onboarding pipelines are an
accounts lifecycle concept that happens to live in the ``hr`` schema). This
module re-exports them so legacy imports keep resolving.
ShiftHandoverTask: also defined in ``domains.hr.models.employee_models`` (the
version used by the HR service layer). This module uses ``extend_existing=True``
so both registration sites share the same MetaData entry.
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


# ── Re-export OnboardingPipeline / OnboardingStep from accounts (canonical) ──
from domains.accounts.models.onboarding import (  # noqa: F401
    OnboardingPipeline,
    OnboardingStep,
)


# ── ShiftHandoverTask (also defined in employee_models.py) ───────────────────
class ShiftHandoverTask(Base):
    __tablename__ = "shift_handover_tasks"
    __table_args__ = ({"extend_existing": True, "schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("customer.shift_handover_sessions.id"), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")
    status_code = Column(String(20), default="open")
    assigned_to = Column(Integer, ForeignKey("accounts.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    session = relationship("ShiftHandoverSession", back_populates="tasks")


__all__ = ["ShiftHandoverTask", "OnboardingPipeline", "OnboardingStep"]
