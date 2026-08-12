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
    from db.database import get_db

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
    from routers.generated import auto_router as ar

    modules = ar.scan_controllers()
    # The policy is "new controllers only"; we already have a healthy set.
    assert len(modules) >= 25, f"expected >=25 controller modules, got {len(modules)}"

    total_routes = sum(len(m["routes"]) for m in modules)
    assert total_routes >= 180, f"expected >=180 decorated routes, got {total_routes}"


def test_auto_router_no_duplicate_routes():
    from routers.generated import auto_router as ar

    modules = ar.scan_controllers()
    errors = ar.validate(modules)
    assert errors == [], "duplicate route declarations found:\n" + "\n".join(errors)


def test_auto_router_emits_marker_routers():
    from routers.generated import auto_router as ar

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
    from routers.generated import auto_router as ar

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


def test_auto_router_verify_passes():
    assert _run_generator(["--verify"]) == 0, "auto_router --verify must pass (in sync)"


@pytest.mark.integration
def test_health_via_client(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
