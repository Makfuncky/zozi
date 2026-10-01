"""Regression tests for customer security router (FILE-138 fix).

Proves:
- Router is no longer an orphan (endpoints exist, no TODO).
- Every protected endpoint uses require_feature (Law 4 / Law 88).
- Handlers delegate to a domain service, no raw SQL (Law 2).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from tests.modules._ast_helpers import (
    AUTH_DEPENDENCIES,
    BACKEND_ROOT,
    _handler_auth_names,
    _has_raw_sql,
    _find_route_handlers,
    parse_file,
)

MODULE = "customer"
SECURITY_ROUTER = BACKEND_ROOT / "modules" / MODULE / "routers" / "security.py"


def _handler_has_require_feature(func: ast.FunctionDef) -> bool:
    """Return True if the handler uses require_feature in any Depends call.

    Handles both direct ``Depends(require_feature(...))`` (nested Call) and
    ``_rf_gate = Depends(require_feature(...))`` patterns.
    """
    for dec in func.decorator_list:
        if isinstance(dec, ast.Call):
            for arg in dec.args:
                if _node_contains_require_feature(arg):
                    return True
    for default in func.args.defaults:
        if _node_contains_require_feature(default):
            return True
    return False


def _node_contains_require_feature(node) -> bool:
    """Recursively check whether an AST node contains a require_feature(...) call."""
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "require_feature":
            return True
        for arg in node.args:
            if _node_contains_require_feature(arg):
                return True
        for kw in node.keywords:
            if _node_contains_require_feature(kw.value):
                return True
    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id == "require_feature":
            return True
    return False


class TestCustomerSecurityRouterNotOrphan:
    """F-026 regression: router must have implemented endpoints."""

    def test_security_router_has_endpoints(self):
        source = SECURITY_ROUTER.read_text(encoding="utf-8")
        assert "TODO" not in source, "security.py still contains TODO — orphan router"

        tree = parse_file(SECURITY_ROUTER)
        handlers = _find_route_handlers(tree)
        assert len(handlers) > 0, "security.py has zero route handlers"

    def test_security_router_prefix(self):
        tree = parse_file(SECURITY_ROUTER)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "router":
                        if isinstance(node.value, ast.Call):
                            for kw in node.value.keywords:
                                if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                    assert kw.value.value == "/api/v1/customer/security"


class TestCustomerSecurityRouterLaw8788:
    """Law 87/88: auth + feature gate on every handler."""

    def test_all_handlers_have_auth_and_gate(self):
        tree = parse_file(SECURITY_ROUTER)
        failures = []
        for handler in _find_route_handlers(tree):
            auth = _handler_auth_names(handler)
            if not (auth & AUTH_DEPENDENCIES):
                failures.append(f"{handler.name} (no auth)")
            if not _handler_has_require_feature(handler):
                failures.append(f"{handler.name} (no gate)")
        assert not failures, f"Law 87/88 violations in security.py: {failures}"


class TestCustomerSecurityRouterLaw2:
    """Law 2: thin router — no raw SQL, delegates to services."""

    def test_no_raw_sql(self):
        tree = parse_file(SECURITY_ROUTER)
        assert not _has_raw_sql(tree), "security.py contains raw SQL — violates Law 2"

    def test_delegates_to_security_service(self):
        source = SECURITY_ROUTER.read_text(encoding="utf-8")
        tree = parse_file(SECURITY_ROUTER)
        handlers = _find_route_handlers(tree)
        assert len(handlers) > 0, "no handlers to test"
        assert "domains.security.services.core.security_service" in source, (
            "security.py must import from domains.security.services"
        )
        for handler in handlers:
            handler_src = ast.unparse(handler)
            assert "list_fraud_events" in handler_src, (
                f"handler {handler.name} does not call list_fraud_events"
            )


class TestCustomerSecurityRouterRequireFeaturePresent:
    """Nature check: require_feature must appear on every protected endpoint."""

    def test_require_feature_on_every_endpoint(self):
        tree = parse_file(SECURITY_ROUTER)
        handlers = _find_route_handlers(tree)
        assert len(handlers) > 0, "no handlers"
        for handler in handlers:
            assert _handler_has_require_feature(handler), (
                f"require_feature not found for handler {handler.name} — "
                f"endpoint lacks feature gate"
            )
