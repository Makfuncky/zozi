"""Regression test for the MET5 split of ``models/__init__.py``.

Verifies that, after moving the god module's responsibilities into domain
subpackages:

* all 297 ORM tables still register (no duplicate ``__tablename__``),
* the domain packages expose their canonical classes, and
* the preserved flat modules / re-export shims keep resolving
  (backward compatibility, no broken import chains).
"""
from __future__ import annotations

import os
import sys

# Ensure the backend package is importable when the test is run standalone.
BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, os.path.abspath(BACKEND))

import models  # noqa: E402


def test_table_count_and_no_duplicates():
    tables = list(models.Base.metadata.tables.keys())
    assert len(tables) == 297, f"expected 297 tables, got {len(tables)}"
    dupes = {t for t in tables if tables.count(t) > 1}
    assert not dupes, f"duplicate table names: {dupes}"


def test_all_names_resolve():
    missing = [n for n in models.__all__ if not hasattr(models, n)]
    assert not missing, f"missing __all__ names: {missing}"


def test_domain_packages_expose_classes():
    from models.identity import User
    from models.catalog import Product
    from models.orders import Order, OrderNotification  # OrderNotification __all__ regression
    from models.gateway import Payment
    from models.logistics import LogisticsPartner
    from models.geography import CountryConfig
    from models.finance import TransactionLedger
    from models.hr import Employee
    from models.media import MediaAsset
    from models.ai import AIUploadJob
    from models.security import FraudEvent
    from models.permissions import Permission
    from models.comms import Notification
    from models.configuration import SystemSetting

    for cls in (
        User, Product, Order, OrderNotification, Payment, LogisticsPartner,
        CountryConfig, TransactionLedger, Employee, MediaAsset, AIUploadJob,
        FraudEvent, Permission, Notification, SystemSetting,
    ):
        assert cls.__tablename__ is not None


def test_moved_packages_re_export_via_canonical_submodule():
    # The canonical ORM code now lives under the domain package; the old
    # flat module paths were deleted, so the package must expose everything.
    from models.orders import OrderItem, ReturnRequest
    from models.finance import Invoice, JournalEntry, BankTransaction
    from models.logistics import Shipment
    from models.permissions import (
        PermissionCategory, RolePermissionAssignment,
        UserPermissionOverride, PermissionAuditLog,
    )

    for cls in (OrderItem, ReturnRequest, Invoice, JournalEntry,
                BankTransaction, Shipment, PermissionCategory,
                RolePermissionAssignment, UserPermissionOverride,
                PermissionAuditLog):
        assert cls.__tablename__ is not None


def test_preserved_flat_modules_and_shims_still_resolve():
    # Backward-compat: flat modules and re-export shims keep working.
    from models.user import User
    from models.products import Product
    from models.payments import Payment
    from models.employee_models import Employee
    from models.media_models import MediaAsset
    from models.ai_upload import AIUploadJob
    from models.fraud import FraudEvent
    from models.incident import IncidentWarRoom
    from models.commission import CommissionAgreement
    from models.admin import SystemSetting
    from models.mixins import AuditMixin, SoftDeleteMixin
    from models.onboarding import OnboardingPipeline
    from models.country_control import CountryMapConfig
    from models.suppliers import SupplierProfile  # shim -> comms.suppliers
    from models.marketing import FlashSale  # shim -> comms.marketing

    for cls in (
        User, Product, Payment, Employee, MediaAsset, AIUploadJob, FraudEvent,
        IncidentWarRoom, CommissionAgreement, SystemSetting, AuditMixin,
        SoftDeleteMixin,         OnboardingPipeline, CountryMapConfig,
        SupplierProfile, FlashSale,
    ):
        # Mixins have no __tablename__; the rest must.
        if hasattr(cls, "__tablename__"):
            assert cls.__tablename__ is not None
