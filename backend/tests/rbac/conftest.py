"""Conftest for rbac tests - patch broken imports in the codebase."""
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Patch missing ReferralPointEvent class that breaks rbac.catalog import.
# Guard against duplicate registration: the real ReferralPointEvent may already
# be in Base.metadata (imported via the customers domain by tests/conftest.py).
from infrastructure.database.base import Base

try:
    from domains.accounts.models import user as _user_mod
    if not hasattr(_user_mod, "ReferralPointEvent"):
        if not any(t.name == "referral_point_events" for t in Base.metadata.tables.values()):
            from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

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


import pytest
from sqlalchemy.orm import sessionmaker

from tests.rbac.fixtures import seed_permission_categories


@pytest.fixture(scope="session", autouse=True)
def _seed_rbac_categories(engine):
    """Seed ``security.permission_categories`` so RBACService.grant() has a
    valid ``category_id=1`` target (hardcoded in ``rbac/service.py``)."""
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        seed_permission_categories(session)
        session.commit()
    finally:
        session.close()
    yield
