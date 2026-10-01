"""Paired test for FILE-5: commission_read_service precision (LOGIC-024 / ARCH-021, Law 19).

Law 19 (ARCHITECTURE_STACK.md:545): "No float for money — Monetary values MUST
use Decimal or Numeric. Float FORBIDDEN for money."

Before: `"rate": float(rule.rate)` — Decimal->float loses precision/scale.
After:  `"rate": str(rule.rate) if rule.rate is not None else None`
        (string-serialized, JSON-safe; numeric conversion only at the
        serializer/consumption boundary per ARCH-021).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from decimal import Decimal
from pathlib import Path


SERVICE_PATH = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "domains"
    / "finance"
    / "services"
    / "commission_read_service.py"
)


def _load_service_with_stubs():
    """Load the service module with a stubbed model layer.

    The service lazily imports CommissionProfile/CommissionRule/ChartOfCategory/
    CommissionGroup from domains.finance.models.general_ledger, which does not
    export those names (canonical models live in domains.catalog.models.commission).
    That wiring issue is out of scope for LOGIC-024, so the test stubs the model
    module and exercises the rate-serialization logic with fakes.
    """
    for name in list(sys.modules):
        if name == "commission_read_service_under_test" or name.startswith(
            ("domains", "commission_read_service")
        ):
            # Only clear our synthetic module; leave real packages alone.
            if name == "commission_read_service_under_test":
                del sys.modules[name]

    class _Col:
        def __eq__(self, other):  # noqa: D105
            return True

        def __ne__(self, other):  # noqa: D105
            return False

        def is_(self, value):
            return True

        def in_(self, seq):
            return True

        def asc(self):
            return "asc"

    class CommissionProfile:
        supplier_id = _Col()
        is_active = _Col()
        is_deleted = _Col()
        id = _Col()

        def __init__(self, id, supplier_id, name="P", is_default=False, country_code="AE"):
            self.id = id
            self.supplier_id = supplier_id
            self.name = name
            self.is_default = is_default
            self.country_code = country_code

    class CommissionRule:
        profile_id = _Col()
        is_active = _Col()
        is_deleted = _Col()
        id = _Col()
        priority = _Col()

        def __init__(self, id, profile_id, name="R", rate=None, priority=1, **kw):
            self.id = id
            self.profile_id = profile_id
            self.name = name
            self.rate = rate
            self.priority = priority
            self.coc_node_id = kw.get("coc_node_id")
            self.commission_group_id = kw.get("commission_group_id")
            self.brand = kw.get("brand")
            self.product_type_id = kw.get("product_type_id")
            self.country_code = kw.get("country_code", "AE")
            self.effective_from = kw.get("effective_from")
            self.effective_to = kw.get("effective_to")

    class ChartOfCategory:
        id = _Col()

    class CommissionGroup:
        id = _Col()

    stub_models = types.ModuleType("domains.finance.models.general_ledger")
    stub_models.CommissionProfile = CommissionProfile
    stub_models.CommissionRule = CommissionRule
    stub_models.ChartOfCategory = ChartOfCategory
    stub_models.CommissionGroup = CommissionGroup

    # Parent packages must exist so `from domains.finance.models.general_ledger
    # import ...` resolves to the stub without importing the real DB layer.
    def _ensure_pkg(name):
        mod = sys.modules.get(name)
        if mod is None:
            mod = types.ModuleType(name)
            mod.__path__ = []
            sys.modules[name] = mod
        return mod

    _ensure_pkg("domains")
    _ensure_pkg("domains.finance")
    _ensure_pkg("domains.finance.models")
    sys.modules["domains.finance.models.general_ledger"] = stub_models

    spec = importlib.util.spec_from_file_location(
        "commission_read_service_under_test", str(SERVICE_PATH)
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["commission_read_service_under_test"] = module
    spec.loader.exec_module(module)
    return module, stub_models


class _Q:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *a, **k):
        return self

    def order_by(self, *a, **k):
        return self

    def all(self):
        return list(self._rows)


class FakeDB:
    def __init__(self, stubs, profiles, rules):
        self._stubs = stubs
        self._profiles = profiles
        self._rules = rules

    def query(self, model):
        if model is self._stubs.CommissionProfile:
            return _Q(self._profiles)
        if model is self._stubs.CommissionRule:
            return _Q(self._rules)
        return _Q([])


def _call(profiles, rules, supplier_id=7):
    module, stubs = _load_service_with_stubs()
    db = FakeDB(stubs, profiles, rules)
    return module.get_supplier_commission_rates(db, supplier_id), stubs


def test_rate_preserves_decimal_precision_exact():
    """Precision: Decimal('0.10') must serialize as '0.10' (scale preserved)."""
    _, stubs = _load_service_with_stubs()
    profile = stubs.CommissionProfile(id=1, supplier_id=7)
    rule = stubs.CommissionRule(id=11, profile_id=1, rate=Decimal("0.10"))
    result, _ = _call([profile], [rule])
    rate = result[0]["rules"][0]["rate"]
    assert isinstance(rate, str), f"rate must be str, got {type(rate)}"
    assert rate == "0.10", f"scale lost: {rate!r}"
    assert Decimal(rate) == Decimal("0.10")
    # float() would collapse the scale: float(Decimal('0.10')) == 0.1
    assert rate != str(float(Decimal("0.10")))


def test_rate_exact_for_typical_percentage():
    _, stubs = _load_service_with_stubs()
    profile = stubs.CommissionProfile(id=1, supplier_id=7)
    rule = stubs.CommissionRule(id=12, profile_id=1, rate=Decimal("12.34"))
    result, _ = _call([profile], [rule])
    rate = result[0]["rules"][0]["rate"]
    assert rate == "12.34"
    assert not isinstance(rate, float)
    # Exact Decimal round-trip; JSON-safe (raw Decimal is not json.dumps-able).
    assert Decimal(rate) * Decimal("100") == Decimal("1234")
    json.dumps(result)


def test_rate_none_guard():
    _, stubs = _load_service_with_stubs()
    profile = stubs.CommissionProfile(id=1, supplier_id=7)
    rule = stubs.CommissionRule(id=13, profile_id=1, rate=None)
    result, _ = _call([profile], [rule])
    assert result[0]["rules"][0]["rate"] is None


def test_no_float_cast_in_source():
    source = SERVICE_PATH.read_text(encoding="utf-8")
    assert "float(rule.rate)" not in source
    assert "str(rule.rate)" in source
