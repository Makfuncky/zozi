"""Paired tests for FILE-2: commission_service pagination and explicit columns.

Contract: _audit/resolver/contracts/commission-service.md
Findings fixed:
  PERF-028 — db.query(Model) without explicit columns → db.query(Model.col1, ...)
  PERF-040 — unbounded .all() in list functions → keyset pagination (cursor_before + limit)
"""
from __future__ import annotations

import importlib.util
import sys
import types
import unittest.mock
from pathlib import Path


# ── Paths ────────────────────────────────────────────────────────────────────

SERVICE_PATH = (
    Path(__file__).resolve().parents[3]
    / "backend"
    / "domains"
    / "catalog"
    / "services"
    / "commission_service.py"
)


# ── Stub column descriptors ───────────────────────────────────────────────────

class _Col:
    """Column descriptor; supports is_() / == / > / asc / desc."""
    def __init__(self, name):
        self.key = name
        self.name = name

    def is_(self, value):
        return _Cmp(self, "is_", value)

    def __eq__(self, other):
        return _Cmp(self, "eq", other)

    def __gt__(self, other):
        return _Cmp(self, "gt", other)

    def __lt__(self, other):
        return _Cmp(self, "lt", other)

    def asc(self):
        return self

    def desc(self):
        return self


class _Cmp:
    def __init__(self, col, op, val):
        self.col = col
        self.op = op
        self.val = val


# Unique subclasses per model → enables isinstance-based dispatch
class _CGCol(_Col): pass
class _CPCol(_Col): pass
class _CRCol(_Col): pass


def _cg(name): return _CGCol(name)
def _cp(name): return _CPCol(name)
def _cr(name): return _CRCol(name)


# ── Complete stub model classes (every column the service accesses) ────────────

class CommissionGroup:
    id                    = _cg("id")
    name                  = _cg("name")
    slug                  = _cg("slug")
    description           = _cg("description")
    base_rate             = _cg("base_rate")
    max_commission_amount = _cg("max_commission_amount")
    is_active             = _cg("is_active")
    country_code          = _cg("country_code")
    is_deleted            = _cg("is_deleted")
    created_at            = _cg("created_at")
    updated_at            = _cg("updated_at")
    version               = _cg("version")


class CommissionProfile:
    id                    = _cp("id")
    supplier_id           = _cp("supplier_id")
    name                  = _cp("name")
    slug                  = _cp("slug")
    description           = _cp("description")
    is_default            = _cp("is_default")
    is_active             = _cp("is_active")
    country_code          = _cp("country_code")
    is_deleted            = _cp("is_deleted")
    created_at            = _cp("created_at")
    updated_at            = _cp("updated_at")
    version               = _cp("version")


class CommissionRule:
    id                      = _cr("id")
    profile_id              = _cr("profile_id")
    commission_group_id     = _cr("commission_group_id")
    name                    = _cr("name")
    coc_node_id             = _cr("coc_node_id")
    product_type_id         = _cr("product_type_id")
    brand                   = _cr("brand")
    attribute_key           = _cr("attribute_key")
    attribute_value         = _cr("attribute_value")
    rate                    = _cr("rate")
    max_commission_amount   = _cr("max_commission_amount")
    priority                = _cr("priority")
    effective_from          = _cr("effective_from")
    effective_to            = _cr("effective_to")
    is_active               = _cr("is_active")
    country_code            = _cr("country_code")
    is_deleted              = _cr("is_deleted")
    created_at              = _cr("created_at")
    updated_at              = _cr("updated_at")
    version                 = _cr("version")


# ── Per-model column index maps (avoids name collisions across models) ────────
# Keys are column *names*; values are positional indices in that model's tuple.

_CG_IDX: dict[str, int] = {
    "id": 0, "name": 1, "slug": 2, "description": 3,
    "base_rate": 4, "max_commission_amount": 5, "is_active": 6,
    "country_code": 7, "is_deleted": 8,
    "created_at": 9, "updated_at": 10, "version": 11,
}

