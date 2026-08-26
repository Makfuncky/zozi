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


# Lazy-loaded cross-domain models (Law 3: avoid direct cross-domain model imports at module level)
_LAZY_CROSS_DOMAIN_MODELS: dict[str, tuple[str, str]] = {
    "OnboardingPipeline": ("domains.accounts.models.onboarding", "OnboardingPipeline"),
    "OnboardingStep": ("domains.accounts.models.onboarding", "OnboardingStep"),
}
_IMPORTED_CROSS_DOMAIN: dict[str, object] = {}


def _get_cross_domain_model(name: str):
    """Lazily import a cross-domain model to avoid import-time coupling."""
    if name in _IMPORTED_CROSS_DOMAIN:
        return _IMPORTED_CROSS_DOMAIN[name]
    if name in _LAZY_CROSS_DOMAIN_MODELS:
        module_path, class_name = _LAZY_CROSS_DOMAIN_MODELS[name]
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        _IMPORTED_CROSS_DOMAIN[name] = cls
        return cls
    raise AttributeError(f"Cross-domain model {name!r} not registered")


def __getattr__(name: str):
    """Module-level lazy resolver for cross-domain models (Law 3)."""
    try:
        return _get_cross_domain_model(name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
