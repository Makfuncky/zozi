"""Canonical shared helpers for the Zozi backend test-suite.

This package is imported by the law-aligned test modules under ``tests/``. It is
deliberately NOT named ``test_*`` so pytest never collects it as a test module.

It centralises the assertions that map directly onto the architecture benchmark
(``ARCHITECTURE_DIAGRAM.md``, Laws 1-325) so every domain / module / provider test
can reuse identical, auditable checks instead of re-implementing them.

Design rules for this file:
* No top-level import of domain *models* (those are heavy and registered lazily).
* Only fast, safe imports at module load (rbac.catalog scans feature files only).
* Every helper is pure and side-effect free unless documented otherwise.
"""
from __future__ import annotations

import ast
import importlib
import logging
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical axis constants (Law 12 / 13 / 160 / 138)
# ---------------------------------------------------------------------------
# The 16 operational domains present on disk. (Law 12 text says "15"; the
# authoritative AGENTS.md + on-disk layout is 16 with `hr` added.)
ALL_DOMAINS: tuple[str, ...] = (
    "accounts",
    "analytics",
    "audit",
    "catalog",
    "comms",
    "country",
    "customers",
    "finance",
    "governance",
    "hr",
    "logistics",
    "orders",
    "promotions",
    "security",
    "suppliers",
)

ALL_MODULES: tuple[str, ...] = (
    "admin",
    "customer",
    "employee",
    "logistics",
    "supplier",
)

# Schemas that are FORBIDDEN as Postgres schema names (Law 24 / 56).
FORBIDDEN_SCHEMAS: frozenset[str] = frozenset({"core", "platform", "identity"})

# Modules that must never be imported by the layers below them (Law 1 / 97-106).
# key = the importing layer's package root; value = forbidden import roots.
FORBIDDEN_IMPORT_RULES: dict[str, tuple[str, ...]] = {
    "domains": ("modules", "rbac"),
    "infrastructure": ("domains", "modules", "rbac", "providers"),
    "kernel": ("domains", "modules", "rbac", "providers", "infrastructure", "jobs", "middleware"),
    "providers": ("domains", "modules", "rbac", "jobs", "middleware"),
    "jobs": ("modules", "middleware"),
    "middleware": ("domains", "modules"),
}

BACKEND_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# RBAC feature catalog (Law 4 / 161)
# ---------------------------------------------------------------------------
def load_feature_catalog() -> dict:
    """Return the aggregated feature catalog from ``rbac/catalog.py``."""
    from rbac.catalog import FEATURE_CATALOG

    return dict(FEATURE_CATALOG)


def all_feature_keys() -> set[str]:
    return set(load_feature_catalog().keys())


def assert_feature_in_catalog(feature: str) -> None:
    """Assert a single feature atom exists in the aggregated catalog (Law 4)."""
    assert feature in all_feature_keys(), (
        f"Feature '{feature}' is not registered in rbac/catalog.py. "
        "Every require_feature(...) literal must resolve to a single-sourced atom."
    )


# ---------------------------------------------------------------------------
# Source-level import checks (Law 1 / 97-102)
# ---------------------------------------------------------------------------
def read_source(module_path: Path) -> ast.Module:
    return ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))


def module_import_roots(tree: ast.Module) -> list[str]:
    """Return the top-level import roots (e.g. 'domains', 'rbac') used by a module."""
    roots: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                roots.append(node.module.split(".")[0])
    return roots


