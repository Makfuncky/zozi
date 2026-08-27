"""Architecture gates enforcing the routers -> controllers -> services layering (W1).

These are the real, runnable gates (run: ``pytest tests/test_architecture_gates.py -q``).
They exist because a prior remediation pass claimed gates passed against a test file
that was never committed; this file is the source of truth.

W1 rules enforced here:
  * A ``service`` must NOT own a FastAPI router or route decorator (DB logic only).
  * A ``controller`` must be routing-metadata only (declare ``get``/``post``/... markers
    or live in ``modules/``); it must not instantiate ``APIRouter`` and must not own
    the DB transaction boundary (``db.add``/``db.commit``/etc. — those belong in
    ``services``). The historical ``infrastructure.routing.route_contract`` marker
    module was retired; HTTP routes are declared directly in module routers.
  * A ``router`` must be thin: it must not import ``models`` or own the DB
    transaction boundary (those belong in ``services``); routing is declared by
    controllers and the auto-generator. Legacy offenders are frozen in
    ``tests/_router_logic_baseline.txt`` and must only decrease.
  * ``main:app`` must import/boot and mount the remediated routes.

``services/location_service`` is exempt: it is a *standalone* FastAPI microservice
(``uvicorn providers.geo.main:app``), not part of the main app surface.
"""
from __future__ import annotations

import ast
import os

import pytest

