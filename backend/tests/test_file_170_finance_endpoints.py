"""Regression test for FILE 170: verify finance endpoint state after deletion of non-canonical modules/finance/.

Block FILE 170 claimed:
  - 4 finance endpoints permanently deleted with no replacement
  - app boots 738 paths identically before and after
  - CONTRAD-001 exists

Evidence shows:
  - Route count is 85, not 738
  - CONTRAD-001 does NOT exist in _audit/07_CONTRADICTIONS.md
  - admin_financial_summary was migrated to modules/employee/routers/finance.py
  - get_cash_flow_report, get_payment_health, get_revenue_metrics never existed
  - backend/modules/finance/ was a non-canonical module (Law 13 violation)
"""
from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_route_count_is_85_not_738():
    route_count = len(app.routes)
    assert route_count == 85, (
        f"Block FILE 170 claims 738 routes; actual is {route_count}"
    )


def test_admin_financial_summary_route_exists():
    resp = client.get("/api/v1/employee/finance/admin/summary")
    assert resp.status_code != 404, (
        "admin_financial_summary was migrated to modules/employee/routers/finance.py "
        "but route is not reachable"
    )


def test_get_cash_flow_report_returns_404():
    resp = client.get("/api/v1/admin/finance/cash-flow-report")
    assert resp.status_code == 404, (
        "get_cash_flow_report never existed in the codebase; 404 expected"
    )


def test_get_payment_health_returns_404():
    resp = client.get("/api/v1/admin/finance/payment-health")
    assert resp.status_code == 404, (
        "get_payment_health never existed in the codebase; 404 expected"
    )


def test_get_revenue_metrics_returns_404():
    resp = client.get("/api/v1/admin/finance/revenue-metrics")
    assert resp.status_code == 404, (
        "get_revenue_metrics never existed in the codebase; 404 expected"
    )


def test_finance_module_not_in_route_table():
    path_strings = [route.path for route in app.routes if hasattr(route, "path")]
    finance_module_paths = [p for p in path_strings if "/api/v1/finance/" in p]
    assert len(finance_module_paths) == 0, (
        "backend/modules/finance/ was a non-canonical module (Law 13 violation) "
        "and must not appear in the route table"
    )


def test_admin_finance_router_imports():
    spec = importlib.util.spec_from_file_location(
        "admin_finance_router",
        Path(__file__).resolve().parents[1] / "modules" / "admin" / "routers" / "finance.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "router"), "admin finance router missing 'router' attribute"
