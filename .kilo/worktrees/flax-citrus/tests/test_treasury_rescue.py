"""Treasury module rescue tests.

Verifies the architectural fixes applied to the ``treasury`` bounded context:
  * BC3  - services no longer import legacy ``models.<domain>`` paths directly
           (they go through the canonical ``data.models`` layer).
  * W4   - ``admin_controller`` no longer imports a controller (controller->controller).
  * CIR2 - treasury routers delegate to controller facades, not services directly.
  * A functional smoke test of ``TreasuryEngine.run_orphan_detector`` (the code
    path that previously reached into ``models.orders``).
"""
from __future__ import annotations

from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"


def _read(rel: str) -> str:
    return (BACKEND / rel).read_text(encoding="utf-8")


def test_bc3_treasury_engine_no_legacy_orders_import():
    src = _read("services/treasury/treasury_engine.py")
    assert "from models.orders import" not in src, "treasury_engine still imports legacy models.orders"
    assert "from data.models import" in src


def test_bc3_ediscovery_no_legacy_treasury_import():
    src = _read("services/audit/ediscovery.py")
    assert "from models.treasury.finance import" not in src, "ediscovery still imports legacy models.treasury.finance"
    assert "from data.models import JournalEntry" in src


def test_treasury_controller_facades_expose_functions():
    from controllers.treasury import (
        cash_write_controller,
        auto_payout_controller,
        payout_admin_controller,
        payout_approval_controller,
        treasury_metrics_controller,
    )
    assert hasattr(cash_write_controller, "list_cash_accounts")
    assert hasattr(auto_payout_controller, "run_auto_payout_sweep")
    assert hasattr(payout_admin_controller, "query_pending_payouts")
    assert hasattr(payout_approval_controller, "approve_batch")
    assert hasattr(treasury_metrics_controller, "get_treasury_metrics")

    from controllers.finance import treasury_query_controller
    assert hasattr(treasury_query_controller, "calculate_eosb")


def test_w4_admin_controller_not_controller_to_controller():
    src = _read("controllers/admin_controller.py")
    assert "from controllers.treasury.admin_payouts_controller import" not in src, \
        "admin_controller still imports a controller (controller->controller leak)"
    assert "from services.treasury.payout_admin_service import" in src


def test_cir2_routers_delegate_to_controllers():
    expected = {
        "routers/admin_treasury_routes.py": "controllers.treasury.cash_write_controller",
        "routers/admin_treasury_routes_2.py": "controllers.treasury.auto_payout_controller",
        "routers/admin_treasury_routes_3.py": "controllers.treasury.payout_approval_controller",
        "routers/api_treasury_approval.py": "controllers.treasury.payout_approval_controller",
        "routers/api_treasury_routes.py": "controllers.treasury.payout_approval_controller",
        "routers/api_treasury_routes_2.py": "controllers.treasury.treasury_metrics_controller",
        "routers/api_treasury_accounting.py": "controllers.treasury.treasury_query_controller",
    }
    for router_rel, controller_mod in expected.items():
        src = _read(router_rel)
        assert f"from {controller_mod} import" in src, f"{router_rel} does not import {controller_mod}"
        # The legacy direct service import for the treasury call must be gone.
        assert "from services.treasury.treasury_router_service import" not in src, \
            f"{router_rel} still imports the treasury service directly (CIR2)"
        assert "from services.treasury.treasury_service import" not in src, \
            f"{router_rel} still imports treasury_service directly (CIR2)"


def test_treasury_engine_orphan_detector_runs(db_session):
    """Exercise the previously-leaky code path now routed via data.models."""
    from services.treasury.treasury_engine import TreasuryEngine

    engine = TreasuryEngine(db_session)
    alerts = engine.run_orphan_detector()
    assert isinstance(alerts, list)


def test_verify_payout_relocated_to_service():
    from services.treasury import payout_admin_service

    assert hasattr(payout_admin_service, "verify_payout")
    assert hasattr(payout_admin_service, "list_pending_payouts")
