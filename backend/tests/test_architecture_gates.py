"""Architecture gates enforcing the routers -> controllers -> services layering (W1).

These are the real, runnable gates (run: ``pytest tests/test_architecture_gates.py -q``).
They exist because a prior remediation pass claimed gates passed against a test file
that was never committed; this file is the source of truth.

W1 rules enforced here:
  * A ``service`` must NOT own a FastAPI router or route decorator (DB logic only).
  * A ``controller`` must be routing-metadata only (import ``get``/``post``/... from
    ``routers.generated.auto_router``); it must not instantiate ``APIRouter``.
  * ``main:app`` must import/boot and mount the remediated routes.

``services/location_service`` is exempt: it is a *standalone* FastAPI microservice
(``uvicorn services.location_service.main:app``), not part of the main app surface.
"""
from __future__ import annotations

import ast
import logging
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES_DIR = os.path.join(BACKEND, "services")
CONTROLLERS_DIR = os.path.join(BACKEND, "controllers")

# Standalone microservice — its `app = FastAPI(...)` is intentional.
SERVICE_EXCLUDES = {"services/location_service"}

ROUTE_ATTRS = {"get", "post", "put", "patch", "delete", "websocket"}

# Router-load failures that exist independently of this remediation (legacy,
# out-of-scope). New failures (e.g. from a broken generated router) must still fail.
KNOWN_PREEXISTING_ROUTER_FAILURES = {
    "admin_logistics_imports",
    "expense_controller",
    "operational_controller",
}


def _iter_py(root: str, excludes=()):
    for dirpath, _, files in os.walk(root):
        rel_dir = os.path.relpath(dirpath, BACKEND).replace(os.sep, "/")
        if any(rel_dir == ex or rel_dir.startswith(ex + "/") for ex in excludes):
            continue
        for fn in files:
            if fn.endswith(".py") and fn != "__init__.py":
                yield os.path.join(dirpath, fn)


def _router_violations(tree: ast.Module):
    """Return a list of human-readable routing violations in a module."""
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "fastapi":
            for alias in node.names:
                if alias.name == "APIRouter":
                    problems.append("imports APIRouter from fastapi")
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and isinstance(node.value, ast.Call):
                    fn = node.value.func
                    fn_name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
                    if tgt.id == "router" and fn_name == "APIRouter":
                        problems.append("router = APIRouter(...)")
                    if tgt.id == "app" and fn_name == "FastAPI":
                        problems.append("app = FastAPI(...)")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    if dec.func.attr in ROUTE_ATTRS:
                        problems.append(f"@{dec.func.attr}(...) route decorator on {node.name}")
    return problems


class TestNoFastAPIRoutersInServices:
    def test_no_router_definitions_in_services(self):
        violations = {}
        for path in _iter_py(SERVICES_DIR, SERVICE_EXCLUDES):
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except SyntaxError as e:
                violations[os.path.relpath(path, BACKEND)] = [f"syntax error: {e}"]
                continue
            probs = _router_violations(tree)
            if probs:
                violations[os.path.relpath(path, BACKEND)] = probs
        if violations:
            msg = "\n".join(f"  {k}: {v}" for k, v in violations.items())
            raise AssertionError(
                "Services must not own FastAPI routers/routes (W1). Violations:\n" + msg
            )


class TestControllersUseNoFastAPIRouters:
    def test_no_router_definitions_in_controllers(self):
        violations = {}
        for path in _iter_py(CONTROLLERS_DIR):
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except SyntaxError as e:
                violations[os.path.relpath(path, BACKEND)] = [f"syntax error: {e}"]
                continue
            probs = _router_violations(tree)
            if probs:
                violations[os.path.relpath(path, BACKEND)] = probs
        if violations:
            msg = "\n".join(f"  {k}: {v}" for k, v in violations.items())
            raise AssertionError(
                "Controllers must be routing-metadata only "
                "(import from routers.generated.auto_router). Violations:\n" + msg
            )


class TestAppBoot:
    def test_app_loads_and_mounts_remediated_routes(self, caplog):
        with caplog.at_level(logging.ERROR):
            import main  # noqa: F401
        assert main.app is not None

        # (1) The remediated country_versioning router must be mounted. Mounted
        # routers surface as ``_IncludedRouter`` with an empty ``.path``, so the
        # reliable source of truth is the generated OpenAPI path set.
        spec = main.app.openapi()
        mounted_paths = set(spec.get("paths", {}).keys())
        assert any("config-versions" in p for p in mounted_paths), \
            "Remediated router (country_versioning) is not mounted — check generated file."

        # (2) No *new* router-load failures beyond the known legacy ones.
        failed = [r.getMessage() for r in caplog.records if "Failed to load" in r.getMessage()]
        failed_names = set()
        for msg in failed:
            body = msg.split(":", 1)[1] if ":" in msg else msg
            failed_names.update(n.strip() for n in body.split(","))
        unexpected = failed_names - KNOWN_PREEXISTING_ROUTER_FAILURES
        assert not unexpected, f"Unexpected router load failures: {sorted(unexpected)}"
