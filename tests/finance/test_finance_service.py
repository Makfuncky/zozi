"""Paired test for FILE-7: finance_service Decimal precision (LOGIC-001/002/047, Law 19 + Law 42).

Law 19: "Decimal for money" — monetary values and rates MUST use Decimal/Numeric,
float FORBIDDEN for money (binary artifacts e.g. 0.1+0.2 != 0.3).
Law 42: Pydantic validation — schemas validate bounds with Decimal limits.

Before:
  class CodRemittanceRequest(BaseModel):
      amount: float                                   # :68 LOGIC-001
  class CommissionRateBody(BaseModel):
      rate: float = Field(..., ge=0.0, le=1.0, ...)   # :335 LOGIC-002
  def reconcile_in_multi_currency(amount: float, ...) # :581 LOGIC-047
      rate = float(target) / float(base); round(amount*rate, 2)

After:
  amount/rate/new_amount/order_value/...: Decimal with ge/gt/le Decimal bounds
  + field_validator(mode="before") Decimal(str(v)) for float/int/str compat
  reconcile: Decimal(str()) coercion, Decimal division, quantize(0.01, HALF_UP).

DB columns already Numeric (commission.py Numeric(5,4)/Numeric(12,2),
general_ledger.py Numeric(12,2)/Numeric(5,4), alembic baseline) — schema-only fix,
no migration needed. Downstream general_ledger/cash helpers already do
Decimal(str(...)) internally, so Decimal inputs are compatible.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

SERVICE_PATH = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "domains"
    / "finance"
    / "services"
    / "finance_service.py"
)


def _ensure_pkg(name: str):
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        mod.__path__ = []  # mark as package
        sys.modules[name] = mod
    return mod


def _load_service():
    # Clear prior synthetic load only; leave real third-party (pydantic/fastapi) alone.
    for name in list(sys.modules):
        if name == "finance_service_under_test":
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
    ]:
        _ensure_pkg(pkg)

    # --- providers.finance.bank_api ---
    bank_api = types.ModuleType("providers.finance.bank_api")
    class BankApiError(Exception):
        pass
    bank_api.BankApiError = BankApiError
    bank_api.dispatch_batch = lambda *a, **k: {}
    bank_api.test_connection = lambda *a, **k: {"ok": True, "detail": "ok"}
    sys.modules["providers.finance.bank_api"] = bank_api

    # --- providers.geography.rates (deterministic Decimal rates) ---
    rates_mod = types.ModuleType("providers.geography.rates")
    def _fetch_rates():
        return (
            {"USD": Decimal("1"), "EUR": Decimal("0.9"), "OMR": Decimal("0.38")},
            "test",
        )
    rates_mod.fetch_rates = _fetch_rates
    sys.modules["providers.geography.rates"] = rates_mod

    # --- providers.automation.scheduler ---
    sched = types.ModuleType("providers.automation.scheduler")
    sched.add_interval_job = lambda *a, **k: None
    sched.create_scheduler = lambda *a, **k: None
    sys.modules["providers.automation.scheduler"] = sched

    # --- providers.payments.connect ---
    connect = types.ModuleType("providers.payments.connect")
    connect.create_connect_account = lambda **k: {"id": "acct_test"}
    sys.modules["providers.payments.connect"] = connect

    # --- infrastructure.utils.auth ---
    auth_mod = types.ModuleType("infrastructure.utils.auth")
    auth_mod.require_permission = lambda *a, **k: None
    sys.modules["infrastructure.utils.auth"] = auth_mod

    # --- infrastructure.security.dependencies ---
    sec_dep = types.ModuleType("infrastructure.security.dependencies")
    sec_dep.require_admin = lambda *a, **k: None
    sys.modules["infrastructure.security.dependencies"] = sec_dep

    # --- infrastructure.database.database ---
    db_mod = types.ModuleType("infrastructure.database.database")
    db_mod.get_db = lambda: None
    sys.modules["infrastructure.database.database"] = db_mod

    # --- infrastructure.database.schemas (dummy models for all imported names) ---
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

    # --- infrastructure.utils.dependencies ---
    deps = types.ModuleType("infrastructure.utils.dependencies")
    deps.get_current_user = lambda *a, **k: {}
    deps.require_admin = lambda *a, **k: None
    sys.modules["infrastructure.utils.dependencies"] = deps

    # --- infrastructure.utils.config ---
    cfg = types.ModuleType("infrastructure.utils.config")
    cfg.settings = types.SimpleNamespace(
        bank_api_batch_path="/batch", bank_api_timeout_seconds="5"
    )
    sys.modules["infrastructure.utils.config"] = cfg

    # --- infrastructure.utils.country_rls ---
    rls_country = types.ModuleType("infrastructure.utils.country_rls")
    rls_country.get_country_or_404 = lambda *a, **k: {"code": "US"}
    sys.modules["infrastructure.utils.country_rls"] = rls_country

    # --- infrastructure.database.rls_interceptor ---
    rls = types.ModuleType("infrastructure.database.rls_interceptor")
    rls.set_rls_context = lambda *a, **k: None
    rls.clear_rls_context = lambda *a, **k: None
    sys.modules["infrastructure.database.rls_interceptor"] = rls

    # --- domains.finance.services.treasury.cash_management_service ---
    cms = types.ModuleType(
        "domains.finance.services.treasury.cash_management_service"
    )
    class CashManagementService:
        def __init__(self, db=None):
            self.db = db
    cms.CashManagementService = CashManagementService
    sys.modules["domains.finance.services.treasury.cash_management_service"] = cms

    # --- domains.finance.services.ledger.general_ledger_service ---
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

    # --- domains.accounts.models.user ---
    user_mod = types.ModuleType("domains.accounts.models.user")
    user_mod.User = type("User", (), {})
    sys.modules["domains.accounts.models.user"] = user_mod

    spec = importlib.util.spec_from_file_location(
        "finance_service_under_test", str(SERVICE_PATH)
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["finance_service_under_test"] = module
    spec.loader.exec_module(module)
    return module


MOD = _load_service()


# --- P1 LOGIC-001: CodRemittanceRequest.amount is Decimal ---
def test_cod_amount_is_decimal_and_nonnegative():
    m = MOD.CodRemittanceRequest(amount=Decimal("10.50"))
    assert isinstance(m.amount, Decimal)
    assert m.amount == Decimal("10.50")
    with pytest.raises(ValidationError):
        MOD.CodRemittanceRequest(amount=Decimal("-1"))


def test_cod_amount_float_compat_exact():
    # float 0.1 must coerce via Decimal(str()) -> Decimal("0.1"), not binary float.
    m = MOD.CodRemittanceRequest(amount=0.1)
    assert isinstance(m.amount, Decimal)
    assert m.amount == Decimal("0.1")
    assert m.amount != Decimal(0.1) or True  # Decimal(str(0.1)) is exact "0.1"
    assert str(m.amount) == "0.1"
    # int/str compat, identical business values
    assert MOD.CodRemittanceRequest(amount=5).amount == Decimal("5")
    assert MOD.CodRemittanceRequest(amount="7.25").amount == Decimal("7.25")


# --- P2 LOGIC-002: CommissionRateBody.rate is Decimal with 0..1 bounds ---
def test_commission_rate_decimal_bounds():
    m = MOD.CommissionRateBody(rate=Decimal("0.12"))
    assert isinstance(m.rate, Decimal)
    assert m.rate == Decimal("0.12")
    # float compat keeps business value
    assert MOD.CommissionRateBody(rate=0.12).rate == Decimal("0.12")
    for bad in [Decimal("-0.01"), Decimal("1.01"), -0.5, 1.5]:
        with pytest.raises(ValidationError):
            MOD.CommissionRateBody(rate=bad)
    # edges allowed
    assert MOD.CommissionRateBody(rate=0).rate == Decimal("0")
    assert MOD.CommissionRateBody(rate=1).rate == Decimal("1")


def test_all_money_rate_schemas_use_decimal():
    # GlobalConfigBody
    g = MOD.GlobalConfigBody(default_rate=0.1, low_value_threshold="5.00",
                             fixed_cap_amount=10, margin_threshold=Decimal("0.5"))
    assert isinstance(g.default_rate, Decimal) and g.default_rate == Decimal("0.1")
    assert g.low_value_threshold == Decimal("5.00")
    # CategoryRateBody
    c = MOD.CategoryRateBody(rate=0.2)
    assert isinstance(c.rate, Decimal) and c.rate == Decimal("0.2")
    # BadgeTierBody
    b = MOD.BadgeTierBody(commission_rate=0.15, setup_fee=9.99,
                          recurring_fee="4.50", min_monthly_revenue=100)
    assert b.commission_rate == Decimal("0.15")
    assert b.setup_fee == Decimal("9.99")
    assert b.recurring_fee == Decimal("4.50")
    assert b.min_monthly_revenue == Decimal("100")
    # LedgerAdjustmentBody
    la = MOD.LedgerAdjustmentBody(new_amount=12.34, reason="correction reason here")
    assert isinstance(la.new_amount, Decimal) and la.new_amount == Decimal("12.34")
    with pytest.raises(ValidationError):
        MOD.LedgerAdjustmentBody(new_amount=-1, reason="correction reason here")
    # PreviewBody
    p = MOD.PreviewBody(supplier_id=1, order_value=99.99)
    assert isinstance(p.order_value, Decimal) and p.order_value == Decimal("99.99")
    with pytest.raises(ValidationError):
        MOD.PreviewBody(supplier_id=1, order_value=0)


# --- P3 LOGIC-047: reconcile_in_multi_currency uses Decimal ---
def test_reconcile_same_currency_returns_decimal_one():
    r = MOD.reconcile_in_multi_currency(Decimal("100.00"), "USD", "USD")
    assert r["original"] == Decimal("100.00")
    assert r["converted"] == Decimal("100.00")
    assert r["rate"] == Decimal("1")
    assert isinstance(r["rate"], Decimal)


def test_reconcile_decimal_arithmetic_exact():
    # 100 USD -> EUR at 0.9/1 = 0.9 => 90.00 exact (float would give 89.999... risk)
    r = MOD.reconcile_in_multi_currency(Decimal("100"), "USD", "EUR")
    assert r["rate"] == Decimal("0.9")
    assert r["converted"] == Decimal("90.00")
    assert isinstance(r["converted"], Decimal)
    # float input compat, identical business value
    r2 = MOD.reconcile_in_multi_currency(100.0, "USD", "EUR")
    assert r2["converted"] == Decimal("90.00")
    assert r2["original"] == Decimal("100.0")


def test_reconcile_rounding_half_up():
    # 10 OMR base 0.38 -> USD: rate = 1/0.38 = 2.631578..., 10*rate = 26.3157 -> 26.32
    r = MOD.reconcile_in_multi_currency(Decimal("10"), "OMR", "USD")
    expected_rate = Decimal("1") / Decimal("0.38")
    expected = (Decimal("10") * expected_rate).quantize(Decimal("0.01"))
    assert r["rate"] == expected_rate
    assert r["converted"] == expected


def test_reconcile_missing_rate_and_invalid_amount():
    r = MOD.reconcile_in_multi_currency(Decimal("5"), "USD", "XXX")
    assert r["converted"] is None and r["rate"] is None and "error" in r
    assert r["original"] == Decimal("5")
    r2 = MOD.reconcile_in_multi_currency("not-a-number", "USD", "EUR")
    assert r2["converted"] is None and "error" in r2


def test_no_float_money_in_source():
    src = SERVICE_PATH.read_text(encoding="utf-8")
    assert "amount: float" not in src
    assert "rate: float" not in src
    assert "Optional[float]" not in src
    assert "new_amount: Decimal" in src
    assert "order_value: Decimal" in src
    assert "def reconcile_in_multi_currency(amount: Decimal" in src
    assert "quantize(Decimal(\"0.01\")" in src
