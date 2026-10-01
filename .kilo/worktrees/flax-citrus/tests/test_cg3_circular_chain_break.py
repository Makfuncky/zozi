"""
CG3 regression: the circular call chain
    controllers.supplier_controller → services.cash_management_service → controllers.supplier_controller
is broken by moving the full badge recalculation cycle into the services layer.

Guards:
1. `services.cash_management_service` must not import from `controllers` (no upward edge).
2. `services.supplier_badge_service` must not import from `controllers`.
3. The full cycle + refresh live in `services.supplier_badge_service` with the
   scheduler-facing signatures and result contract.
4. `controllers.supplier_controller` re-exports the same functions (same module
   identity) so routers/facades keep working.
"""
import importlib
import inspect
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _import(module: str):
    return importlib.import_module(module)


def _controllers_imports(module_file: Path) -> list[str]:
    """Static scan: any `from controllers...` / `import controllers...` line."""
    hits = []
    for line in module_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.search(r"(?:from controllers|import controllers)\b", line):
            hits.append(line.strip())
    return hits


def test_cash_management_service_has_no_controllers_import():
    hits = _controllers_imports(BACKEND / "services" / "cash_management_service.py")
    assert hits == [], f"service still imports from controllers: {hits}"


def test_supplier_badge_service_has_no_controllers_import():
    hits = _controllers_imports(BACKEND / "services" / "supplier_badge_service.py")
    assert hits == [], f"service still imports from controllers: {hits}"


def test_full_cycle_lives_in_service_with_scheduler_contract():
    svc = _import("services.supplier_badge_service")
    fn = svc.run_badge_recalculation_cycle
    sig = inspect.signature(fn)
    assert list(sig.parameters) == ["db"], f"unexpected signature {sig}"
    # Scheduler-facing result contract (see services/cash_management_service.py
    # execute_finance_cycle): the full cycle reports billing/recurring counters.
    src = inspect.getsource(fn)
    for key in ("suppliers_processed", "badges_changed", "billings_created", "recurring_billings_created"):
        assert key in src, f"cycle result lost contract key {key!r}"


def test_full_refresh_signature_matches_controller_callers():
    svc = _import("services.supplier_badge_service")
    fn = svc.refresh_supplier_badge
    sig = inspect.signature(fn)
    # routers call refresh_supplier_badge(user_id, db) positionally
    assert list(sig.parameters) == ["supplier_id", "db"], f"unexpected signature {sig}"


def test_controller_reexports_service_identity():
    sc = _import("controllers.supplier_controller")
    svc = _import("services.supplier_badge_service")
    for name in ("refresh_supplier_badge", "run_badge_recalculation_cycle"):
        assert getattr(sc, name).__module__ == "services.supplier_badge_service", name
        assert getattr(sc, name) is getattr(svc, name), name


def test_controller_keeps_public_badge_surface():
    sc = _import("controllers.supplier_controller")
    for name in (
        "compute_credibility_score",
        "list_supplier_badge_catalog",
        "list_supplier_badge_billing_history",
        "record_badge_billing_payment",
        "purchase_supplier_badge",
        "refresh_supplier_badge",
        "run_badge_recalculation_cycle",
        "admin_set_supplier_badge",
    ):
        assert hasattr(sc, name), f"controller lost public symbol {name}"


def test_facade_still_resolves():
    facade = _import("controllers.supplier.badge")
    for name in (
        "compute_credibility_score",
        "list_supplier_badge_catalog",
        "list_supplier_badge_billing_history",
        "record_badge_billing_payment",
        "purchase_supplier_badge",
        "refresh_supplier_badge",
        "run_badge_recalculation_cycle",
        "admin_set_supplier_badge",
    ):
        assert hasattr(facade, name), f"facade lost symbol {name}"
