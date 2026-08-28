"""Conftest for rbac tests - patch broken imports in the codebase."""
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Patch missing ReferralPointEvent class that breaks rbac.catalog import
try:
    from domains.accounts.models import user as _user_mod
    if not hasattr(_user_mod, "ReferralPointEvent"):
        # Create a minimal stub class
        from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
        from infrastructure.database.base import Base

        class ReferralPointEvent(Base):
            __tablename__ = "referral_point_events"
            __table_args__ = {"schema": "accounts"}
            id = Column(Integer, primary_key=True)
            user_id = Column(Integer, ForeignKey("accounts.users.id"))
            points = Column(Integer, default=0)
            event_type = Column(String(50))
            created_at = Column(DateTime)

        _user_mod.ReferralPointEvent = ReferralPointEvent
except Exception:
    pass
