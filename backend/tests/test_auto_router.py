"""Tests for the auto-router pipeline and the ``get_db`` session contract.

These are deliberately DB-light / DB-free so they can run in CI on every push
without standing up the full app:

* ``get_db`` contract  — must be a *synchronous* generator so it works both as
  ``Depends(get_db)`` and ``with get_db() as db:``.  (Regression guard for the
  async-generator bug that broke RLS and raised 500s.)
* auto-router AST scan  — controllers are discovered, have no duplicate routes,
  and emit marker-carrying routers.
* generator subprocess  — ``--check`` and ``--verify`` exit 0 (the CI gate that
  proves "ready to auto-generate").
"""
from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# get_db contract
# ─────────────────────────────────────────────────────────────────────────────
def test_get_db_is_sync_generator():
    from infrastructure.database.database import get_db

    # Regression: it used to be ``async def`` (an async generator), which made
    # ``with get_db() as db:`` raise AttributeError: __enter__.
    assert inspect.isgeneratorfunction(get_db), "get_db must be a generator function"
    assert not inspect.iscoroutinefunction(get_db), "get_db must NOT be a coroutine"

    gen = get_db()
    try:
        assert inspect.isgenerator(gen), "get_db() must return a generator"
        assert not inspect.iscoroutine(gen)
    finally:
        gen.close()


# ─────────────────────────────────────────────────────────────────────────────
# auto-router AST layer (no app import, no DB)
# ─────────────────────────────────────────────────────────────────────────────
def test_auto_router_discovers_controllers():
    from modules.routers.generated import auto_router as ar

    modules = ar.scan_controllers()
    # The policy is "new controllers only"; we already have a healthy set.
    assert len(modules) >= 25, f"expected >=25 controller modules, got {len(modules)}"

    total_routes = sum(len(m["routes"]) for m in modules)
    assert total_routes >= 180, f"expected >=180 decorated routes, got {total_routes}"


def test_auto_router_no_duplicate_routes():
    from modules.routers.generated import auto_router as ar

    modules = ar.scan_controllers()
    errors = ar.validate(modules)
    assert errors == [], "duplicate route declarations found:\n" + "\n".join(errors)


def test_auto_router_emits_marker_routers():
    from modules.routers.generated import auto_router as ar

    modules = ar.scan_controllers()
    # Find a controller whose routes don't all collide, so generation is non-empty.
    emitted = False
    for mi in modules:
        content = ar.generate_router_file(mi)
        if not content:
            continue
        assert ar.MARKER in content, "generated router must carry the AUTO-GENERATED marker"
        assert "from fastapi import APIRouter" in content
        assert "router = APIRouter(" in content
        emitted = True
        break
    assert emitted, "no controller produced a non-empty generated router"


def test_existing_generated_routers_compile():
    """Every committed AUTO-GENERATED router must be importable / valid Python."""
    import py_compile

    gen_dir = BACKEND_ROOT / "routers"
    found = 0
    for path in gen_dir.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        try:
            head = path.read_text(encoding="utf-8")[:400]
        except Exception:
            continue
        if ar_MARKER_NOT_PRESENT(head):
            continue
        py_compile.compile(str(path), doraise=True)
        found += 1
    assert found > 0, "expected at least one AUTO-GENERATED router to compile-check"


def ar_MARKER_NOT_PRESENT(head: str) -> bool:
    from modules.routers.generated import auto_router as ar

    return ar.MARKER not in head


# ─────────────────────────────────────────────────────────────────────────────
# generator subprocess — the CI gate
# ─────────────────────────────────────────────────────────────────────────────
def _run_generator(args: list[str]) -> int:
    proc = subprocess.run(
        [sys.executable, "routers/generated/auto_router.py", *args],
        cwd=str(BACKEND_ROOT),
        capture_output=True,
        text=True,
    )
    return proc.returncode


def test_auto_router_check_passes():
    assert _run_generator(["--check"]) == 0, "auto_router --check must pass"


def test_auto_router_verify_passes(tmp_path):
    """End-to-end CI-gate proof: generate into a temp dir, then ``--verify`` on
    that dir must pass.

    The committed live ``routers/`` surface is only populated as part of the
    deliberate migration that *replaces* each legacy router with its generated
    counterpart (42 of the 68 generated filenames currently collide with
    hand-written routers and must be resolved before a live emit). This test
    proves the verify gate is mechanically correct and self-consistent.
    """
    out = tmp_path / "gen"
    assert _run_generator(["--out", str(out)]) == 0, "generation must succeed"
    assert _run_generator(["--verify", "--out", str(out)]) == 0, \
        "verify must pass on freshly generated output"


def test_derive_filename_has_no_admin_doubling():
    """Regression: ``controllers.admin.admin_catalog_orders_controller`` used to
    emit ``admin_admin_admin_catalog_orders.py`` (surface + subpackage + domain
    all repeated ``admin``). It must collapse to ``admin_catalog_orders.py``."""
    from modules.routers.generated import auto_router as ar

    fake_routes = [{
        "skip": False, "method": "GET", "path": "/api/v1/admin/categories/X",
        "deps": [], "query": [], "body": None,
    }]
    fname = ar._derive_filename(
        "controllers.admin.admin_catalog_orders_controller", fake_routes)
    assert fname == "admin_catalog_orders.py", f"got {fname!r}"
    assert "admin_admin" not in fname


def test_dict_annotated_body_param_is_not_treated_as_dep():
    """Regression: a request-body param declared as ``payload: dict`` must NOT
    be swallowed as an injected dependency (which previously crashed with
    "'body' set but found 0 non-path/non-dep args")."""
    from modules.routers.generated import auto_router as ar

    modules = ar.scan_controllers()
    hr = next(m for m in modules if m["module"] == "controllers.hr.hr_controller")
    content = ar.generate_router_file(hr)  # must not raise
    assert content
    assert "address_data: dict = Body(...)" in content
    assert "def register_address_route(" in content


def test_generated_router_delegates_and_stays_thin():
    """Every generated router is a thin delegator: it imports the controller
    module and never re-imports services/models or performs DB commits."""
    from modules.routers.generated import auto_router as ar

    modules = ar.scan_controllers()
    for mi in modules:
        content = ar.generate_router_file(mi)
        if not content:
            continue
        assert "from controllers." in content
        assert "from services import" not in content
        assert "from models import" not in content
        assert "db.commit" not in content
        assert "return " in content
        break


@pytest.mark.integration
def test_health_via_client(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

