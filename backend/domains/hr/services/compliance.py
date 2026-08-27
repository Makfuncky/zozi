"""HR compliance service wrapper.

Provides HR-domain access to the compliance engine owned by the audit domain.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.audit.services.compliance_engine import get_compliance_engine  # noqa: F401

__all__ = ["get_compliance_engine"]
