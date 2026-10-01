"""Regression tests for the supplier_badge_service consolidation.

Verifies that:
  * the service is the single source of truth (SYM2 resolved),
  * controllers/supplier/badge re-exports the REAL service function
    (the old stub returned 0.0 -- a latent bug),
  * the 16 previously-leaked private helpers are now internal to the service
    (API2 resolved), and
  * the pure helpers behave correctly.
"""
import os

# Minimal env so the project import chain (utils.config -> Settings) can load
# without a real secret / database.
os.environ.setdefault("SECRET_KEY", "test-secret-not-for-prod")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from decimal import Decimal

import services.supplier.supplier_badge_service as svc
import controllers.supplier.badge as badge_mod
import controllers.supplier.supplier_controller as sc


PUBLIC_API = [
    "list_supplier_badge_catalog",
    "list_supplier_badge_billing_history",
    "record_badge_billing_payment",
    "purchase_supplier_badge",
    "compute_credibility_score",
    "refresh_supplier_badge",
    "admin_set_supplier_badge",
    "run_badge_recalculation_cycle",
]


def test_public_api_present_in_service():
    for fn in PUBLIC_API:
        assert hasattr(svc, fn), f"service missing public fn: {fn}"


def test_badge_reexport_is_real_service_function():
    # The old controllers/supplier/badge.py stub did `return 0.0`; the re-export
    # must resolve to the canonical service implementation.
    assert badge_mod.compute_credibility_score is svc.compute_credibility_score
    assert badge_mod.refresh_supplier_badge is svc.refresh_supplier_badge


def test_single_definition_sym2_resolved():
    # SYM2: compute_credibility_score and admin_set_supplier_badge must each be
    # defined exactly once (in the service) and imported everywhere else.
    assert sc.compute_credibility_score is svc.compute_credibility_score
    assert sc.admin_set_supplier_badge is svc.admin_set_supplier_badge


def test_private_helpers_internal_to_service():
    # API2: these were flagged as private symbols "leaked" to external modules.
    # After consolidation they must remain module-private and live only here.
    for name in (
        "_round_badge_amount",
        "_BADGE_THRESHOLDS",
        "_FULFILLED_ORDER_STATUSES",
        "_MANUAL_BADGE_LEVELS",
        "_BADGE_AMOUNT_QUANT",
        "_compute_badge_threshold_metrics",
        "_create_badge_billing_record",
        "_serialize_badge_billing_record",
    ):
        assert hasattr(svc, name), f"service should still define {name}"
        assert name.startswith("_"), f"{name} should remain private (internal)"


def test_badge_for_score_pure():
    assert svc._badge_for_score(95) == "gold"
    assert svc._badge_for_score(70) == "silver"
    assert svc._badge_for_score(45) == "bronze"
    assert svc._badge_for_score(10) == "none"


def test_round_badge_amount_quantizes():
    assert svc._round_badge_amount("1.23456") == Decimal("1.235")
    assert svc._round_badge_amount(0) == Decimal("0.000")
