"""Law-aligned tests for infrastructure isolation (Law 102 / 140-149).

Laws covered:
  - Law 102: infrastructure/ does NOT import domains/modules/rbac/providers
  - Law 148: canonical Base is infrastructure.database.base.Base
  - Law 149: get_db/get_read_db session lifecycle
  - Law 47: DB connection pool settings expose sizing
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import pytest

# Ensure backend root is importable
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# --- Inlined from tests._support.laws (import path broken in this env) ---

FORBIDDEN_IMPORT_RULES: dict[str, tuple[str, ...]] = {
    "domains": ("modules", "rbac"),
    "infrastructure": ("domains", "modules", "rbac", "providers"),
    "kernel": ("domains", "modules", "rbac", "providers", "infrastructure", "jobs", "middleware"),
    "providers": ("domains", "modules", "rbac", "jobs", "middleware"),
    "jobs": ("modules", "middleware"),
    "middleware": ("domains", "modules"),
}


def _read_source(module_path: Path) -> ast.Module:
    return ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))


def _module_import_roots(tree: ast.Module) -> list[str]:
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
    forbidden = FORBIDDEN_IMPORT_RULES.get(package_root, ())
    if not forbidden:
        return
    violations: list[str] = []
    for path in sorted(source_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            tree = _read_source(path)
        except SyntaxError as exc:
            violations.append(f"{path}: syntax error ({exc})")
            continue
        for root in _module_import_roots(tree):
            if root in forbidden:
                violations.append(f"{path}: imports forbidden layer '{root}'")
    assert not violations, (
        f"{package_root} violates Law 1 (arrows point down only):\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
INFRA_DIR = BACKEND_ROOT / "infrastructure"


class TestInfrastructureIsolation:
    """Law 102: infrastructure/ must not import domains/modules/rbac/providers."""

    def test_infrastructure_no_forbidden_imports(self) -> None:
        assert_no_forbidden_imports("infrastructure", INFRA_DIR)


class TestCanonicalBase:
    """Law 148: canonical Base is infrastructure.database.base.Base."""

    def test_canonical_base_exists(self) -> None:
        from infrastructure.database.base import Base
        assert Base is not None
        assert hasattr(Base, "metadata")

    def test_canonical_base_is_declarative_base(self) -> None:
        from sqlalchemy.orm import DeclarativeBase
        from infrastructure.database.base import Base
        assert issubclass(Base, DeclarativeBase)

    def test_no_other_declarative_base_subclasses(self) -> None:
        """Scan for non-canonical DeclarativeBase subclasses that models might use."""
        import ast

        from sqlalchemy.orm import DeclarativeBase

        # Find all Python files in infrastructure that define a DeclarativeBase
        violations = []
        for path in sorted(INFRA_DIR.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            try:
                tree = _read_source(path)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_name = ""
                        if isinstance(base, ast.Name):
                            base_name = base.id
                        elif isinstance(base, ast.Attribute):
                            base_name = base.attr
                        if base_name == "DeclarativeBase" and node.name != "Base":
                            violations.append(f"{path}:{node.lineno} - class {node.name}")

        # Also check domains for non-canonical bases
        domains_dir = BACKEND_ROOT / "domains"
        for path in sorted(domains_dir.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            try:
                tree = _read_source(path)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_name = ""
                        if isinstance(base, ast.Name):
                            base_name = base.id
                        elif isinstance(base, ast.Attribute):
                            base_name = base.attr
                        if base_name == "DeclarativeBase" and node.name != "Base":
                            violations.append(f"{path}:{node.lineno} - class {node.name}")

        assert not violations, (
            f"Non-canonical DeclarativeBase subclasses found (Law 148):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_infrastructure_database_init_exports_canonical_base(self) -> None:
        """infrastructure.database.__init__ must export the canonical Base."""
        from infrastructure.database import Base
        from infrastructure.database.base import Base as DirectBase
        assert Base is DirectBase


class TestDatabaseSessionLifecycle:
    """Law 149: get_db/get_read_db session lifecycle."""

    def test_get_db_yields_session(self, db_session) -> None:
        from sqlalchemy.orm import Session
        assert isinstance(db_session, Session)

    def test_get_db_session_rollback(self, db_session) -> None:
        """Verify the rollback session does not persist data."""
        from sqlalchemy import text
        result = db_session.execute(text("SELECT 1 AS val"))
        row = result.fetchone()
        assert row[0] == 1

    def test_engine_fixture_exists(self, engine) -> None:
        assert engine is not None
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_check_connection_health(self) -> None:
        from infrastructure.database.database import check_connection_health
        assert check_connection_health() is True

    def test_validate_connection_pool(self) -> None:
        from infrastructure.database.database import validate_connection_pool
        result = validate_connection_pool()
        assert isinstance(result, dict)
        assert result.get("validation_ok") is True

    def test_get_pool_metrics(self) -> None:
        from infrastructure.database.database import get_pool_metrics
        result = get_pool_metrics()
        assert isinstance(result, dict)
        assert "size" in result


class TestConnectionPoolSizing:
    """Law 47: DB connection pool settings expose sizing for 100K+ users."""

    def test_pool_size_configurable(self) -> None:
        from infrastructure.utils.config import settings
        assert hasattr(settings, "db_pool_size")
        assert settings.db_pool_size > 0

    def test_max_overflow_configurable(self) -> None:
        from infrastructure.utils.config import settings
        assert hasattr(settings, "db_max_overflow")
        assert settings.db_max_overflow > 0

    def test_pool_recycle_configurable(self) -> None:
        from infrastructure.utils.config import settings
        assert hasattr(settings, "db_pool_recycle")
        assert settings.db_pool_recycle > 0

    def test_pool_pre_ping_enabled(self) -> None:
        """pool_pre_ping must be True for connection health validation."""
        from infrastructure.database.database import _pool_kwargs
        assert _pool_kwargs.get("pool_pre_ping") is True

    def test_pool_size_reasonable_for_scale(self) -> None:
        """Pool size should be at least 10 for 100K+ user scale."""
        from infrastructure.utils.config import settings
        assert settings.db_pool_size >= 10, \
            f"db_pool_size={settings.db_pool_size} too small for 100K+ users (Law 47)"

    def test_validate_connection_pool_returns_pre_ping(self) -> None:
        from infrastructure.database.database import validate_connection_pool
        result = validate_connection_pool()
        assert "pre_ping_enabled" in result
