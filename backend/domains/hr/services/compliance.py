"""HR compliance service wrapper.

Provides HR-domain access to the compliance engine owned by the audit domain.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.audit.ports import get_compliance_engine

__all__ = ["get_compliance_engine"]
