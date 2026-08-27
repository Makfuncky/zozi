"""Isolated unit tests for the treasury module import surface.

These deliberately avoid importing ``main`` or building a live DB schema, so
they keep working even when an unrelated module (e.g. the missing
``services.security.auth_write_service`` used by ``auth_controller``) breaks the rest of
the app. They validate that:

  * ``routers.public_treasury_api_access`` exposes the four query functions that
    ``routers.public_treasury_access`` depends on (regression guard for the W1 relocation
    bug where ``treasury_api`` was moved into ``services.treasury`` but the
    router import was never updated).
  * ``scripts.maintenance.write_helpers`` provides the session helpers consumed by the
    treasury service layer.

The DB session is a MagicMock, so no real database or model metadata is needed.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest


def test_treasury_api_reexports_resolve():
    from modules.admin.routers.public_treasury_api_access import (
        get_cash_position,
        get_supplier_payables,
        get_treasury_metrics,
        get_vat_liability,
    )

    assert callable(get_treasury_metrics)
    assert callable(get_cash_position)
    assert callable(get_vat_liability)
    assert callable(get_supplier_payables)


def test_write_helpers_roundtrip():
    from sqlalchemy.orm import Session

    from infrastructure.utils.write_helpers import (
        add_and_flush,
        commit_and_refresh,
        commit_only,
    )

    db = MagicMock(spec=Session)
    obj = object()
    assert add_and_flush(db, obj) is obj
    db.add.assert_called_once_with(obj)
    db.flush.assert_called_once()

    obj2 = object()
    assert commit_and_refresh(db, obj2) is obj2
    db.commit.assert_called()
    db.refresh.assert_called_once_with(obj2)

    commit_only(db)
    # commit called again (refresh not)
    db.refresh.assert_called_once()


def test_treasury_metrics_runs_with_mocked_session():
    """Smoke-test that get_treasury_metrics executes against a mock session
    without raising (proves the function body + its imports are wired)."""
    from modules.admin.routers.public_treasury_api_access import get_treasury_metrics

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.scalar.return_value = Decimal("0")

    result = get_treasury_metrics(db)
    assert isinstance(result, dict)
