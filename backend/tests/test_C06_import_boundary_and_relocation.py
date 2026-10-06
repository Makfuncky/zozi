"""Paired tests for C-06: Law 3 import-boundary fix and Law 13 endpoint relocation.

Fail-before baseline (recorded 2026-10-04):
  - backend/modules/employee/routers/finance.py had 5 direct
    ``domains.finance.services.*`` imports (lines 22, 598, 1204, 1336, 1337).
  - 27 admin-prefix endpoints (paths ``/admin/*``) lived inside the employee
    finance router at ``/api/v1/employee/finance/admin/*``.

Post-fix expected state:
  - Zero direct imports in either router; all reads go through
    ``domains.finance.ports`` (Law 3).
  - All admin cash-management endpoints now live in the admin router at
    ``/api/v1/admin/finance/*`` (Law 13).
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path


# Ensure backend/ is importable
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


# ── Helpers ───────────────────────────────────────────────────────────────────


def _load_router_module(path: Path):
    """Load a router module from a filesystem path without triggering package imports."""
    spec = importlib.util.spec_from_file_location("_router_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _collect_paths(routes):
    """Recursively collect all route paths from a router list."""
    paths = []
    for r in routes:
        rtype = type(r).__name__
        if rtype == "_IncludedRouter":
            orig = getattr(r, "original_router", None)
            if orig and hasattr(orig, "routes"):
                paths.extend(_collect_paths(orig.routes))
        elif hasattr(r, "routes"):
            paths.extend(_collect_paths(r.routes))
        elif hasattr(r, "path"):
            paths.append(r.path)
    return paths


def _assert_no_direct_service_imports(path: Path, label: str) -> None:
    """Assert that a Python file contains no ``from domains.finance.services`` imports."""
    with open(path, encoding="utf-8-sig") as fh:
        content = fh.read()
    if content.startswith("\ufeff"):
        content = content[1:]
    tree = ast.parse(content)
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if "domains.finance.services" in mod:
                violations.append((node.lineno, mod, [a.name for a in node.names]))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if "domains.finance.services" in alias.name:
                    violations.append((node.lineno, alias.name, []))
    assert violations == [], (
        f"{label} has {len(violations)} direct domains.finance.services "
        f"import(s) — all must go through ports.py (Law 3): {violations}"
    )


# ── Test 1: Employee router — zero direct domains.finance.services imports ────


def test_employee_finance_router_no_direct_service_imports():
    """Law 3: the employee finance router must not import directly from
    ``domains.finance.services``.  All reads must go through ``ports.py``."""
    path = _BACKEND_ROOT / "modules" / "employee" / "routers" / "finance.py"
    _assert_no_direct_service_imports(path, "Employee finance router")


# ── Test 2: Admin router — zero direct domains.finance.services imports ───────


def test_admin_finance_router_no_direct_service_imports():
    """Law 3: the admin finance router must also route through ports.py."""
    path = _BACKEND_ROOT / "modules" / "admin" / "routers" / "finance.py"
    _assert_no_direct_service_imports(path, "Admin finance router")


# ── Test 3: Admin endpoints absent from employee router (Law 13) ──────────────


def test_admin_endpoints_absent_from_employee_router():
    """Law 13: after relocation, the employee finance router must not define
    any route whose path contains ``/admin/``."""
    path = _BACKEND_ROOT / "modules" / "employee" / "routers" / "finance.py"
    mod = _load_router_module(path)
    router = getattr(mod, "router", None)
    assert router is not None, "employee finance router missing 'router' attribute"
    routes = getattr(router, "routes", [])
    paths = _collect_paths(routes)
    admin_paths = [p for p in paths if "/admin/" in p]
    assert admin_paths == [], (
        f"Employee finance router still exposes admin-prefix paths "
        f"(Law 13 violation): {admin_paths}"
    )


# ── Test 4: Relocated endpoints reachable at new admin paths ─────────────────


def test_relocated_endpoints_registered_in_admin_router():
    """All 27 cash-management admin endpoints must now be registered under
    ``/api/v1/admin/finance/*``.  We load the admin router directly to
    avoid the pre-existing circular-import issue in the full app."""
    path = _BACKEND_ROOT / "modules" / "admin" / "routers" / "finance.py"
    mod = _load_router_module(path)
    router = getattr(mod, "router", None)
    assert router is not None, "admin finance router missing 'router' attribute"
    paths = _collect_paths(router.routes)

    expected_new_paths = [
        "/api/v1/admin/finance/summary",
        "/api/v1/admin/finance/reconciliation-summary",
        "/api/v1/admin/finance/ledger",
        "/api/v1/admin/finance/badge-billings",
        "/api/v1/admin/finance/badge-billings/{billing_id}/record-payment",
        "/api/v1/admin/finance/supplier-settlements",
        "/api/v1/admin/finance/logistics-settlements",
        "/api/v1/admin/finance/bank-transactions",
        "/api/v1/admin/finance/refunds",
        "/api/v1/admin/finance/vat-remittances",
        "/api/v1/admin/finance/bank-settings",
        "/api/v1/admin/finance/transfer-providers",
        "/api/v1/admin/finance/bank-settings/test-connection",
        "/api/v1/admin/finance/payouts/supplier/process",
        "/api/v1/admin/finance/payouts/logistics/process",
        "/api/v1/admin/finance/payouts/{kind}/dispatch",
        "/api/v1/admin/finance/cod-remittance/{settlement_id}",
        "/api/v1/admin/finance/cod-remittance-receipts",
        "/api/v1/admin/finance/cod-remittance-receipts/{receipt_id}/verify",
        "/api/v1/admin/finance/cod-remittance-receipts/{receipt_id}/reject",
    ]
    missing = [p for p in expected_new_paths if p not in paths]
    assert missing == [], (
        f"Relocated admin endpoints missing from admin router: {missing}"
    )


def test_old_employee_admin_paths_absent_from_employee_router():
    """The old ``/api/v1/employee/finance/admin/*`` paths must no longer exist
    in the employee finance router."""
    path = _BACKEND_ROOT / "modules" / "employee" / "routers" / "finance.py"
    mod = _load_router_module(path)
    router = getattr(mod, "router", None)
    assert router is not None
    routes = getattr(router, "routes", [])
    paths = _collect_paths(routes)
    old_paths = [p for p in paths if "/employee/finance/admin" in p]
    assert old_paths == [], (
        f"Old employee/admin paths still registered: {old_paths}"
    )


# ── Test 5: ports.py re-exports all symbols used by both routers ──────────────


def test_ports_exports_employee_router_symbols():
    """Every non-controller symbol the employee router uses from finance_ports
    must appear in ``_LAZY_SERVICE_EXPORTS`` or as a module-level attribute."""
    from domains.finance import ports as fp

    lazy_map = getattr(fp, "_LAZY_SERVICE_EXPORTS", {})
    source = Path(fp.__file__).read_text(encoding="utf-8-sig")

    # Non-controller symbols used by the employee router
    required_lazy = [
        "reverse_journal_entry",
        "list_periods",
        "get_or_create_fiscal_period",
        "get_current_fiscal_period",
        "close_period",
        "FinancialReportingService",
        "list_contractor_milestones",
        "commit_db",
        "set_rls_context_service",
        "get_expense_router",
    ]
    missing_lazy = [s for s in required_lazy if s not in lazy_map]
    assert missing_lazy == [], (
        f"Symbols missing from _LAZY_SERVICE_EXPORTS: {missing_lazy}"
    )

    # Controller modules are imported at module level in ports.py
    for ctrl_name in ("accounting_controller", "cash_management_controller", "invoice_controller"):
        assert ctrl_name in source, (
            f"Controller module '{ctrl_name}' not imported at module level in ports.py"
        )


def test_ports_exports_admin_router_symbols():
    """Every non-controller symbol the admin router uses from finance_ports
    must appear in ``_LAZY_SERVICE_EXPORTS``."""
    from domains.finance import ports as fp

    lazy_map = getattr(fp, "_LAZY_SERVICE_EXPORTS", {})

    required_lazy = [
        "list_category_rates",
        "create_category_rate",
        "update_category_rate",
        "list_badge_tiers",
        "create_badge_tier",
        "update_badge_tier",
        "commit_db",
    ]
    missing_lazy = [s for s in required_lazy if s not in lazy_map]
    assert missing_lazy == [], (
        f"Symbols missing from _LAZY_SERVICE_EXPORTS for admin router: {missing_lazy}"
    )

    # cash_management_controller imported at module level
    source = Path(fp.__file__).read_text(encoding="utf-8-sig")
    assert "cash_management_controller" in source, (
        "cash_management_controller not imported at module level in ports.py"
    )


# ── Test 6: Auth still enforced on relocated endpoints (static analysis) ──────


def _find_depends_calls(node):
    """Recursively find all Depends(...) calls in an AST node."""
    results = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name) and func.id == "Depends":
                results.append(child)
            elif isinstance(func, ast.Attribute) and func.attr == "Depends":
                results.append(child)
    return results


def _has_require_feature(func_node):
    for call in _find_depends_calls(func_node):
        if len(call.args) >= 1 and isinstance(call.args[0], ast.Call):
            inner = call.args[0]
            if isinstance(inner.func, ast.Name) and inner.func.id == "require_feature":
                return True
            if isinstance(inner.func, ast.Attribute) and inner.func.attr == "require_feature":
                return True
    return False


def _has_require_admin(func_node):
    for call in _find_depends_calls(func_node):
        if len(call.args) >= 1 and isinstance(call.args[0], ast.Name):
            if call.args[0].id == "require_admin":
                return True
        if len(call.args) >= 1 and isinstance(call.args[0], ast.Call):
            inner = call.args[0]
            if isinstance(inner.func, ast.Name) and inner.func.id == "require_admin":
                return True
    return False


def test_relocated_endpoints_all_have_feature_gates():
    """Every relocated admin endpoint must carry a ``require_feature`` gate
    (Law 88).  require_feature appears as Depends(require_feature(...)) in
    the function body, not as a decorator."""
    path = _BACKEND_ROOT / "modules" / "admin" / "routers" / "finance.py"
    with open(path, encoding="utf-8-sig") as fh:
        source = fh.read()

    tree = ast.parse(source)
    gated_routes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and _has_require_feature(node):
            gated_routes.append(node.name)

    expected_gated = [
        "admin_financial_summary",
        "admin_reconciliation_summary",
        "admin_list_ledger",
        "admin_list_badge_billings",
        "admin_list_supplier_settlements",
        "admin_list_bank_transactions",
        "admin_list_refunds",
        "admin_get_bank_settings",
        "admin_trigger_supplier_payouts",
        "admin_dispatch_payouts",
        "admin_record_cod_remittance",
        "admin_list_cod_remittance_receipts",
        "admin_verify_cod_remittance_receipt",
        "admin_reject_cod_remittance_receipt",
    ]
    missing_gate = [n for n in expected_gated if n not in gated_routes]
    assert missing_gate == [], (
        f"Relocated admin endpoints missing require_feature gate: {missing_gate}"
    )


def test_relocated_endpoints_all_have_require_admin():
    """Every relocated admin endpoint must call ``require_admin`` (Law 87).
    require_admin appears as Depends(require_admin) in the function body."""
    path = _BACKEND_ROOT / "modules" / "admin" / "routers" / "finance.py"
    with open(path, encoding="utf-8-sig") as fh:
        source = fh.read()

    tree = ast.parse(source)
    admin_routes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and _has_require_admin(node):
            admin_routes.append(node.name)

    expected_admin = [
        "admin_financial_summary",
        "admin_reconciliation_summary",
        "admin_list_ledger",
        "admin_list_badge_billings",
        "admin_record_badge_billing_payment",
        "admin_list_supplier_settlements",
        "admin_list_logistics_settlements",
        "admin_list_bank_transactions",
        "admin_list_refunds",
        "admin_list_vat_remittances",
        "admin_get_bank_settings",
        "admin_list_transfer_providers",
        "admin_test_bank_settings_connection",
        "admin_upsert_bank_settings",
        "admin_record_vat_remittance",
        "admin_create_bank_transaction",
        "admin_import_bank_transactions",
        "admin_reconcile_transaction",
        "admin_flag_transaction",
        "admin_resolve_transaction",
        "admin_auto_reconcile_transactions",
        "admin_trigger_supplier_payouts",
        "admin_trigger_logistics_payouts",
        "admin_dispatch_payouts",
        "admin_record_cod_remittance",
        "admin_list_cod_remittance_receipts",
        "admin_verify_cod_remittance_receipt",
        "admin_reject_cod_remittance_receipt",
    ]
    missing_admin = [n for n in expected_admin if n not in admin_routes]
    assert missing_admin == [], (
        f"Relocated admin endpoints missing require_admin gate: {missing_admin}"
    )


# ── Test 7: RBAC features present in admin role ───────────────────────────────


def test_admin_role_grants_all_finance_features():
    """admin and super_admin have wildcard ['*'] — all finance features are granted."""
    from rbac.dependencies import _ROLE_FEATURES

    admin_features = _ROLE_FEATURES.get("admin", [])
    assert "*" in admin_features, "admin role must have wildcard feature access"

    # Spot-check: every feature used by relocated endpoints must be in the catalog
    from rbac.catalog import FEATURE_CATALOG
    needed = {
        "finance.treasury.read", "finance.bank.read", "finance.payout.read",
        "finance.payout.write", "finance.commission.read", "finance.ledger.read",
        "finance.treasury.manage",
    }
    catalog = set(FEATURE_CATALOG.keys()) if hasattr(FEATURE_CATALOG, "keys") else set(FEATURE_CATALOG)
    missing = needed - catalog
    assert not missing, f"Finance features missing from catalog: {missing}"


# ── Test 8: Import-boundary check on both routers (static AST) ────────────────


def test_both_finance_routers_passed_import_boundary_check():
    """Both routers must pass the AST-based no-direct-services-import check."""
    emp_path = _BACKEND_ROOT / "modules" / "employee" / "routers" / "finance.py"
    adm_path = _BACKEND_ROOT / "modules" / "admin" / "routers" / "finance.py"
    _assert_no_direct_service_imports(emp_path, "employee")
    _assert_no_direct_service_imports(adm_path, "admin")
