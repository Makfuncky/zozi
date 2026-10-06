"""Law 21 gate for ``domains/finance/models/general_ledger.py``.

Why this file exists
--------------------
Audit block FILE 92 declared 40 findings of the form
``created_at missing server_default=func.now() (Law 21)``, one per ORM class
in ``general_ledger.py``. Each finding anchored on a distinct ``class X(Base):``
line, so the block amounted to a single Law-21 defect repeated per model.

The pre-existing Law-21 gate
``tests/architecture/test_law19_through_law31.py::TestLaw21TimestampsServerDefault``
cannot see this module: it only walks ``ast.AnnAssign`` nodes (the annotated
``created_at: Mapped[...]`` style). ``general_ledger.py`` uses bare
``ast.Assign`` (``created_at = Column(...)``), so every one of its 45 models was
silently skipped and the gate passed regardless of the defect.

The finance domain gates in ``test_finance_architecture.py`` also cannot see it:
``iter_domain_models("finance")`` resolves models via
``domains.finance.models.__init__``, which does not import ``general_ledger``,
so it yields zero models and the Law 19/22/23 assertions are vacuous.

This module therefore checks ``general_ledger`` directly, through both
declaration styles (``Assign`` and ``AnnAssign``) and through the live
SQLAlchemy ``Table`` metadata, which is the authoritative view.

What is asserted (Law 21)
-------------------------
* ``created_at`` is declared with a ``server_default`` -- DB-side, so raw SQL,
  bulk loads and non-ORM writers all get a correct timestamp.
* ``created_at`` is timezone-aware and NOT NULL, so no writer can leave a
  ledger row undated or store a naive local time.
* ``created_at`` carries no Python-side ``default``; a Python-side default would
  let an application clock override the database clock and is the precise
  defect the audit reported.
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
_MODEL_FILE = _BACKEND_ROOT / "domains" / "finance" / "models" / "general_ledger.py"

# Matches a Python-side ``default=`` but NOT ``server_default=``.
_PY_SIDE_DEFAULT = re.compile(r"(?<!server_)default\s*=")

# The 40 model classes the audit named, via the `class X(Base):` line each
# finding pointed at. Kept explicit so a future regression on one of these
# cannot be masked by the file-level sweeps below.
AUDITED_CLASSES = [
    "AccountGroup",
    "Account",
    "Accrual",
    "APBill",
    "APLedger",
    "ARInvoice",
    "ARLedgerEntry",
    "AutomationLog",
    "AutomationRule",
    "BankAccount",
    "BankMappingRule",
    "BankStatementImport",
    "BankStatementLine",
    "BankTransaction",
    "Budget",
    "CashAccount",
    "CashFlowForecast",
    "CashPositionSnapshot",
    "CashTransaction",
    "CostCenter",
    "Customer",
    "FinanceAuditLog",
    "FinanceAutomationLog",
    "FiscalPeriod",
    "FixedAsset",
    "GatewaySettlementSchedule",
    "InvoiceItem",
    "Invoice",
    "JournalEntry",
    "JournalEntryLine",
    "PayoutBatch",
    "PendingJournalEntry",
    "RecurringTemplate",
    "RefundLedger",
    "ScannedExpense",
    "SupplierSettlement",
    "TransactionLedger",
    "TreasuryAccount",
    "VATRemittance",
    "Vendor",
]


def _columns_by_class() -> dict[str, dict[str, str]]:
    """Map each model class to ``{column_name: call_source}``.

    Walks ``ast.ClassDef`` bodies and handles BOTH declaration styles, so the
    gate cannot be sidestepped by picking one over the other (this is precisely
    the hole in the pre-existing Law-21 gate, which reads only ``AnnAssign``):

    * ``created_at = Column(...)``              -> ``ast.Assign``
    * ``created_at: Mapped[...] = Column(...)`` -> ``ast.AnnAssign``
    """
    source = _MODEL_FILE.read_text(encoding="utf-8")
    out: dict[str, dict[str, str]] = {}
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        cols: dict[str, str] = {}
        for stmt in node.body:
            targets: list[ast.expr] = []
            value: object = None
            if isinstance(stmt, ast.Assign):
                targets = list(stmt.targets)
                value = stmt.value
            elif isinstance(stmt, ast.AnnAssign):
                targets = [stmt.target]
                value = stmt.value
            else:
                continue
            if not isinstance(value, ast.Call):
                continue
            func = value.func
            if (getattr(func, "attr", None) or getattr(func, "id", None)) != "Column":
                continue
            call_src = ast.get_source_segment(source, value) or ""
            for target in targets:
                if isinstance(target, ast.Name):
                    cols[target.id] = call_src
        out[node.name] = cols
    return out


def _gl_models() -> list:
    """Import the 45 general_ledger ORM classes explicitly.

    Deliberately does not use ``tests._support.laws.iter_domain_models``:
    that helper resolves models through ``domains.finance.models.__init__``,
    which does not import ``general_ledger``, so it yields nothing for this
    file and every assertion built on it is vacuous.
    """
    from domains.finance.models import general_ledger as gl

    return [
        getattr(gl, name)
        for name in sorted(vars(gl))
        if isinstance(getattr(gl, name), type) and hasattr(getattr(gl, name), "__tablename__")
    ]


@pytest.fixture(scope="module")
def columns_by_class() -> dict[str, dict[str, str]]:
    return _columns_by_class()


@pytest.fixture(scope="module")
def models() -> list:
    return _gl_models()


# ---------------------------------------------------------------------------
# Law 21 -- created_at server_default
# ---------------------------------------------------------------------------


class TestLaw21CreatedAtServerDefault:
    """Every created_at in general_ledger.py is stamped by the database."""

    def test_module_actually_defines_models(self, models):
        """Guard against a vacuous gate.

        If the import or the class scan ever breaks, every assertion below
        would silently pass on an empty set. This pins the expected size.
        """
        assert len(models) == 45, f"expected 45 general_ledger models, got {len(models)}"

    def test_every_created_at_has_server_default(self, columns_by_class):
        """No created_at may rely on a Python-side default (Law 21)."""
        offenders: list[str] = []
        for class_name, cols in columns_by_class.items():
            call_src = cols.get("created_at")
            if call_src is None:
                offenders.append(f"{class_name}: no created_at column")
                continue
            if "server_default" not in call_src:
                offenders.append(f"{class_name}.created_at = {call_src}")
        assert not offenders, (
            "Law 21 violation: created_at missing server_default (audit block FILE 92):\n  "
            + "\n  ".join(offenders)
        )

    def test_no_created_at_has_python_side_default(self, columns_by_class):
        """A Python-side default lets the app clock beat the DB clock (Law 21).

        Matched with a negative lookbehind so ``server_default=`` is not
        mistaken for a Python-side ``default=``.
        """
        offenders = [
            f"{class_name}.created_at = {cols['created_at']}"
            for class_name, cols in columns_by_class.items()
            if cols.get("created_at")
            and _PY_SIDE_DEFAULT.search(cols["created_at"])
        ]
        assert not offenders, (
            "Law 21 violation: created_at carries a Python-side default; "
            "the server must own the timestamp:\n  " + "\n  ".join(offenders)
        )

    def test_created_at_is_timezone_aware_and_not_null(self, columns_by_class):
        """created_at must be timestamptz NOT NULL (audit columns cannot be skipped)."""
        offenders = [
            f"{class_name}.created_at = {cols['created_at']}"
            for class_name, cols in columns_by_class.items()
            if cols.get("created_at")
            and not ("timezone=True" in cols["created_at"] and "nullable=False" in cols["created_at"])
        ]
        assert not offenders, (
            "created_at must be declared DateTime(timezone=True), nullable=False:\n  "
            + "\n  ".join(offenders)
        )

    def test_audited_classes_all_compliant(self, columns_by_class):
        """The 40 classes named by audit findings FILE 92 are individually pinned.

        Filed as one finding per class by the audit; pinned individually so a
        regression on any single ledger table cannot hide behind the sweep.
        """
        offenders: list[str] = []
        for name in AUDITED_CLASSES:
            if name not in columns_by_class:
                offenders.append(f"{name}: class no longer present in general_ledger.py")
            elif "server_default" not in columns_by_class[name].get("created_at", ""):
                offenders.append(f"{name}.created_at = {columns_by_class[name].get('created_at')}")
        assert not offenders, "Law 21 violation on audit-named classes:\n  " + "\n  ".join(offenders)


# ---------------------------------------------------------------------------
# Runtime metadata cross-check
# ---------------------------------------------------------------------------


class TestLaw21LiveMetadata:
    """The mapped SQLAlchemy Table must agree with the source declaration."""

    def test_metadata_created_at_has_server_default(self, models):
        """Live metadata: every created_at column has a server_default."""
        offenders = [
            f"{m.__name__}.created_at"
            for m in models
            if m.__table__.c.created_at.server_default is None
        ]
        assert not offenders, (
            "Law 21 violation: mapped column has no server_default:\n  " + "\n  ".join(offenders)
        )

    def test_metadata_created_at_is_timestamptz_not_null(self, models):
        """Live metadata: created_at is timezone-aware and NOT NULL."""
        offenders = [
            f"{m.__name__}.created_at"
            for m in models
            if not getattr(m.__table__.c.created_at.type, "timezone", False)
            or m.__table__.c.created_at.nullable is not False
        ]
        assert not offenders, (
            "created_at must map to TIMESTAMPTZ NOT NULL:\n  " + "\n  ".join(offenders)
        )

    def test_every_model_has_created_at(self, models):
        """No ledger table may omit created_at entirely."""
        offenders = [m.__name__ for m in models if "created_at" not in m.__table__.c]
        assert not offenders, "Model(s) missing created_at:\n  " + "\n  ".join(offenders)