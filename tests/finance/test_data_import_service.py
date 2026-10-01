"""Paired test for FILE-6: data_import_service atomicity (LOGIC-009 / LOGIC-018, Laws 50/66).

P1 LOGIC-009: record_customs_entry committed entry even if journal post failed
  -> orphan entry without ledger. Fix: SAVEPOINT via `with db.begin_nested():`
  covering entry + shipment + journal; journal failure rolls back entry and
  re-raises (Law 50 explicit txn, Law 59 no-swallow).
P2 LOGIC-018: `seq = 1` hardcoded start -> SEQUENCE_START = 1 module constant
  (Law 66 no magic numbers).
"""
from __future__ import annotations

import importlib.util
import re
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
    / "data_import_service.py"
)


def _ensure_pkg(name: str):
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        mod.__path__ = []
        sys.modules[name] = mod
    return mod


def _load_service():
    for name in list(sys.modules):
        if name == "data_import_service_under_test":
            del sys.modules[name]

    # --- stub leaf modules before exec ---
    _ensure_pkg("domains")
    _ensure_pkg("domains.catalog")
    _ensure_pkg("domains.catalog.models")
    _ensure_pkg("domains.finance")
    _ensure_pkg("domains.finance.models")
    _ensure_pkg("domains.finance.services")
    _ensure_pkg("domains.logistics")
    _ensure_pkg("domains.logistics.models")
    _ensure_pkg("infrastructure")
    _ensure_pkg("infrastructure.database")
    _ensure_pkg("infrastructure.utils")

    class _Col:
        def __eq__(self, other):
            return True

        def __ne__(self, other):
            return False

        def like(self, *a, **k):
            return True

    class _FakeModel:
        id = _Col()
        shipment_ref = _Col()

        def __init__(self, **kw):
            for k, v in kw.items():
                object.__setattr__(self, k, v)
            if "id" not in kw:
                object.__setattr__(self, "id", 1)

    class CustomsEntry(_FakeModel):
        pass

    class LandedCostAllocation(_FakeModel):
        pass

    class ImportCostTemplate(_FakeModel):
        pass

    class ImportShipment(_FakeModel):
        lines = _Col()

    class ImportShipmentLine(_FakeModel):
        pass

    class PurchaseOrder(_FakeModel):
        pass

    class PurchaseOrderLine(_FakeModel):
        pass

    class Warehouse(_FakeModel):
        pass

    class Vendor(_FakeModel):
        pass

    class Account(_FakeModel):
        pass

    class AccountGroup(_FakeModel):
        pass

    class AccountBalance(_FakeModel):
        pass

    class JournalEntry(_FakeModel):
        pass

    class JournalEntryLine(_FakeModel):
        pass

    class Product(_FakeModel):
        pass

    stub_erp = types.ModuleType("domains.finance.models.erp")
    stub_erp.LandedCostAllocation = LandedCostAllocation
    stub_erp.CustomsEntry = CustomsEntry
    stub_erp.ImportCostTemplate = ImportCostTemplate

    stub_log_erp = types.ModuleType("domains.logistics.models.erp")
    stub_log_erp.Warehouse = Warehouse
    stub_log_erp.ImportShipment = ImportShipment
    stub_log_erp.ImportShipmentLine = ImportShipmentLine
    stub_log_erp.PurchaseOrder = PurchaseOrder
    stub_log_erp.PurchaseOrderLine = PurchaseOrderLine

    stub_fin = types.ModuleType("domains.finance.models.finance")
    stub_fin.Vendor = Vendor
    stub_fin.Account = Account
    stub_fin.AccountGroup = AccountGroup
    stub_fin.AccountBalance = AccountBalance
    stub_fin.JournalEntry = JournalEntry
    stub_fin.JournalEntryLine = JournalEntryLine

    stub_prod = types.ModuleType("domains.catalog.models.products")
    stub_prod.Product = Product

    class JournalEntryCreate:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class JournalLineInput:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    stub_schemas = types.ModuleType("infrastructure.database.schemas")
    stub_schemas.JournalEntryCreate = JournalEntryCreate
    stub_schemas.JournalLineInput = JournalLineInput

    stub_gl = types.ModuleType("stub_gl")
    def _ok(db, data, user_id=None):
        class _Out:
            id = 999
        return _Out()
    stub_gl.create_journal_entry = _ok

    stub_fin_svc = types.ModuleType("domains.finance.services.finance_service")
    stub_fin_svc.general_ledger_service = stub_gl

    stub_dt = types.ModuleType("infrastructure.utils.datetime_utils")
    from datetime import datetime, timezone
    stub_dt.utcnow = lambda: datetime.now(timezone.utc)

    # sqlalchemy stubs (only what module import needs)
    stub_sa_orm = sys.modules.get("sqlalchemy.orm")
    # real sqlalchemy is available; keep it. Only stub our domain modules.
    sys.modules["domains.finance.models.erp"] = stub_erp
    sys.modules["domains.logistics.models.erp"] = stub_log_erp
    sys.modules["domains.finance.models.finance"] = stub_fin
    sys.modules["domains.catalog.models.products"] = stub_prod
    sys.modules["infrastructure.database.schemas"] = stub_schemas
    sys.modules["domains.finance.services.finance_service"] = stub_fin_svc
    sys.modules["infrastructure.utils.datetime_utils"] = stub_dt

    spec = importlib.util.spec_from_file_location(
        "data_import_service_under_test", str(SERVICE_PATH)
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["data_import_service_under_test"] = module
    spec.loader.exec_module(module)
    # joinedload needs a real InstrumentedAttribute; stub it to no-op for fakes.
    module.joinedload = lambda *a, **k: None
    return module


# --- fakes for integration ---

class _NestedCtx:
    def __init__(self, session):
        self.s = session

    def __enter__(self):
        self.s._nested_depth += 1
        self.s._snap = list(self.s.added)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.s._nested_depth -= 1
        if exc_type is not None:
            # SAVEPOINT rollback: discard everything added inside block
            self.s.added = self.s._snap
            self.s.savepoint_rolled_back = True
        return False  # propagate (no swallow)


class FakeSession:
    """Minimal Session fake with SAVEPOINT semantics."""

    def __init__(self, shipment):
        self.added = []
        self.committed = False
        self.savepoint_rolled_back = False
        self._nested_depth = 0
        self._snap = []
        self._shipment = shipment
        self.used_savepoint = False

    def begin_nested(self):
        self.used_savepoint = True
        return _NestedCtx(self)

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        for i, o in enumerate(self.added):
            if getattr(o, "id", None) is None:
                o.id = 100 + i

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        pass

    def query(self, model):
        outer = self

        class _Q:
            def options(self, *a, **k):
                return self

            def filter(self, *a, **k):
                return self

            def first(self):
                # Return shipment for ImportShipment queries
                name = getattr(model, "__name__", "")
                if name == "ImportShipment":
                    return outer._shipment
                return None

        return _Q()


def _make_shipment(module):
    line = module.ImportShipmentLine(
        id=1,
        line_total_fx=Decimal("100"),
        unit_cost_local=Decimal("10"),
        unit_cost_fx=Decimal("10"),
        quantity=Decimal("10"),
        allocated_freight=Decimal("0"),
        allocated_insurance=Decimal("0"),
        allocated_port=Decimal("0"),
        allocated_other=Decimal("0"),
        duty_amount=None,
        landed_unit_cost=None,
    )
    shipment = module.ImportShipment(
        id=5,
        shipment_ref="SHIP-00001",
        product_cost_total=Decimal("100"),
        freight_cost=Decimal("0"),
        insurance_cost=Decimal("0"),
        port_charges=Decimal("0"),
        inland_freight=Decimal("0"),
        bank_charges=Decimal("0"),
        other_costs=Decimal("0"),
        duty_cost=Decimal("0"),
        total_landed_cost=Decimal("100"),
        currency="OMR",
        country_code="OM",
        lines=[line],
    )
    return shipment


def test_sequence_start_constant_present():
    module = _load_service()
    assert hasattr(module, "SEQUENCE_START"), "SEQUENCE_START constant missing (Law 66)"
    assert module.SEQUENCE_START == 1


def test_no_hardcoded_seq_start():
    source = SERVICE_PATH.read_text(encoding="utf-8")
    # No `seq = 1` literal may remain; must use SEQUENCE_START (Law 66)
    assert not re.search(r"^\s*seq\s*=\s*1\s*$", source, re.MULTILINE), (
        "hardcoded `seq = 1` still present; use SEQUENCE_START"
    )
    assert "seq = SEQUENCE_START" in source


def test_record_customs_entry_uses_savepoint_and_reraises():
    source = SERVICE_PATH.read_text(encoding="utf-8")
    assert "with db.begin_nested():" in source, "missing SAVEPOINT (Law 50)"
    # error must surface: except block must re-raise (Law 59)
    m = re.search(
        r"except\s+Exception\s+as\s+e:.*?raise",
        source,
        re.DOTALL,
    )
    assert m is not None, "journal failure must re-raise (no swallow, Law 59)"
    # old swallow-only pattern must be gone (warning without raise)
    assert "entry rolled back" in source


def test_journal_failure_rolls_back_entry_no_orphan():
    """Integration (logical): force journal failure, assert no orphan entry."""
    module = _load_service()
    module._ensure_import_accounts = lambda db: None
    shipment = _make_shipment(module)
    db = FakeSession(shipment)

    def _fail(db_, data, user_id=None):
        raise ValueError("GL down")

    module.gl.create_journal_entry = _fail

    try:
        module.record_customs_entry(db, 5, duty_amount=Decimal("10"))
    except ValueError as e:
        assert "GL down" in str(e)
    else:
        raise AssertionError("journal failure must propagate (Law 59)")

    assert db.used_savepoint, "must use savepoint"
    assert db.savepoint_rolled_back, "savepoint must roll back entry"
    assert not db.committed, "must NOT commit on journal failure (Law 50)"
    assert db.added == [], f"no orphan entry may remain, got {db.added}"


def test_journal_success_commits_entry():
    module = _load_service()
    module._ensure_import_accounts = lambda db: None
    shipment = _make_shipment(module)
    db = FakeSession(shipment)
    module.gl.create_journal_entry = lambda db_, data, user_id=None: types.SimpleNamespace(id=999)

    entry = module.record_customs_entry(db, 5, duty_amount=Decimal("10"))
    assert db.used_savepoint
    assert not db.savepoint_rolled_back
    assert db.committed, "success must commit (explicit txn)"
    assert len(db.added) == 1
    assert entry in db.added
