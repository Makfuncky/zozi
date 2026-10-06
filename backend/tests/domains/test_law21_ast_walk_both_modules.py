"""Paired regression tests for Law 21 + Law 23 across logistics and suppliers models.

Walk ast.Assign AND ast.AnnAssign so the blind spot that let 40+ similar
defects survive a green suite is explicitly covered:

  - Every ``created_at`` / ``updated_at`` DateTime column in
    ``logistics_entities.py`` and ``suppliers.py`` MUST carry
    ``server_default=func.now()`` (DB-side), found via both Assign and
    AnnAssign AST node types.
  - Every model listed in ``domains.suppliers.models.__init__.__all__``
    actually exists as a class in ``suppliers.py``.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_LOGISTICS_MODEL = _BACKEND / "domains" / "logistics" / "models" / "logistics_entities.py"
_SUPPLIERS_MODEL = _BACKEND / "domains" / "suppliers" / "models" / "suppliers.py"
_SUPPLIERS_INIT = _BACKEND / "domains" / "suppliers" / "models" / "__init__.py"

_LOGISTICS_TABLES = {
    "logistics_category_pricing_rules",
    "logistics_partner_profiles",
    "logistics_partner_service_areas",
    "logistics_partners",
    "logistics_pricing_profiles",
    "logistics_vehicle_rules",
    "shipment_events",
    "shipments",
}

# ---------------------------------------------------------------------------
# AST helpers — walk BOTH Assign and AnnAssign
# ---------------------------------------------------------------------------
_AUDIT_COLUMNS = {"created_at", "updated_at"}


def _has_server_default_now(node: ast.AST) -> bool:
    """Return True if the AST node is a sa.Column(...) call with
    server_default=func.now() or server_default=sa.func.now()."""
    if not isinstance(node, ast.Call):
        return False
    for kw in node.keywords:
        if kw.arg != "server_default":
            continue
        sd = kw.value
        # server_default=func.now()  ->  Call node with attr 'now' or 'current_timestamp'
        if isinstance(sd, ast.Call):
            name = getattr(sd.func, "attr", None) or getattr(sd.func, "id", None)
            if name in {"now", "current_timestamp"}:
                return True
        # server_default=text('now()')  ->  Call with keyword arg text='now()'
        if isinstance(sd, ast.Call):
            for kw2 in sd.keywords:
                if kw2.arg == "text" and isinstance(kw2.value, ast.Constant):
                    if "now" in str(kw2.value.value).lower():
                        return True
    return False


def _is_datetime_call(node: ast.AST) -> bool:
    """True if the node is a DateTime() or DateTime(timezone=True) call."""
    if not isinstance(node, ast.Call):
        return False
    func_name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
    return func_name == "DateTime"


def _collect_datetime_columns(
    model_path: Path, target_tables: set[str],
) -> dict[str, dict[str, bool]]:
    """Return {tablename: {col_name: has_server_default}}.

    Walks BOTH ast.Assign and ast.AnnAssign so annotated column declarations
    are not silently missed.
    """
    source = ast.parse(model_path.read_text(encoding="utf-8"))
    result: dict[str, dict[str, bool]] = {}

    for node in ast.walk(source):
        if not isinstance(node, ast.ClassDef):
            continue

        tablename: str | None = None
        cols: dict[str, bool] = {}

        for stmt in node.body:
            # Capture __tablename__ from Assign OR AnnAssign
            tbn = None
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                tgt = stmt.targets[0]
                if isinstance(tgt, ast.Name) and tgt.id == "__tablename__":
                    if isinstance(stmt.value, ast.Constant):
                        tbn = stmt.value.value
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if stmt.target.id == "__tablename__":
                    tbn = _literal(stmt.value)

            if tbn:
                tablename = tbn
                continue

            # Capture column assignments from BOTH Assign AND AnnAssign
            col_name: str | None = None
            col_type_node: ast.AST | None = None

            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                tgt = stmt.targets[0]
                if isinstance(tgt, ast.Name):
                    col_name = tgt.id
                    col_type_node = stmt.value
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                col_name = stmt.target.id
                col_type_node = stmt.value

            if col_name in _AUDIT_COLUMNS and col_type_node is not None:
                has_sd = _has_server_default_now(col_type_node)
                cols[col_name] = has_sd

        if tablename and tablename in target_tables:
            result[tablename] = cols

    return result


def _literal(node):
    if isinstance(node, ast.Constant):
        return node.value
    return None


# ---------------------------------------------------------------------------
# Logistics tests
# ---------------------------------------------------------------------------
class TestLogisticsLaw21AllTimestampColumns:
    """Law 21: created_at and updated_at must carry server_default=func.now()
    across all 8 logistics tables, verified by walking Assign AND AnnAssign."""

    def test_all_tables_have_created_at_server_default(self):
        state = _collect_datetime_columns(_LOGISTICS_MODEL, _LOGISTICS_TABLES)
        missing_tables = sorted(set(_LOGISTICS_TABLES) - set(state))
        assert not missing_tables, (
            f"logistics_entities.py no longer declares tables: {missing_tables}"
        )
        offenders = sorted(
            f"{tbl}.{col}"
            for tbl, cols in sorted(state.items())
            for col, has_sd in sorted(cols.items())
            if col == "created_at" and not has_sd
        )
        assert not offenders, (
            f"Law 21 (Assign+AnnAssign walk): created_at missing "
            f"server_default=func.now() on: {offenders}"
        )

    def test_all_tables_have_updated_at_server_default(self):
        state = _collect_datetime_columns(_LOGISTICS_MODEL, _LOGISTICS_TABLES)
        offenders = sorted(
            f"{tbl}.{col}"
            for tbl, cols in sorted(state.items())
            for col, has_sd in sorted(cols.items())
            if col == "updated_at" and not has_sd
        )
        assert not offenders, (
            f"Law 21 (Assign+AnnAssign walk): updated_at missing "
            f"server_default=func.now() on: {offenders}"
        )

    def test_every_model_has_both_timestamp_columns(self):
        source = ast.parse(_LOGISTICS_MODEL.read_text(encoding="utf-8"))
        for node in ast.walk(source):
            if not isinstance(node, ast.ClassDef):
                continue
            tablename = None
            col_names: set[str] = set()
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    tgt = stmt.targets[0]
                    if isinstance(tgt, ast.Name):
                        if tgt.id == "__tablename__" and isinstance(stmt.value, ast.Constant):
                            tablename = stmt.value.value
                        else:
                            col_names.add(tgt.id)
                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    col_names.add(stmt.target.id)
            if tablename and tablename in _LOGISTICS_TABLES:
                missing = sorted(_AUDIT_COLUMNS - col_names)
                assert not missing, (
                    f"Law 23: {tablename} missing timestamp columns: {missing}"
                )


# ---------------------------------------------------------------------------
# Suppliers tests
# ---------------------------------------------------------------------------
_SUPPLIERS_TABLES = {
    "suppliers.supplier_profiles",
    "suppliers.supplier_documents",
    "suppliers.supplier_notification_preferences",
    "suppliers.supplier_badge_catalogs",
    "suppliers.supplier_badges",
    "suppliers.supplier_badge_billing_histories",
    "suppliers.supplier_disputes",
}


class TestSuppliersLaw21AllTimestampColumns:
    """Law 21: same Assign+AnnAssign walk over suppliers.py."""

    def _collect(self):
        source = ast.parse(_SUPPLIERS_MODEL.read_text(encoding="utf-8"))
        state: dict[str, dict[str, bool]] = {}
        for node in ast.walk(source):
            if not isinstance(node, ast.ClassDef):
                continue
            tablename = None
            cols: dict[str, bool] = {}
            for stmt in node.body:
                tbn = None
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    tgt = stmt.targets[0]
                    if isinstance(tgt, ast.Name) and tgt.id == "__tablename__":
                        if isinstance(stmt.value, ast.Constant):
                            tbn = stmt.value.value
                if tbn:
                    tablename = f"suppliers.{tbn}"
                    continue
                col_name = None
                col_type_node = None
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    tgt = stmt.targets[0]
                    if isinstance(tgt, ast.Name):
                        col_name = tgt.id
                        col_type_node = stmt.value
                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    col_name = stmt.target.id
                    col_type_node = stmt.value
                if col_name in _AUDIT_COLUMNS and col_type_node is not None:
                    cols[col_name] = _has_server_default_now(col_type_node)
            if tablename and tablename in _SUPPLIERS_TABLES:
                state[tablename] = cols
        return state

    def test_all_supplier_models_have_created_at_server_default(self):
        state = self._collect()
        offenders = sorted(
            f"{tbl}.{col}"
            for tbl, cols in sorted(state.items())
            for col, has_sd in sorted(cols.items())
            if col == "created_at" and not has_sd
        )
        assert not offenders, (
            f"Law 21 (Assign+AnnAssign): created_at missing "
            f"server_default=func.now() on: {offenders}"
        )

    def test_all_supplier_models_have_updated_at_server_default(self):
        state = self._collect()
        offenders = sorted(
            f"{tbl}.{col}"
            for tbl, cols in sorted(state.items())
            for col, has_sd in sorted(cols.items())
            if col == "updated_at" and not has_sd
        )
        assert not offenders, (
            f"Law 21 (Assign+AnnAssign): updated_at missing "
            f"server_default=func.now() on: {offenders}"
        )


# ---------------------------------------------------------------------------
# __init__.py existence test
# ---------------------------------------------------------------------------
class TestInitPyExportsMatchActualModels:
    """Every name exported by __init__.py must exist as a class in the module.

    Catches omissions (e.g. SupplierDispute missing from __init__.py before
    this fix) and typos that would cause ImportError at consumer import time.
    """

    def test_all_init_exports_exist_in_suppliers_module(self):
        source = ast.parse(_SUPPLIERS_MODEL.read_text(encoding="utf-8"))
        actual_classes = {
            node.name for node in ast.walk(source)
            if isinstance(node, ast.ClassDef)
        }

        init_source = ast.parse(_SUPPLIERS_INIT.read_text(encoding="utf-8"))
        exported_names: set[str] = set()
        for node in ast.walk(init_source):
            # Walk the from X import (A, B, C) aliases and __all__ list
            if isinstance(node, ast.ImportFrom) and node.module and "suppliers" in node.module:
                for alias in node.names:
                    exported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Assign) and len(node.targets) == 1:
                tgt = node.targets[0]
                if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant):
                                exported_names.add(elt.value)

        # Base is a special case — imported from infrastructure, not a class here
        exported_names.discard("Base")

        missing = sorted(exported_names - actual_classes)
        assert not missing, (
            f"__init__.py exports {missing!r} but they are not classes "
            f"in suppliers.py — consumers get ImportError"
        )

    def test_supplier_dispute_in_init_exports(self):
        """SupplierDispute must be importable from domains.suppliers.models."""
        from domains.suppliers.models import SupplierDispute  # noqa: F401

        assert SupplierDispute.__name__ == "SupplierDispute"
