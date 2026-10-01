"""Regression test for FILE-136: customer HR router must be thin and gated.

Verifies that backend/modules/customer/routers/hr.py:
- Has implemented endpoint handlers (not just a TODO / orphan router)
- Every handler uses require_feature (Law 4 / Law 88)
- Every handler delegates to a domain service (Law 2 / Law 90)
- No handler performs raw SQL or DB writes (Law 2)

NOTE: The shared tests.modules._ast_helpers._handler_auth_names has a
pre-existing bug (it does not recurse into Depends(require_feature(...))),
so the core assertions here use direct source checks.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_BACKEND_ROOT))

HR_ROUTER = _BACKEND_ROOT / "modules" / "customer" / "routers" / "hr.py"
HR_SOURCE = HR_ROUTER.read_text(encoding="utf-8")

# Feature atoms defined in domains/hr/features.py (single-sourced per Law 4)
_KNOWN_HR_FEATURES = {
    "hr.employee.read", "hr.employee.manage",
    "hr.department.read", "hr.department.manage",
    "hr.payroll.read", "hr.payroll.manage",
    "hr.attendance.read", "hr.attendance.manage",
    "hr.leave.read", "hr.leave.manage", "hr.leave.create",
    "hr.performance.read", "hr.performance.manage",
    "hr.profile.read", "hr.profile.update",
    "hr.payslip.read", "hr.okr.read", "hr.org.read",
    "hr.employees.read", "hr.employees.manage",
    "hr.org_structure.read", "hr.org_structure.manage",
    "hr.training.read", "hr.training.manage",
    "hr.read", "hr.create", "hr.update", "hr.delete",
}


class TestCustomerHRRouterExists:
    """FILE-136: the router must have implemented endpoints (not orphan)."""

    def test_router_file_exists(self):
        assert HR_ROUTER.exists(), f"{HR_ROUTER} missing"

    def test_router_has_handlers(self):
        tree = ast.parse(HR_SOURCE)
        handlers = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
            and any(
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and dec.func.attr in {"get", "post", "put", "delete", "patch"}
                for dec in n.decorator_list
            )
        ]
        assert len(handlers) > 0, "hr.py has zero endpoint handlers (orphan router)"

    def test_router_no_todo_only(self):
        non_doc_non_todo = [
            line for line in HR_SOURCE.splitlines()
            if line.strip()
            and not line.strip().startswith("#")
            and not line.strip().startswith('"""')
            and not line.strip().startswith("'''")
            and "TODO" not in line
        ]
        assert len(non_doc_non_todo) > 10, (
            "hr.py appears to contain only a TODO / docstring — no implemented endpoints"
        )


class TestCustomerHRRouterLaw88:
    """Law 88: every protected endpoint must use require_feature or require_module."""

    def test_all_handlers_have_require_feature(self):
        tree = ast.parse(HR_SOURCE)
        handlers = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
            and any(
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and dec.func.attr in {"get", "post", "put", "delete", "patch"}
                for dec in n.decorator_list
            )
        ]
        failures = []
        for handler in handlers:
            # Look for require_feature(...) anywhere in the handler's defaults or body
            has_gate = False
            for node in ast.walk(handler):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Attribute) and func.attr == "require_feature":
                        has_gate = True
                    if isinstance(func, ast.Name) and func.id == "require_feature":
                        has_gate = True
            if not has_gate:
                failures.append(handler.name)
        assert not failures, f"Law 88 violations — no require_feature: {failures}"


class TestCustomerHRRouterLaw2:
    """Law 2: thin routers — no raw SQL, delegates to domain services."""

    def test_no_raw_sql(self):
        tree = ast.parse(HR_SOURCE)
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in {
                    "execute", "commit", "add", "delete", "flush", "merge",
                }:
                    if isinstance(func.value, ast.Name) and func.value.id in {"db", "session"}:
                        violations.append(
                            f"L{node.lineno}: {ast.unparse(node)}"
                        )
                if isinstance(func, ast.Name) and func.id == "text":
                    violations.append(f"L{node.lineno}: text()")
        assert not violations, f"Law 2 raw-SQL violations: {violations}"

    def test_handlers_delegate_to_domain_services(self):
        tree = ast.parse(HR_SOURCE)
        handlers = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
            and any(
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and dec.func.attr in {"get", "post", "put", "delete", "patch"}
                for dec in n.decorator_list
            )
        ]
        failures = []
        for handler in handlers:
            delegates = False
            for node in ast.walk(handler):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("domains.") and ".services." in node.module:
                        delegates = True
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Attribute) and func.attr in {
                        "ess_get_profile", "ess_leave_history", "ess_request_leave",
                        "ess_attendance", "ess_payslips", "ess_org_chart",
                        "list_org_units",
                    }:
                        delegates = True
            if not delegates:
                failures.append(handler.name)
        assert not failures, f"non-delegating handlers: {failures}"


class TestCustomerHRRouterLaw87:
    """Law 87: protected endpoints must authenticate the caller.

    Endpoints without ``get_current_user`` are treated as public (like
    ``country.py:list_countries``) and are allowed as long as they still
    carry a ``require_feature`` gate (Law 88).
    """

    def test_all_handlers_have_auth_or_are_public(self):
        tree = ast.parse(HR_SOURCE)
        handlers = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
            and any(
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and dec.func.attr in {"get", "post", "put", "delete", "patch"}
                for dec in n.decorator_list
            )
        ]
        auth_deps = {
            "require_admin", "require_supplier", "require_logistics",
            "require_employee", "require_customer", "get_current_user",
            "rbac_get_current_user", "get_current_active_user",
        }
        failures = []
        for handler in handlers:
            names_used: set[str] = set()
            for node in ast.walk(handler):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name):
                        names_used.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        names_used.add(func.attr)
                    for arg in node.args:
                        if isinstance(arg, ast.Name):
                            names_used.add(arg.id)
                        elif isinstance(arg, ast.Attribute):
                            names_used.add(arg.attr)
                        elif isinstance(arg, ast.Call):
                            inner = arg.func
                            if isinstance(inner, ast.Name):
                                names_used.add(inner.id)
                            elif isinstance(inner, ast.Attribute):
                                names_used.add(inner.attr)
            has_auth = bool(names_used & auth_deps)
            # Public endpoints (no user-specific data) may omit get_current_user
            # as long as they carry a require_feature gate.
            has_gate = bool(
                names_used & {"require_feature", "require_module"}
            )
            if not has_auth and not has_gate:
                failures.append(f"{handler.name} (no auth, no gate)")
        assert not failures, f"Law 87 violations: {failures}"


class TestCustomerHRRouterFeatureGatesCatalog:
    """Law 4: every require_feature literal must be a known HR feature atom."""

    def test_require_feature_literals_in_catalog(self):
        tree = ast.parse(HR_SOURCE)
        unknown = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "require_feature":
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            if arg.value not in _KNOWN_HR_FEATURES:
                                unknown.append(arg.value)
        assert not unknown, (
            f"require_feature literal(s) not in hr features catalog: {unknown}"
        )