_CP_IDX: dict[str, int] = {
    "id": 0, "supplier_id": 1, "name": 2, "slug": 3,
    "description": 4, "is_default": 5, "is_active": 6,
    "country_code": 7, "is_deleted": 8,
    "created_at": 9, "updated_at": 10, "version": 11,
}

_CR_IDX: dict[str, int] = {
    "id": 0, "profile_id": 1, "commission_group_id": 2, "name": 3,
    "coc_node_id": 4, "product_type_id": 5, "brand": 6,
    "attribute_key": 7, "attribute_value": 8, "rate": 9,
    "max_commission_amount": 10, "priority": 11,
    "effective_from": 12, "effective_to": 13,
    "is_active": 14, "country_code": 15, "is_deleted": 16,
    "created_at": 17, "updated_at": 18, "version": 19,
}

_MODEL_IDX: dict[type, dict[str, int]] = {
    _CGCol: _CG_IDX,
    _CPCol: _CP_IDX,
    _CRCol: _CR_IDX,
}


def _col_index(col):
    """Resolve column descriptor to positional index; unwraps _Cmp wrappers."""
    # Unwrap nested _Cmp from .is_() chains: is_deleted.is_(False) → _Cmp(_Cmp(_Col,...), ...)
    while isinstance(col, _Cmp):
        col = col.col
    if not hasattr(col, "name"):
        return None
    # Dispatch by column CLASS (not name) to avoid cross-model name collisions
    for col_cls, idx_map in _MODEL_IDX.items():
        if isinstance(col, col_cls):
            return idx_map.get(col.name)
    return None


def _apply_filter(rows, cond):
    """Apply one filter condition to a list of row tuples."""
    if isinstance(cond, _Cmp):
        col, raw_val, op = cond.col, cond.val, cond.op
    elif isinstance(cond, tuple):
        col, raw_val = cond
        op = getattr(raw_val, "op", None) if isinstance(raw_val, _Cmp) else None
    else:
        return rows

    idx = _col_index(col)
    if idx is None:
        return rows

    cmp_val = raw_val.val if isinstance(raw_val, _Cmp) else raw_val

    if op == "eq":
        return [r for r in rows if r[idx] == cmp_val]
    if op == "gt":
        return [r for r in rows if r[idx] is not None and r[idx] > cmp_val]
    if op == "lt":
        return [r for r in rows if r[idx] is not None and r[idx] < cmp_val]
    if op == "is_":
        if cmp_val is True:
            return [r for r in rows if r[idx] is True]
        if cmp_val is False:
            return [r for r in rows if r[idx] is False]
        return [r for r in rows if r[idx] is cmp_val]
    return rows


class _Q:
    """Mimics a SQLAlchemy query chain: .filter().order_by().limit().all().

    All mutating methods modify ``self._rows`` in place and return ``self``
    so callers can chain::

        q = db.query(Model.id).filter(...).order_by(...).limit(5)
    """

    def __init__(self, rows):
        self._rows = list(rows)

    def filter(self, *args, **kwargs):
        combined = list(args) + list(kwargs.items())
        for cond in combined:
            self._rows = _apply_filter(self._rows, cond)
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, n):
        self._rows = self._rows[:n]
        return self

    def all(self):
        return list(self._rows)

    def __iter__(self):
        return iter(self._rows)


class FakeDB:
    """Returns a fresh _Q for each db.query(col1, col2, ...) call.

    Dispatches on the class of the first column descriptor.
    """

    def __init__(self, groups, profiles, rules):
        self._groups = list(groups)
        self._profiles = list(profiles)
        self._rules = list(rules)

    def query(self, *cols):
        if not cols:
            return _Q([])
        first = cols[0]
        if isinstance(first, _CGCol):
            return _Q(self._groups)
        if isinstance(first, _CPCol):
            return _Q(self._profiles)
        if isinstance(first, _CRCol):
            return _Q(self._rules)
        return _Q([])


# ── Module loader ─────────────────────────────────────────────────────────────

