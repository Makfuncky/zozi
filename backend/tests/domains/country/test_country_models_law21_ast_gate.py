"""AST-based Law 21 gate for country_control.py and country_enhancements.py.

Why this file exists
--------------------
The pre-existing Law-21 gate ``tests/architecture/test_law19_through_law31.py``
only walks ``ast.AnnAssign`` nodes (the annotated ``created_at: Mapped[...]``
style). Both ``country_control.py`` and ``country_enhancements.py`` use bare
``ast.Assign`` (``created_at = Column(...)``), so every one of their timestamp
columns was silently skipped and the gate passed regardless of the defect.

This module checks both files directly through the AST, handling BOTH
declaration styles so the gate cannot be sidestepped:

* ``created_at = Column(...)``              -> ``ast.Assign``
* ``created_at: Mapped[...] = Column(...)`` -> ``ast.AnnAssign``

It also verifies that ``domains/country/models/__init__.py`` imports both
modules, so the architecture gate covering these models cannot be vacuous
(the same class of defect that rendered the finance architecture gates
vacuous because ``domains/finance/models/__init__.py`` never imported
``general_ledger``).

Laws covered: 21 (server_default on timestamps), 20 (country_code String(2)).
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[3]
_COUNTRY_MODELS_DIR = _BACKEND_ROOT / "domains" / "country" / "models"
_INIT_FILE = _COUNTRY_MODELS_DIR / "__init__.py"
_CONTROL_FILE = _COUNTRY_MODELS_DIR / "country_control.py"
_ENHANCEMENTS_FILE = _COUNTRY_MODELS_DIR / "country_enhancements.py"

# Ensure backend root is importable so direct module imports work.
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Matches a Python-side ``default=`` but NOT ``server_default=``.
_PY_SIDE_DEFAULT = re.compile(r"(?<!server_)default\s*=")

# Timestamp column names that must carry server_default=func.now() per Law 21.
_TIMESTAMP_COLUMNS = {"created_at", "updated_at"}


def _parse_columns_by_class(model_file: pathlib.Path) -> dict[str, dict[str, str]]:
    """Map each model class to ``{column_name: call_source}``.

    Walks ``ast.ClassDef`` bodies and handles BOTH declaration styles so the
    gate cannot be sidestepped by picking one over the other:

    * ``col = Column(...)``              -> ``ast.Assign``
    * ``col: Mapped[...] = Column(...)`` -> ``ast.AnnAssign``
    """
    source = model_file.read_text(encoding="utf-8")
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


def _server_default_is_now(call_src: str) -> bool:
    """True if the Column(...) call carries server_default=func.now()."""
    return "server_default=func.now()" in call_src or "server_default=now()" in call_src


def _python_side_default_present(call_src: str) -> bool:
    """True if the Column(...) call has a Python-side default= (not server_)."""
    return bool(_PY_SIDE_DEFAULT.search(call_src))


def _load_orm_models() -> tuple[list, list]:
    """Import the ORM classes from both modules directly.

    Deliberately does not use ``domains.country.models`` (the __init__.py):
    that is what we are testing for vacuous-gate risk.
    """
    import importlib

    control_mod = importlib.import_module("domains.country.models.country_control")
    enhancements_mod = importlib.import_module("domains.country.models.country_enhancements")

    control_models = [
        getattr(control_mod, name)
        for name in sorted(vars(control_mod))
        if isinstance(getattr(control_mod, name), type)
        and hasattr(getattr(control_mod, name), "__tablename__")
    ]
    enhancement_models = [
        getattr(enhancements_mod, name)
        for name in sorted(vars(enhancements_mod))
        if isinstance(getattr(enhancements_mod, name), type)
        and hasattr(getattr(enhancements_mod, name), "__tablename__")
    ]
    return control_models, enhancement_models


class TestCountryModelsLaw21ASTGate:
    """AST walk covering both ast.Assign and ast.AnnAssign."""

    @pytest.fixture(scope="class")
    def control_columns(self):
        return _parse_columns_by_class(_CONTROL_FILE)

    @pytest.fixture(scope="class")
    def enhancements_columns(self):
        return _parse_columns_by_class(_ENHANCEMENTS_FILE)

    def test_control_timestamp_columns_have_server_default_now(
        self, control_columns: dict[str, dict[str, str]]
    ) -> None:
        offenders = []
        for class_name, cols in control_columns.items():
            for col_name in _TIMESTAMP_COLUMNS:
                if col_name not in cols:
                    continue
                src = cols[col_name]
                if not _server_default_is_now(src):
                    offenders.append(
                        f"{class_name}.{col_name}: {src!r} (no server_default=func.now())"
                    )
        assert not offenders, (
            "Law 21 AST gate (country_control.py): timestamp column(s) missing "
            "server_default=func.now():\n  " + "\n  ".join(offenders)
        )

    def test_enhancements_timestamp_columns_have_server_default_now(
        self, enhancements_columns: dict[str, dict[str, str]]
    ) -> None:
        offenders = []
        for class_name, cols in enhancements_columns.items():
            for col_name in _TIMESTAMP_COLUMNS:
                if col_name not in cols:
                    continue
                src = cols[col_name]
                if not _server_default_is_now(src):
                    offenders.append(
                        f"{class_name}.{col_name}: {src!r} (no server_default=func.now())"
                    )
        assert not offenders, (
            "Law 21 AST gate (country_enhancements.py): timestamp column(s) missing "
            "server_default=func.now():\n  " + "\n  ".join(offenders)
        )

    def test_control_no_python_side_default_on_timestamps(
        self, control_columns: dict[str, dict[str, str]]
    ) -> None:
        offenders = []
        for class_name, cols in control_columns.items():
            for col_name in _TIMESTAMP_COLUMNS:
                if col_name not in cols:
                    continue
                src = cols[col_name]
                if _python_side_default_present(src):
                    offenders.append(
                        f"{class_name}.{col_name}: Python-side default present"
                    )
        assert not offenders, (
            "Law 21: timestamp column(s) carry Python-side default= (forbidden):\n  "
            + "\n  ".join(offenders)
        )

    def test_enhancements_no_python_side_default_on_timestamps(
        self, enhancements_columns: dict[str, dict[str, str]]
    ) -> None:
        offenders = []
        for class_name, cols in enhancements_columns.items():
            for col_name in _TIMESTAMP_COLUMNS:
                if col_name not in cols:
                    continue
                src = cols[col_name]
                if _python_side_default_present(src):
                    offenders.append(
                        f"{class_name}.{col_name}: Python-side default present"
                    )
        assert not offenders, (
            "Law 21: timestamp column(s) carry Python-side default= (forbidden):\n  "
            + "\n  ".join(offenders)
        )

    def test_control_country_code_is_string_2(
        self, control_columns: dict[str, dict[str, str]]
    ) -> None:
        offenders = []
        for class_name, cols in control_columns.items():
            if "country_code" not in cols:
                offenders.append(f"{class_name}.country_code MISSING")
                continue
            src = cols["country_code"]
            if "String(2)" not in src:
                offenders.append(f"{class_name}.country_code is not String(2): {src!r}")
        assert not offenders, (
            f"Law 20 violation in country_control.py: {offenders}"
        )

    def test_enhancements_country_code_is_string_2(
        self, enhancements_columns: dict[str, dict[str, str]]
    ) -> None:
        offenders = []
        for class_name, cols in enhancements_columns.items():
            if "country_code" not in cols:
                offenders.append(f"{class_name}.country_code MISSING")
                continue
            src = cols["country_code"]
            if "String(2)" not in src:
                offenders.append(f"{class_name}.country_code is not String(2): {src!r}")
        assert not offenders, (
            f"Law 20 violation in country_enhancements.py: {offenders}"
        )


class TestCountryModelsInitNotVacuous:
    """The country models __init__.py must import both sub-modules so that
    architecture gates resolving models through the package cannot be vacuous.
    """

    def test_init_imports_country_control(self) -> None:
        src = _INIT_FILE.read_text(encoding="utf-8")
        assert "country_control" in src, (
            "domains/country/models/__init__.py must import country_control "
            "or the Law 21/20/23 gates for those models are vacuous."
        )

    def test_init_imports_country_enhancements(self) -> None:
        src = _INIT_FILE.read_text(encoding="utf-8")
        assert "country_enhancements" in src, (
            "domains/country/models/__init__.py must import country_enhancements "
            "or the Law 21/20/23 gates for those models are vacuous."
        )

    def test_control_models_load_through_init(self) -> None:
        """Importing through __init__ must actually yield the control models."""
        import domains.country.models as pkg

        for name in (
            "ShiftHandoverLog",
            "PaymentOrchestratorSync",
            "SupplierOnboardingSync",
            "DataResidencyRecord",
            "CountryMapConfig",
            "ShopWarehouseLocation",
            "LogisticsPartnerLocation",
            "ParcelLocationTracker",
        ):
            assert hasattr(pkg, name), (
                f"domains.country.models.__init__ does not export {name}; "
                f"the gate is vacuous for that model."
            )

    def test_enhancements_models_load_through_init(self) -> None:
        """Importing through __init__ must actually yield the enhancement models."""
        import domains.country.models as pkg

        for name in (
            "CountryFeatureFlag",
            "CountryStaffAssignment",
            "OmanDeliveryZone",
            "CountryConfigVersion",
            "SupplierKYCRequirement",
            "LogisticsPartnerKYCRequirement",
            "CountryCommissionRate",
            "CountryLocalization",
            "CountryPaymentAlias",
            "CountryLegalContract",
            "CountryCategoryTaxRate",
            "CountryCity",
            "CountryHolidayCalendar",
            "CountryGatewayConfig",
            "CountryCommunicationThread",
            "CountryCommissionRateHistory",
            "CountryLogisticsZone",
            "CountryPayoutRule",
        ):
            assert hasattr(pkg, name), (
                f"domains.country.models.__init__ does not export {name}; "
                f"the gate is vacuous for that model."
            )
