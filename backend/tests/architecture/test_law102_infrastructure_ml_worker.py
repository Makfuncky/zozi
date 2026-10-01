"""Law 102 gate + behaviour regression for ``infrastructure/ml/worker.py``.

FILE-65 / LAW-EXTRACT-018: the ML worker used to import
``providers.image.bg_remover.create_rembg_session`` from inside
``_warmup_models()``, creating a forbidden ``infrastructure -> providers``
arrow (ARCHITECTURE_STACK.md Law 102: ``infrastructure`` MUST NOT import
``domains/``, ``modules/``, ``rbac/`` or ``providers/``).

The fix inverts the dependency: the warm-up is a port, ``_warmup_models()``
takes an injected zero-argument hook, and the ``jobs``-layer process boundary
(which Law 103 lets import ``providers``) supplies the provider-backed
implementation.

These tests lock in both halves:
  * the import direction stays clean at every scope (module-level AND lazy
    function-body imports), and
  * the warm-up still runs, still runs exactly once, and still degrades
    non-fatally when the hook raises.

Note: the existing canonical Law 1 gate
(``backend/scripts/_gen_import_laws_baseline.py``) only inspects module-scope
imports and only forbids ``domains``/``modules``, so this file deliberately
walks the whole AST instead.
"""
from __future__ import annotations

import ast
import logging
import pathlib
import sys
import types

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_WORKER_PATH = _BACKEND_ROOT / "infrastructure" / "ml" / "worker.py"
_BASELINE_PATH = _BACKEND_ROOT / "tests" / "architecture" / "_import_laws_baseline.txt"

# Law 102: layers ``infrastructure`` must never import.
_FORBIDDEN_ROOTS = frozenset({"domains", "modules", "rbac", "providers"})


# ---------------------------------------------------------------------------
# Import-direction regression (the finding itself)
# ---------------------------------------------------------------------------
def _imported_roots(tree: ast.AST) -> list[str]:
    """Top-level package name of every import in ``tree``, at any scope."""
    roots: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import, cannot escape the package
                continue
            roots.append((node.module or "").split(".")[0])
    return roots


def test_ml_worker_does_not_import_above_infrastructure() -> None:
    """No ``domains``/``modules``/``rbac``/``providers`` import anywhere in the file."""
    assert _WORKER_PATH.exists(), f"expected {_WORKER_PATH} to exist"
    tree = ast.parse(_WORKER_PATH.read_text(encoding="utf-8"))
    offenders = sorted(set(_imported_roots(tree)) & _FORBIDDEN_ROOTS)
    assert not offenders, (
        "Law 102 violation: infrastructure/ml/worker.py must not import "
        f"{offenders} (lazy function-body imports count too, not just "
        "module-level ones)"
    )


def test_ml_worker_is_not_frozen_in_the_law1_debt_baseline() -> None:
    """The file must never re-enter the frozen Law 1 offender baseline."""
    if not _BASELINE_PATH.exists():
        pytest.skip("import-laws baseline file not present")
    frozen = {
        line.strip()
        for line in _BASELINE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    rel = "infrastructure/ml/worker.py"
    assert rel not in frozen, (
        f"{rel} is frozen in _import_laws_baseline.txt; the Law 102 fix must "
        "keep it out of the debt baseline"
    )


def test_ml_worker_still_wires_its_own_infrastructure_deps() -> None:
    """The worker keeps polling through ``infrastructure`` (downward only)."""
    tree = ast.parse(_WORKER_PATH.read_text(encoding="utf-8"))
    roots = set(_imported_roots(tree))
    assert "infrastructure" in roots, (
        "the job loop must keep importing its collaborators from "
        "infrastructure.* (downward arrow preserved)"
    )


# ---------------------------------------------------------------------------
# Behaviour regression (the warm-up still works)
# ---------------------------------------------------------------------------
@pytest.fixture()
def worker(monkeypatch):
    """Import the module under test and keep the import side effects isolated."""
    sys.path.insert(0, str(_BACKEND_ROOT))
    try:
        import infrastructure.ml.worker as mod  # noqa: PLC0415
    finally:
        sys.path.remove(str(_BACKEND_ROOT))
    return mod


def test_warmup_invokes_the_injected_hook_once(worker, caplog) -> None:
    """Outcome: a supplied hook is called exactly once and success is logged."""
    calls: list[int] = []

    with caplog.at_level(logging.INFO, logger="ml_worker"):
        worker._warmup_models(lambda: calls.append(1))

    assert calls == [1], "the injected warm-up hook must be invoked exactly once"
    assert "Background-removal model warmed up." in caplog.text


def test_warmup_without_a_hook_is_reported_not_silent(worker, caplog) -> None:
    """No hook -> the omission is logged and the worker still starts."""
    with caplog.at_level(logging.INFO, logger="ml_worker"):
        assert worker._warmup_models() is None

    assert "No model warmup hook supplied" in caplog.text


def test_warmup_failure_stays_non_fatal(worker, caplog) -> None:
    """Error path: a raising hook degrades to a warning, never propagates."""
    def boom() -> None:
        raise RuntimeError("rembg weights unavailable")

    with caplog.at_level(logging.WARNING, logger="ml_worker"):
        assert worker._warmup_models(boom) is None

    assert "Model warmup skipped (expected on first load, will be ready on first job)" in caplog.text


def test_main_warms_up_before_polling_and_exits_on_idle(worker, monkeypatch) -> None:
    """``main`` forwards its hook to the warm-up, then shuts down when idle."""
    calls: list[int] = []

    class _EmptyRedis:
        def keys(self, _pattern: str):
            return []

        def get(self, _key: str):
            return None

    jobs = types.ModuleType("infrastructure.utils.background_jobs")
    jobs.get_job = lambda job_id: None
    jobs._update_job = lambda job_id, **kwargs: None

    redis_mod = types.ModuleType("infrastructure.utils.redis_client")
    redis_mod.redis_client = _EmptyRedis

    monkeypatch.setitem(sys.modules, "infrastructure.utils.background_jobs", jobs)
    monkeypatch.setitem(sys.modules, "infrastructure.utils.redis_client", redis_mod)
    monkeypatch.setattr(worker, "POLL_INTERVAL", 1)
    monkeypatch.setattr(worker, "IDLE_SHUTDOWN", 1)

    assert worker.main(warmup=lambda: calls.append(1)) is None
    assert calls == [1], "main() must warm up with the injected hook before polling"