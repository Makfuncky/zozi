"""Nature-specific check for FILE-6 finance-service fixes.

Validates the three findings resolved in this session:
  ARCH-003 — no FastAPI imports in finance_service.py
  LOGIC-001 — no float type annotations for money fields
  LOGIC-014 — supplier access denied raises HTTPException(403)
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest
from starlette.exceptions import HTTPException

SERVICE_PATH = (
    Path(__file__).resolve().parents[3]
    / "backend"
    / "domains"
    / "finance"
    / "services"
    / "finance_service.py"
)


def _ensure_pkg(name: str) -> types.ModuleType:
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        mod.__path__ = []
        sys.modules[name] = mod
    return mod


def _load_service() -> types.ModuleType:
    for name in list(sys.modules):
        if name == "finance_service_cash_test":
            del sys.modules[name]

    for pkg in [
        "providers",
        "providers.finance",
        "providers.geography",
        "providers.automation",
        "providers.payments",
        "infrastructure",
        "infrastructure.utils",
        "infrastructure.security",
        "infrastructure.database",
        "domains",
        "domains.finance",
        "domains.finance.services",
        "domains.finance.services.treasury",
        "domains.finance.services.ledger",
        "domains.accounts",
        "domains.accounts.models",
        "domains.logistics",
        "domains.logistics.models",
    ]:
        _ensure_pkg(pkg)

    # providers.finance.bank_api
    bank_api = types.ModuleType("providers.finance.bank_api")
    class BankApiError(Exception):
        pass
    bank_api.BankApiError = BankApiError
    bank_api.dispatch_batch = lambda *a, **k: {}
    bank_api.test_connection = lambda *a, **k: {"ok": True, "detail": "ok"}
    sys.modules["providers.finance.bank_api"] = bank_api

    # providers.geography.rates
    rates_mod = types.ModuleType("providers.geography.rates")
    from decimal import Decimal as _Decimal
    def _fetch_rates():
        return ({"USD": _Decimal("1"), "EUR": _Decimal("0.9"), "OMR": _Decimal("0.38")}, "test")
    rates_mod.fetch_rates = _fetch_rates
    sys.modules["providers.geography.rates"] = rates_mod

    # providers.automation.scheduler
    sched = types.ModuleType("providers.automation.scheduler")
    sched.add_interval_job = lambda *a, **k: None
    sched.create_scheduler = lambda *a, **k: None
    sys.modules["providers.automation.scheduler"] = sched

    # providers.payments.connect
    connect = types.ModuleType("providers.payments.connect")
    connect.create_connect_account = lambda **k: {"id": "acct_test"}
    sys.modules["providers.payments.connect"] = connect

    # infrastructure.utils.auth
    auth_mod = types.ModuleType("infrastructure.utils.auth")
    auth_mod.require_permission = lambda *a, **k: None
    sys.modules["infrastructure.utils.auth"] = auth_mod

    # infrastructure.security.dependencies
    sec_dep = types.ModuleType("infrastructure.security.dependencies")
    sec_dep.require_admin = lambda *a, **k: None
    sys.modules["infrastructure.security.dependencies"] = sec_dep

    # infrastructure.database.database
    db_mod = types.ModuleType("infrastructure.database.database")
    db_mod.get_db = lambda: None
    sys.modules["infrastructure.database.database"] = db_mod

    # infrastructure.database.schemas
    schemas = types.ModuleType("infrastructure.database.schemas")
    _schema_names = [
        "BadgeBillingOut", "BankTransactionCreate", "BankTransactionImportItem",
        "BankTransactionOut", "BankTransactionResolutionIn",
        "FinanceBankConnectionTestOut", "FinanceBankSettingsOut",
        "FinanceBankSettingsUpdate", "FinancialSummaryOut", "LedgerEntryOut",
        "LogisticsCODRemittanceReceiptOut", "LogisticsFinancialSummaryOut",
        "LogisticsSettlementOut", "ReconciliationSummaryOut", "RefundLedgerOut",
        "SupplierFinancialSummaryOut", "SupplierSettlementOut",
        "VATRemittanceCreate", "VATRemittanceOut", "ListPage",
        "CommissionCategoryRateCreate", "CommissionCategoryRateOut",
        "CommissionBadgeTierCreate", "CommissionBadgeTierOut",
    ]
    for _n in _schema_names:
        setattr(schemas, _n, type(_n, (), {}))
    sys.modules["infrastructure.database.schemas"] = schemas

    # infrastructure.utils.dependencies
    deps = types.ModuleType("infrastructure.utils.dependencies")
    deps.get_current_user = lambda *a, **k: {}
    deps.require_admin = lambda *a, **k: None
    sys.modules["infrastructure.utils.dependencies"] = deps

    # infrastructure.utils.config
    cfg = types.ModuleType("infrastructure.utils.config")
    cfg.settings = types.SimpleNamespace(
        bank_api_batch_path="/batch", bank_api_timeout_seconds="5"
    )
    sys.modules["infrastructure.utils.config"] = cfg

    # infrastructure.utils.country_rls
    rls_country = types.ModuleType("infrastructure.utils.country_rls")
    rls_country.get_country_or_404 = lambda *a, **k: {"code": "US"}
    sys.modules["infrastructure.utils.country_rls"] = rls_country

    # infrastructure.database.rls_interceptor
    rls = types.ModuleType("infrastructure.database.rls_interceptor")
    rls.set_rls_context = lambda *a, **k: None
    rls.clear_rls_context = lambda *a, **k: None
    sys.modules["infrastructure.database.rls_interceptor"] = rls

    # domains.finance.services.treasury.cash_management_service
    cms = types.ModuleType("domains.finance.services.treasury.cash_management_service")
    class CashManagementService:
        def __init__(self, db=None):
            self.db = db
    cms.CashManagementService = CashManagementService
    sys.modules["domains.finance.services.treasury.cash_management_service"] = cms

    # domains.finance.services.ledger.general_ledger_service
    gls = types.ModuleType("domains.finance.services.ledger.general_ledger_service")
    for _fn in [
        "get_global_config", "update_global_config", "list_category_rates",
        "update_category_rate", "list_badge_tiers", "update_badge_tier",
        "list_ledger_entries", "create_ledger_adjustment", "preview_commission",
        "list_all_supplier_commissions", "get_supplier_commission",
        "set_supplier_commission", "delete_supplier_commission_override",
        "get_product_commission_override", "list_product_commission_overrides",
        "set_product_commission_override", "delete_product_commission_override",
    ]:
        setattr(gls, _fn, (lambda *a, **k: {}))
    sys.modules["domains.finance.services.ledger.general_ledger_service"] = gls

    # domains.accounts.models.user
    user_mod = types.ModuleType("domains.accounts.models.user")
    user_mod.User = type("User", (), {})
    sys.modules["domains.accounts.models.user"] = user_mod

    # domains.logistics.models.logistics
    logistics_mod = types.ModuleType("domains.logistics.models.logistics")
    logistics_mod.LogisticsPartner = type("LogisticsPartner", (), {})
    sys.modules["domains.logistics.models.logistics"] = logistics_mod

    spec = importlib.util.spec_from_file_location(
        "finance_service_cash_test", str(SERVICE_PATH)
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["finance_service_cash_test"] = module
    spec.loader.exec_module(module)
    return module


MOD = _load_service()


# --- ARCH-003: No FastAPI imports in finance_service.py ---
def test_no_fastapi_imports_in_service():
    src = SERVICE_PATH.read_text(encoding="utf-8")
    assert "from fastapi import" not in src, "FastAPI imports must be removed from service layer"


# --- LOGIC-014: supplier access denied raises HTTPException(403) ---
def test_supplier_financial_summary_raises_403_for_unauthorized():
    db = object()
    with pytest.raises(HTTPException) as exc_info:
        MOD.supplier_financial_summary(db, {"role": "customer", "id": 1})
    assert exc_info.value.status_code == 403
    assert "Supplier access required" in exc_info.value.detail


def test_supplier_list_settlements_raises_403_for_unauthorized():
    db = object()
    with pytest.raises(HTTPException) as exc_info:
        MOD.supplier_list_settlements(0, 20, None, db, {"role": "customer", "id": 1})
    assert exc_info.value.status_code == 403


def test_supplier_list_ledger_raises_403_for_unauthorized():
    db = object()
    with pytest.raises(HTTPException) as exc_info:
        MOD.supplier_list_ledger(0, 20, db, {"role": "customer", "id": 1})
    assert exc_info.value.status_code == 403


def test_supplier_access_allowed_for_supplier_role():
    db = object()
    # Should NOT raise for supplier/admin roles (returns whatever ctrl returns)
    MOD.ctrl.supplier_get_financial_summary = lambda *a, **k: {"ok": True}
    MOD.ctrl.supplier_list_settlements = lambda *a, **k: []
    MOD.ctrl.supplier_list_ledger_entries = lambda *a, **k: []
    result = MOD.supplier_financial_summary(db, {"role": "supplier", "id": 1})
    assert result == {"ok": True}


# --- LOGIC-001: No float type annotations for money ---
def test_no_float_annotations_for_money_in_source():
    src = SERVICE_PATH.read_text(encoding="utf-8")
    assert "amount: float" not in src
    assert "rate: float" not in src
    assert "Optional[float]" not in src
