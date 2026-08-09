"""W1 regression test for the cash-management router rescue.

Guards against re-introducing Layer-1 DB writes into the router or the
cash-management write controller, verifies the controller->service
delegation at runtime, and that the router delegates to the controller.
"""
from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent

_EXPECTED_WRITE_VERBS = {
    "add",
    "add_all",
    "commit",
    "flush",
    "delete",
    "merge",
    "bulk_insert_mappings",
    "bulk_save_objects",
    "bulk_update_mappings",
    "begin",
    "begin_nested",
    "savepoint",
}
_SESSION_NAMES = {
    "db",
    "session",
    "db_session",
    "sess",
    "_db",
    "_session",
    "_db_session",
    "_sess",
    "session_scope",
    "db_session_scope",
}

# Controller module-level write functions the router must delegate to.
_CONTROLLER_FNS = (
    "flag_transaction",
    "reconcile_transaction",
    "resolve_transaction_exception",
    "upsert_bank_settings",
    "record_vat_remittance",
    "create_bank_transaction",
    "import_bank_transactions",
    "auto_reconcile_transactions",
    "trigger_supplier_payouts",
    "trigger_logistics_payouts",
    "dispatch_transfer_batch",
    "record_cod_remittance",
    "verify_cod_remittance_receipt",
    "reject_cod_remittance_receipt",
    "record_badge_billing_payment",
)

# Singleton instance methods the controller delegates to.
_SERVICE_METHODS = (
    "flag_transaction",
    "reconcile_transaction",
    "resolve_transaction_exception",
    "upsert_bank_settings",
    "record_vat_remittance",
    "create_bank_transaction",
    "import_bank_transactions",
    "auto_reconcile_transactions",
    "trigger_supplier_payouts",
    "trigger_logistics_payouts",
    "dispatch_transfer_batch",
    "record_cod_remittance",
    "verify_cod_remittance_receipt",
    "reject_cod_remittance_receipt",
    "record_badge_billing_payment",
)


def _find_layer_writes(source: str) -> list[str]:
    tree = ast.parse(source)
    findings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            value = node.func.value
            if isinstance(value, ast.Name) and value.id in _SESSION_NAMES:
                if node.func.attr in _EXPECTED_WRITE_VERBS:
                    findings.append(f"{value.id}.{node.func.attr}")
    return findings


def _isolate_serializers(module, monkeypatch) -> None:
    for name in dir(module):
        if name.startswith("serialize_"):
            monkeypatch.setattr(module, name, lambda *a, **k: {})


@pytest.fixture(scope="module")
def router_src() -> str:
    return (_BACKEND_ROOT / "routers" / "cash_management.py").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def write_controller_src() -> str:
    return (
        _BACKEND_ROOT / "controllers" / "cash_management_write_controller.py"
    ).read_text(encoding="utf-8")


def test_router_has_no_layer1_writes(router_src: str) -> None:
    assert _find_layer_writes(router_src) == [], "cash_management router must not call db.<write>"


def test_write_controller_has_no_layer1_writes(write_controller_src: str) -> None:
    assert _find_layer_writes(write_controller_src) == [], (
        "cash_management write controller must not call db.<write>"
    )


def test_router_delegates_to_controller(router_src: str) -> None:
    for fn in _CONTROLLER_FNS:
        assert re.search(rf"\bwrite_ctrl\.{fn}\s*\(", router_src), (
            f"router must delegate to write_ctrl.{fn}"
        )


def test_modules_import() -> None:
    importlib.import_module("routers.public_cash_management_access")
    importlib.import_module("controllers.cash_management_write_controller")
    svc_mod = importlib.import_module("services.finance.cash_management_write_service")
    for fn in _SERVICE_METHODS:
        assert callable(getattr(svc_mod, fn, None)), f"missing service method {fn}"


def test_write_controller_delegates_to_service(monkeypatch) -> None:
    from unittest.mock import MagicMock

    import controllers.cash_management_write_controller as write_ctrl
    svc = importlib.import_module("services.finance.cash_management_write_service")

    _isolate_serializers(write_ctrl, monkeypatch)

    patched = {}
    for fn in _SERVICE_METHODS:
        m = MagicMock()
        patched[fn] = m
        monkeypatch.setattr(svc, fn, m)

    db = MagicMock()
    cu = {"id": 3}

    write_ctrl.flag_transaction(7, "suspicious", db)
    write_ctrl.reconcile_transaction(3, {"id": 11}, db)
    write_ctrl.resolve_transaction_exception(3, {"linked_order_id": 5}, cu, db)
    write_ctrl.upsert_bank_settings({"bank_name": "NBO"}, cu, db)
    write_ctrl.record_vat_remittance(
        {"amount_remitted": 1, "period_start": None, "period_end": None}, cu, db
    )
    write_ctrl.create_bank_transaction({"source": "bank", "transaction_type": "inflow",
                                        "category": "misc", "amount": 1}, db)
    write_ctrl.import_bank_transactions([{"a": 1}], cu, db, auto_reconcile=True)
    write_ctrl.auto_reconcile_transactions(cu, db, limit=10)
    write_ctrl.trigger_supplier_payouts(db, settlement_ids=[1])
    write_ctrl.trigger_logistics_payouts(db, settlement_ids=None)
    write_ctrl.dispatch_transfer_batch("supplier", cu, db, provider="csv")
    write_ctrl.record_cod_remittance(12, 25.0, cu, db)
    write_ctrl.verify_cod_remittance_receipt(3, cu, db, note="ok")
    write_ctrl.reject_cod_remittance_receipt(3, cu, db, note="bad")
    write_ctrl.record_badge_billing_payment(
        billing_id=8, payment_method="bank", current_admin=cu, db=db
    )

    missing = [n for n, m in patched.items() if not m.called]
    assert not missing, f"controller did not delegate: {missing}"