def _find_backend_root() -> str:
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.exists(os.path.join(d, "main.py")) and os.path.isdir(os.path.join(d, "modules")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BACKEND = _find_backend_root()
SERVICES_DIR = os.path.join(BACKEND, "services")
CONTROLLERS_DIR = os.path.join(BACKEND, "controllers")
ROUTERS_DIR = os.path.join(BACKEND, "routers")

# Standalone microservice — its `app = FastAPI(...)` is intentional.
SERVICE_EXCLUDES = {"services/location_service"}

ROUTE_ATTRS = {"get", "post", "put", "patch", "delete", "websocket"}

# Unambiguous SQLAlchemy session write operations. A controller must never issue
# these — the transaction boundary belongs in services. ``add`` is deliberately
# narrow: ``set.add`` (used for dedup bookkeeping) is not a DB write, so it is
# excluded when the receiver is a locally-declared ``set(...)`` variable.
DB_WRITE_METHODS = {
    "commit",
    "add_all",
    "merge",
    "flush",
    "bulk_save_objects",
    "bulk_insert_mappings",
    "bulk_update_mappings",
    "bulk_save",
}

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


def _db_write_violations(tree: ast.Module):
    """Return a list of SQLAlchemy write operations performed in a module.

    Controllers declare the HTTP contract and delegate persistence to services;
    they must not own the transaction boundary. In-memory ``set.add`` bookkeeping
    (e.g. WebSocket connection managers) is excluded via the same narrowing used
    by the router baseline scanner — only real session writes (``db.add`` etc.)
    are reported. A chain mentioning a session name (``db``/``session``/...) is
    still treated as a real DB write.
    """
    from _gen_router_baseline import (
        SESSION_NAMES,
        _receiver_is_in_memory_set,
        _set_names_in_scope,
    )

    problems = []
    module_sets = _set_names_in_scope(tree)
    func_set_map = {
        fn: _set_names_in_scope(fn)
        for fn in ast.walk(tree)
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    def _local_sets_for(call):
        sets = set(module_sets)
        for fn, fsets in func_set_map.items():
            if any(child is call for child in ast.walk(fn)):
                sets |= fsets
        return sets

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            func = call.func
            if not isinstance(func, ast.Attribute):
                continue
            attr = func.attr
            if attr in DB_WRITE_METHODS:
                problems.append(f"{node.name}: db.{attr}(...) write in controller")
            elif attr == "add":
                local_sets = _local_sets_for(call)
                if not _receiver_is_in_memory_set(func.value, module_sets, local_sets):
                    problems.append(f"{node.name}: db.add(...) write in controller")
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
                "(declare HTTP markers or live in modules/). Violations:\n" + msg
            )


class TestControllersWriteNoDB:
    """Controllers are routing-metadata only (W1): the transaction boundary
    belongs in ``services``. Regression guard so a stray ``db.add/commit`` in a
    controller fails the build instead of silently re-introducing layering debt.
    """

    def test_controllers_do_not_write_to_db(self):
        violations = {}
        for path in _iter_py(CONTROLLERS_DIR):
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except SyntaxError as e:
                violations[os.path.relpath(path, BACKEND)] = [f"syntax error: {e}"]
                continue
            probs = _db_write_violations(tree)
            if probs:
                violations[os.path.relpath(path, BACKEND)] = probs
        if violations:
            msg = "\n".join(f"  {k}: {v}" for k, v in violations.items())
            raise AssertionError(
                "Controllers must not write to the DB (delegate to services). Violations:\n" + msg
            )


class TestNoNewBusinessLogicInRouters:
    """Routers must be thin (routers -> controllers -> services). A router that
    imports ``models`` or performs a DB write embeds business logic that belongs
    in ``services``. The baseline (``tests/_router_logic_baseline.txt``) freezes
    the current 124 legacy routers; the count must only DECREASE. This gate fails
    only on *new* offenders so the remediation can be chipped away safely.

    Regenerate the baseline after an intentional migration with
    ``python tests/_gen_router_baseline.py``.
    """

    def test_no_new_router_embeds_business_logic(self):
        from _gen_router_baseline import load_baseline, scan_router_files

        baseline = load_baseline()
        new_offenders = []
        for rel, imports_models, db_write in scan_router_files():
            if (imports_models or db_write) and rel not in baseline:
                reasons = []
                if imports_models:
                    reasons.append("imports models")
                if db_write:
                    reasons.append("db write")
                new_offenders.append(f"{rel} [{', '.join(reasons)}]")
        assert not new_offenders, (
            "New router(s) embed business logic (violates routers -> controllers "
            "-> services). Migrate to a controller + auto-generated router, then "
            "regenerate the baseline. New offenders:\n  "
            + "\n  ".join(sorted(new_offenders))
        )


class TestNoServiceCodeInRouters:
    """Regression guard: handler/service code must not live in the routers layer.

    The 54 ``*_service.py`` modules were previously stranded under
    ``routers/extracted/`` (no ``router=``, importing upward into controllers).
    They have been relocated to ``services/<domain>/``. This test ensures none
    reappear under ``routers/``.
    """

    def test_no_service_modules_under_routers(self):
        offenders = []
        for path in _iter_py(ROUTERS_DIR):
            rel = os.path.relpath(path, BACKEND).replace(os.sep, "/")
            if rel.endswith("_service.py"):
                offenders.append(rel)
        assert not offenders, (
            "Handler/service code found in the routers layer (must live in "
            "services/). Offenders:\n  " + "\n  ".join(offenders)
        )


class TestNoNewSdkInServices:
    """Services must not import external third-party SDKs directly — that is a
    provider concern (``providers/**``) wired by the service. Freeze the current
    offenders (P3 baseline); only *new* leakage fails the build, so debt can be
    chipped away safely per-feature. Regenerate the baseline after an intentional
    move: ``python tests/_gen_service_provider_baseline.py``.
    """

    def test_no_new_external_sdk_in_services(self):
        from _gen_service_provider_baseline import (
            load_baseline,
            scan_service_sdk_files,
        )

        baseline = load_baseline()
        new = []
        for rel, sdk in scan_service_sdk_files():
            if rel not in baseline:
                new.append(f"{rel} [{sdk}]")
        assert not new, (
            "New service imports an external SDK directly (violates "
            "services -> providers). Relocate to providers/**, or if this is an "
            "intentional legacy freeze, regenerate the baseline. New:\n  "
            + "\n  ".join(sorted(new))
        )


class TestAppBoot:
    def test_app_loads_and_mounts_remediated_routes(self):
        import sys

        # Boot ``main`` from a clean module state so this gate is
        # order-independent. Other architecture tests (e.g. the supplier
        # route-integrity guard) mutate ``sys.modules``; reusing a ``main``
        # imported against that polluted state made this gate intermittently
        # flaky. Purge ``main`` and the five actor router packages (the exact
        # set ``main._load_routers`` purges internally) before importing,
        # mirroring a fresh-process start.
        _ROUTER_PKGS = {
            "modules.customer.routers",
            "modules.supplier.routers",
            "modules.logistics.routers",
            "modules.admin.routers",
            "modules.employee.routers",
        }
        for _n in [
            n for n in list(sys.modules)
            if n == "main"
            or n in _ROUTER_PKGS
            or any(n.startswith(p + ".") for p in _ROUTER_PKGS)
        ]:
            del sys.modules[_n]

        import main  # noqa: F401
        assert main.app is not None

        # (1) The remediated country_versioning router must be mounted. Mounted
        # routers surface as ``_IncludedRouter`` with an empty ``.path``, so the
        # reliable source of truth is the generated OpenAPI path set.
        spec = main.app.openapi()
        mounted_paths = set(spec.get("paths", {}).keys())
        assert any("config-versions" in p for p in mounted_paths), \
            "Remediated router (country_versioning) is not mounted — check generated file."

        # (2) No *new* router-load failures beyond the known legacy ones. Use the
        # authoritative boot-health API (get_failed_imports /
        # get_package_failures, re-exported by main) instead of scraping log
        # strings — this is deterministic and independent of caplog capture
        # ordering, which previously let real failures pass silently.
        failed_submodules = {
            sub
            for _fails in main.get_failed_imports().values()
            for (sub, _err) in _fails
        }
        unexpected = failed_submodules - KNOWN_PREEXISTING_ROUTER_FAILURES
        assert not unexpected, f"Unexpected router load failures: {sorted(unexpected)}"
        assert not main.get_package_failures(), \
            f"Whole-package router import failures: {dict(main.get_package_failures())}"
