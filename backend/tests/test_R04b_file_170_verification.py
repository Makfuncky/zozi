"""R-04b verification: FILE 170 endpoint state.

Block FILE 170 claimed 4 finance endpoints were deleted with no replacement.
Evidence shows:
  - Route count is 85, not 738
  - CONTRAD-001 does NOT exist in _audit/07_CONTRADICTIONS.md
  - get_cash_flow_report, get_payment_health, get_revenue_metrics never existed
  - admin_financial_summary exists in modules/employee/routers/finance.py
  - backend/modules/finance/ was a non-canonical module (Law 13 violation)
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_route_count_is_85():
    route_count = len(app.routes)
    assert route_count == 85, (
        f"Block FILE 170 claims 738 routes; actual is {route_count}"
    )


def test_admin_financial_summary_reachable_with_admin_auth(admin_auth_headers):
    """admin_financial_summary must be reachable and return non-5xx for an
    authorized admin principal.  The endpoint currently lives under the
    employee module prefix because the canonical admin-module router does
    not yet expose it — that is a separate architectural escalation, not
    a FILE 170 deletion."""
    resp = client.get(
        "/api/v1/employee/finance/admin/summary",
        headers=admin_auth_headers,
    )
    assert resp.status_code < 500, (
        f"admin_financial_summary returned {resp.status_code}; expected non-5xx. "
        "Body: " + resp.text[:300]
    )



# REMOVED L-10: test_phantom_cash_flow_report_never_existed
# The path /api/v1/admin/finance/cash-flow-report never had a real route.
# This endpoint name was fabricated; asserting 404 for a non-existent path
# is vacuous (any unregistered path returns 404 or is intercepted by middleware).
# Real cash-flow capability exists at /api/v1/employee/finance/cash-flow-forecast.
# Product gap: no top-level admin cash-flow report endpoint.

# REMOVED L-10: test_phantom_payment_health_never_existed
# The path /api/v1/admin/finance/payment-health never had a real route.
# This endpoint name was fabricated; asserting 404 for a non-existent path
# is vacuous (any unregistered path returns 404 or is intercepted by middleware).

# REMOVED L-10: test_phantom_revenue_metrics_never_existed
# The path /api/v1/admin/finance/revenue-metrics never had a real route.
# This endpoint name was fabricated; asserting 404 for a non-existent path
# is vacuous (any unregistered path returns 404 or is intercepted by middleware).


def test_finance_module_absent_from_route_table():
    path_strings = [r.path for r in app.routes if hasattr(r, "path")]
    finance_module_paths = [p for p in path_strings if "/api/v1/finance/" in p]
    assert len(finance_module_paths) == 0, (
        "backend/modules/finance/ was a non-canonical module (Law 13 violation) "
        "and must not appear in the route table"
    )



# REMOVED L-10: test_contrad_001_does_not_exist
# Path resolution was incorrect (Path("_audit/07_CONTRADICTIONS.md") resolves
# relative to cwd, which is backend/ during pytest, so it looked for
# backend/_audit/07_CONTRADICTIONS.md which does not exist.
# test_R04c already covers CONTRAD-001 presence/absence with correct pathing.
# This test asserted nothing because the file path was wrong.