def _load_service():
    """Load commission_service.py with stubbed commission models."""
    sys.modules.pop("commission_service_under_test", None)

    stub_commission = types.ModuleType("domains.catalog.models.commission")
    stub_commission.CommissionGroup = CommissionGroup
    stub_commission.CommissionProfile = CommissionProfile
    stub_commission.CommissionRule = CommissionRule

    def _ensure_pkg(name):
        mod = sys.modules.get(name)
        if mod is None:
            mod = types.ModuleType(name)
            mod.__path__ = []
            sys.modules[name] = mod
        return mod

    _ensure_pkg("domains")
    _ensure_pkg("domains.catalog")
    _ensure_pkg("domains.catalog.models")

    with unittest.mock.patch.dict(
        sys.modules, {"domains.catalog.models.commission": stub_commission}
    ):
        spec = importlib.util.spec_from_file_location(
            "commission_service_under_test", str(SERVICE_PATH)
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["commission_service_under_test"] = module
        spec.loader.exec_module(module)
        return module


# ── Row factories (column order must EXACTLY match service query order) ────────
#
# Service query column orders:
#   CommissionGroup:  id, name, slug, description, base_rate,
#                     max_commission_amount, is_active, country_code,
#                     is_deleted, created_at, updated_at, version  (12 cols)
#   CommissionProfile: id, supplier_id, name, slug, description, is_default,
#                      is_active, country_code, is_deleted,
#                      created_at, updated_at, version            (12 cols)
#   CommissionRule:   id, profile_id, commission_group_id, name, coc_node_id,
#                     product_type_id, brand, attribute_key, attribute_value,
#                     rate, max_commission_amount, priority, effective_from,
#                     effective_to, is_active, country_code, is_deleted,
#                     created_at, updated_at, version              (20 cols)


def _make_group(id_, name="G", is_active=True):
    return (id_, name, f"slug-{id_}", None, 10.0, None,
            is_active, "AE", False, None, None, 1)


def _make_profile(id_, supplier_id=1, name="P"):
    return (id_, supplier_id, name, f"slug-{id_}", None, False,
            True, "AE", False, None, None, 1)


def _make_rule(
    id_,
    profile_id=1,
    commission_group_id=None,
    name="R",
    rate=10.0,
    priority=100,
):
    return (
        id_, profile_id, commission_group_id, name,
        None, None, None, None, None,
        rate, None, priority,
        None, None, True, "AE", False, None, None, 1,
    )


def _encode_cursor(last_id):
    """Encode an integer id as base64 cursor matching the service implementation."""
    import base64 as _b64
    import json as _json
    return _b64.urlsafe_b64encode(_json.dumps({"id": last_id}).encode()).decode()


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_list_commission_groups_pagination():
    """PERF-040: keyset pagination returns (rows, has_more) and respects limit."""
    module = _load_service()
    groups = [_make_group(i) for i in range(1, 6)]  # 5 groups, ids 1-5
    db = FakeDB(groups, [], [])

    rows, has_more = module.list_commission_groups(db, limit=3)
    assert len(rows) == 3
    assert has_more is True
    assert [r[0] for r in rows] == [1, 2, 3]

    rows2, has_more2 = module.list_commission_groups(
        db, limit=3, cursor_before=_encode_cursor(3)
    )
    assert len(rows2) == 2
    assert has_more2 is False
    assert [r[0] for r in rows2] == [4, 5]


def test_list_commission_groups_explicit_columns():
    """PERF-028: list function uses explicit columns, not bare db.query(Model)."""
    source = SERVICE_PATH.read_text(encoding="utf-8")
    list_fn = source.split("def list_commission_groups(")[1].split("def ")[0]
    assert "db.query(CommissionGroup)" not in list_fn
    assert "CommissionGroup.id," in list_fn


def test_list_commission_groups_no_unbounded_all():
    """PERF-040: list function does not call .all() directly on its query."""
    source = SERVICE_PATH.read_text(encoding="utf-8")
    list_fn = source.split("def list_commission_groups(")[1].split("def ")[0]
    assert ".all()" not in list_fn


def test_list_commission_profiles_pagination():
    """PERF-040: keyset pagination + supplier_id filter both work."""
    module = _load_service()
    profiles = [
        _make_profile(1, supplier_id=2, name="A"),
        _make_profile(2, supplier_id=1, name="B"),
        _make_profile(3, supplier_id=1, name="C"),
        _make_profile(4, supplier_id=1, name="D"),
    ]
    db = FakeDB([], profiles, [])

    rows, has_more = module.list_commission_profiles(db, supplier_id=1, limit=2)
    assert len(rows) == 2
    assert has_more is True
    assert [r[0] for r in rows] == [2, 3]

    rows2, has_more2 = module.list_commission_profiles(
        db, supplier_id=1, limit=2, cursor_before=_encode_cursor(3)
    )
    assert len(rows2) == 1
    assert has_more2 is False
    assert [r[0] for r in rows2] == [4]


def test_list_commission_profiles_explicit_columns():
    """PERF-028: list function uses explicit columns, not bare db.query(Model)."""
    source = SERVICE_PATH.read_text(encoding="utf-8")
    list_fn = source.split("def list_commission_profiles(")[1].split("def ")[0]
    assert "db.query(CommissionProfile)" not in list_fn
    assert "CommissionProfile.id," in list_fn


def test_list_commission_profiles_no_unbounded_all():
    """PERF-040: list function does not call .all() directly on its query."""
    source = SERVICE_PATH.read_text(encoding="utf-8")
    list_fn = source.split("def list_commission_profiles(")[1].split("def ")[0]
    assert ".all()" not in list_fn


def test_list_commission_rules_pagination():
    """PERF-040: keyset pagination + profile_id filter both work."""
    module = _load_service()
    rules = [
        _make_rule(1, profile_id=1, rate=5.0),
        _make_rule(2, profile_id=1, rate=7.5),
        _make_rule(3, profile_id=1, rate=10.0),
        _make_rule(4, profile_id=2, rate=12.0),
    ]
    db = FakeDB([], [], rules)

    rows, has_more = module.list_commission_rules(db, profile_id=1, limit=2)
    assert len(rows) == 2
    assert has_more is True
    assert [r[0] for r in rows] == [1, 2]

    rows2, has_more2 = module.list_commission_rules(
        db, profile_id=1, limit=2, cursor_before=_encode_cursor(2)
    )
    assert len(rows2) == 1
    assert has_more2 is False
    assert [r[0] for r in rows2] == [3]


def test_list_commission_rules_explicit_columns():
    """PERF-028: list function uses explicit columns, not bare db.query(Model)."""
    source = SERVICE_PATH.read_text(encoding="utf-8")
    list_fn = source.split("def list_commission_rules(")[1].split("def ")[0]
    assert "db.query(CommissionRule)" not in list_fn
    assert "CommissionRule.id," in list_fn


def test_list_commission_rules_no_unbounded_all():
    """PERF-040: list function does not call .all() directly on its query."""
    source = SERVICE_PATH.read_text(encoding="utf-8")
    list_fn = source.split("def list_commission_rules(")[1].split("def ")[0]
    assert ".all()" not in list_fn


def test_list_commission_rules_filters():
    """Optional filter kwargs: profile_id, commission_group_id."""
    module = _load_service()
    rules = [
        _make_rule(1, profile_id=1, commission_group_id=10, rate=5.0),
        _make_rule(2, profile_id=2, commission_group_id=20, rate=7.5),
        _make_rule(3, profile_id=1, commission_group_id=20, rate=10.0),
    ]
    db = FakeDB([], [], rules)

    rows, _ = module.list_commission_rules(db, profile_id=1)
    assert [r[0] for r in rows] == [1, 3]

    rows, _ = module.list_commission_rules(db, commission_group_id=20)
    assert [r[0] for r in rows] == [2, 3]
