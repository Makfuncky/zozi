"""
Regression test for the audit-module consolidation (W3 fix).

Guarantees:
* `controllers/audit_controller.py` no longer exists (it was a facade).
* No backend module imports `controllers.audit_controller` (upward call W3).
* `utils/audit.py` is the canonical module exposing the required public API.

This test uses AST parsing only and does NOT import backend `models`, so it
runs even when `models/products.py` has its unrelated pre-existing import error.
"""

import ast
import os

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
UTILS_AUDIT = os.path.join(BACKEND, "utils", "audit.py")
AUDIT_QUERY = os.path.join(BACKEND, "services", "audit", "audit_query_service.py")
FACADE = os.path.join(BACKEND, "controllers", "audit_controller.py")

# `utils/audit.py` is the canonical WRITE primitive (importable from every layer).
UTILS_AUDIT_API = {"audit_log", "AuditAction"}
# Audit READ queries live in `services/audit/audit_query_service.py` per the
# circuit contract (DB reads belong in services, not in the utils leaf layer).
AUDIT_QUERY_API = {"get_audit_logs", "get_unique_actions"}


def _iter_py_files(root):
    skip_dirs = {"venv", ".venv", "__pycache__", "node_modules", ".git", "migrations", "alembic"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for name in filenames:
            if name.endswith(".py"):
                yield os.path.join(dirpath, name)


def _has_audit_controller_import(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "controllers.audit_controller":
                return True
            # `from controllers import audit_controller` form
            if module == "controllers" and any(
                alias.name == "audit_controller" for alias in node.names
            ):
                return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "controllers.audit_controller":
                    return True
    return False


def test_facade_deleted():
    assert not os.path.exists(FACADE), (
        "controllers/audit_controller.py must be deleted; audit logic lives in "
        "utils/audit (canonical)."
    )


def test_no_controller_audit_controller_imports():
    offenders = []
    for path in _iter_py_files(BACKEND):
        # scripts/ is a read-only audit harness; skip it.
        if os.sep + "scripts" + os.sep in path or path.endswith(
            os.path.join("scripts", "safe_structure_migration.py")
        ):
            continue
        try:
            tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
        except SyntaxError:
            continue
        if _has_audit_controller_import(tree):
            offenders.append(os.path.relpath(path, BACKEND))
    assert not offenders, (
        "Modules still importing controllers.audit_controller (W3): "
        + ", ".join(offenders)
    )


def test_utils_audit_exposes_canonical_api():
    assert os.path.exists(UTILS_AUDIT), "utils/audit.py must exist as canonical module"
    tree = ast.parse(open(UTILS_AUDIT, encoding="utf-8").read(), filename=UTILS_AUDIT)
    defined = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
    missing = UTILS_AUDIT_API - defined
    assert not missing, f"utils/audit.py missing public API: {sorted(missing)}"


def test_audit_query_service_exposes_read_api():
    assert os.path.exists(AUDIT_QUERY), (
        "services/audit/audit_query_service.py must exist for audit reads"
    )
    tree = ast.parse(open(AUDIT_QUERY, encoding="utf-8").read(), filename=AUDIT_QUERY)
    defined = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
    missing = AUDIT_QUERY_API - defined
    assert not missing, f"audit_query_service.py missing read API: {sorted(missing)}"


if __name__ == "__main__":
    test_facade_deleted()
    test_no_controller_audit_controller_imports()
    test_utils_audit_exposes_canonical_api()
    test_audit_query_service_exposes_read_api()
    print("ALL AUDIT CONTRACT TESTS PASSED")