def assert_no_forbidden_imports(package_root: str, source_dir: Path) -> None:
    """Walk ``source_dir`` and assert ``package_root`` never imports forbidden layers.

    ``package_root`` is one of: domains, infrastructure, kernel, providers, jobs,
    middleware. Forbidden targets come from FORBIDDEN_IMPORT_RULES (Law 1/97-106).
    """
    forbidden = FORBIDDEN_IMPORT_RULES.get(package_root, ())
    if not forbidden:
        return
    violations: list[str] = []
    for path in sorted(source_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            tree = read_source(path)
        except SyntaxError as exc:  # pragma: no cover - defensive
            violations.append(f"{path}: syntax error ({exc})")
            continue
        for root in module_import_roots(tree):
            if root in forbidden:
                violations.append(f"{path}: imports forbidden layer '{root}'")
    assert not violations, (
        f"{package_root} violates Law 1 (arrows point down only):\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


# ---------------------------------------------------------------------------
# ORM schema-discipline checks (Law 6 / 23 / 55 / 152)
# ---------------------------------------------------------------------------
REQUIRED_AUDIT_COLUMNS = ("created_at", "updated_at", "country_code", "is_deleted")


def assert_schema_discipline(model: type) -> None:
    """Assert a single ORM model honours schema + audit-column discipline.

    Checks (Law 6 / 23 / 55 / 152):
      * ``__tablename__`` is defined (snake_case, plural recommended).
      * ``__table_args__`` declares a domain Postgres schema that is not forbidden.
      * Audit columns (created_at, updated_at, country_code, is_deleted) exist.
    """
    table = getattr(model, "__table__", None)
    assert table is not None, f"{model!r} has no __table__ (not an ORM model?)"

    assert getattr(model, "__tablename__", None), f"{model!r} missing __tablename__"

    table_args = getattr(model, "__table_args__", None) or ()
    if isinstance(table_args, dict):
        schema = table_args.get("schema")
    else:
        schema = None
        for item in table_args:
            if isinstance(item, dict) and "schema" in item:
                schema = item["schema"]
                break
    assert schema, f"{model.__name__} declares no Postgres schema (Law 6/55)"
    assert schema not in FORBIDDEN_SCHEMAS, (
        f"{model.__name__} uses forbidden schema '{schema}' (Law 24/56)"
    )

    missing = [c for c in REQUIRED_AUDIT_COLUMNS if not hasattr(model, c)]
    assert not missing, (
        f"{model.__name__} missing audit columns {missing} (Law 23/229)"
    )


def assert_foreign_keys_have_ondelete(model: type) -> None:
    """Assert every ForeignKey on a model declares explicit ondelete (Law 22 / 52)."""
    table = getattr(model, "__table__", None)
    assert table is not None
    bad = []
    for column in table.columns:
        for fk in column.foreign_keys:
            if fk.ondelete is None:
                bad.append(f"{table.name}.{column.name} -> {fk.target_fullname}")
    assert not bad, f"ForeignKeys missing ondelete (Law 22/52): {bad}"


# ---------------------------------------------------------------------------
# Provider checks (Law 30 / 31 / 100 / 123-125 / 129)
# ---------------------------------------------------------------------------
def assert_provider_has_flags(provider_module: type | object) -> None:
    """Assert a provider module exposes HAS_<SDK> availability flags (Law 124)."""
    flags = [n for n in dir(provider_module) if n.startswith("HAS_")]
    assert flags, (
        f"Provider {getattr(provider_module, '__name__', provider_module)} exposes "
        "no HAS_<SDK> flags (Law 124: graceful degradation)."
    )


def discover_packages(root: str) -> list[str]:
    """Return importable sub-package names directly under ``backend/<root>``."""
    base = BACKEND_ROOT / root
    if not base.exists():
        return []
    return sorted(
        p.name
        for p in base.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "__init__.py").exists()
    )


def import_module(dotted: str):
    return importlib.import_module(dotted)


def iter_domain_models(domain: str) -> Iterable[type]:
    """Import a domain's models package and yield every Base subclass found."""
    from infrastructure.database.base import Base

    try:
        importlib.import_module(f"domains.{domain}.models")
    except Exception:
        logger.warning("Failed to import domain models: %s", domain, exc_info=True)
        pass
    seen = set()
    for model in Base.__subclasses__():
        mod = model.__module__
        if mod.startswith(f"domains.{domain}.") and model not in seen:
            seen.add(model)
            yield model
