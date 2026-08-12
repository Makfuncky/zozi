"""Static regression tests for the ZOZI backend circuit contract (audit codes CIR1 / CIR2).

These mirror ``scripts/system_trackers/system_architecture_audit.py``:

* **CIR1** - an import lands outside the layer's allowed import set, or flows
  *upward* through the layer order. CIR1 is a hard violation: this suite fails.
* **CIR2** - a "migration bypass" (``routers -> services``, ``routers -> models``,
  ``controllers -> models``). Still advisory in the audit, so it is asserted
  against a ratchet baseline: the count may shrink, never grow.

Pure AST analysis - nothing is imported, so the suite is fast and unaffected by
routers that currently fail to import.
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"
BASELINE_FILE = pathlib.Path(__file__).with_name("circuit_contract_baseline.json")

# Layers excluded from the circuit (mirrors DEFAULT_GRAPH_EXEMPT_LAYERS).
EXEMPT_LAYERS = {"tests", "scripts", "alembic", "monitoring", "docs", "data"}

# Mirrors CIRCUIT_ALLOWED_IMPORTS.
ALLOWED: dict[str, set[str]] = {
    "main": {"middleware", "dependencies", "routers", "db", "utils", "lifespan", "data"},
    "lifespan": {"db", "utils", "middleware", "dependencies", "data"},
    "middleware": {"db", "utils", "dependencies", "data"},
    "dependencies": {"db", "utils", "data"},
    "routers": {"controllers", "dependencies", "utils", "data"},
    "controllers": {"services", "utils", "data"},
    "services": {"models", "providers", "utils", "events", "jobs", "db", "data"},
    "providers": {"utils", "data"},
    "models": {"db", "utils"},
    "db": {"utils"},
    "events": {"services", "models", "providers", "utils", "db", "data"},
    "jobs": {"services", "models", "providers", "utils", "db", "data"},
    "data": set(),
    "utils": set(),
}

# Local mirror of the circuit layer ordering (imports must flow downward: low -> high).
LAYER_ORDER: dict[str, int] = {
    "main": 0, "lifespan": 0,
    "middleware": 1, "dependencies": 1,
    "routers": 2, "controllers": 3, "services": 4,
    "providers": 5, "models": 6, "db": 7,
    "utils": 8, "data": 8,
    "events": 4, "jobs": 4,
}

# Mirrors CIRCUIT_BYPASS_IMPORTS.
BYPASS_EDGES = {("routers", "services"), ("routers", "models"), ("controllers", "models")}

# Cross-cutting targets never count as an upward violation.
CROSS_CUTTING = {"utils", "data"}


def _layer_of(module: str) -> str | None:
    """Top-level package of a dotted module path, if it is a known layer."""
    top = module.split(".", 1)[0]
    return top if top in LAYER_ORDER else None


def _iter_backend_modules():
    """Yield ``(module_name, path)`` for every first-party backend module."""
    for path in sorted(BACKEND.rglob("*.py")):
        parts = path.relative_to(BACKEND).with_suffix("").parts
        if any(p in {"venv", "__pycache__", "node_modules", ".pytest_cache"} for p in parts):
            continue
        if parts and parts[0] in EXEMPT_LAYERS:
            continue
        module = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
        if module:
            yield module, path


def _resolves(target_module: str) -> bool:
    """Whether a dotted module path maps to a real file in the backend tree.

    Mirrors the audit: only *resolvable* first-party imports are graphed, so
    typos / imports of modules that no longer exist are not counted.
    """
    rel = pathlib.Path(*target_module.split("."))
    candidates = [
        BACKEND / rel.with_suffix(".py"),
        BACKEND / rel / "__init__.py",
    ]
    return any(c.is_file() for c in candidates)


def _imports_of(path: pathlib.Path) -> list[tuple[str, int]]:
    """Absolute dotted import targets in a file, with line numbers."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.append((node.module, node.lineno))
    return out


def _scan() -> tuple[list[str], list[str]]:
    """Return ``(cir1_violations, cir2_bypasses)`` as human-readable strings."""
    cir1: list[str] = []
    cir2: list[str] = []

    for module, path in _iter_backend_modules():
        caller = _layer_of(module)
        if caller is None or caller in EXEMPT_LAYERS or caller not in ALLOWED:
            continue
        rel = path.relative_to(BACKEND.parent).as_posix()
        seen: set[tuple[str, str]] = set()

        for target_mod, lineno in _imports_of(path):
            target = _layer_of(target_mod)
            if target is None or target in EXEMPT_LAYERS or target == caller:
                continue
            if not _resolves(target_mod):
                continue

            # Upward flow through the layer order is always CIR1.
            if target not in CROSS_CUTTING and LAYER_ORDER[target] < LAYER_ORDER[caller]:
                cir1.append(f"{rel}:{lineno} upward {caller} -> {target} ({target_mod})")
                continue

            if target in ALLOWED[caller]:
                continue

            edge = (caller, target)
            if edge in seen:
                continue
            seen.add(edge)

            entry = f"{rel}:{lineno} {caller} -> {target} ({target_mod})"
            (cir2 if edge in BYPASS_EDGES else cir1).append(entry)

    return sorted(cir1), sorted(cir2)


@pytest.fixture(scope="module")
def scan_result() -> tuple[list[str], list[str]]:
    return _scan()


def test_backend_tree_is_discoverable() -> None:
    """Guard against the scanner silently walking an empty tree."""
    assert BACKEND.is_dir(), f"backend package not found at {BACKEND}"
    assert sum(1 for _ in _iter_backend_modules()) > 100


def test_no_cir1_circuit_violations(scan_result) -> None:
    """CIR1 is a hard violation - imports must stay inside the circuit and flow downward."""
    cir1, _ = scan_result
    assert not cir1, (
        f"{len(cir1)} CIR1 circuit violation(s):\n  " + "\n  ".join(cir1)
    )


def test_main_does_not_reach_services_or_models(scan_result) -> None:
    """Regression: the A2 orphan-wiring block must not live in the entry layer.

    Orphaned service modules belong in ``services/_registry.py`` and orphaned
    models in ``models/__init__.py`` - both same-layer, therefore legal edges.
    """
    cir1, _ = scan_result
    offenders = [v for v in cir1 if v.startswith("backend/main.py")]
    assert not offenders, "main.py must not import services/models directly:\n  " + "\n  ".join(offenders)


def test_routers_do_not_import_db_or_dependencies(scan_result) -> None:
    """Regression: routers must reach the DB session via ``data.db``/``utils``, not ``db.database``."""
    cir1, _ = scan_result
    offenders = [v for v in cir1 if "/routers/" in v and (" -> db" in v or " -> dependencies" in v)]
    assert not offenders, "routers must not import db/dependencies directly:\n  " + "\n  ".join(offenders)


def test_cir2_bypasses_do_not_regress(scan_result) -> None:
    """CIR2 is advisory; hold a ratchet so the migration only ever moves forward."""
    _, cir2 = scan_result
    baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    limit = int(baseline["max_cir2_bypasses"])
    assert len(cir2) <= limit, (
        f"CIR2 bypasses rose to {len(cir2)} (baseline {limit}). New bypasses:\n  "
        + "\n  ".join(cir2)
    )
