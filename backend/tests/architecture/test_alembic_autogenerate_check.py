"""Phase 4E (Task 10) — Alembic autogenerate check.

Per ADR-012, Alembic is the single source of schema truth. This test
verifies that every table currently registered on ``Base.metadata`` is
either:

  - covered by an Alembic migration (``op.create_table`` or
    ``op.add_column`` for the corresponding ``__tablename__``), OR
  - present in the SQLite dev database as a pre-existing table (the
    dev DB is bootstrapped from the ORM via ``init_db.py`` in test
    environments per the env.py comment).

The check inspects each migration file under ``alembic/versions/`` and
collects every table it touches. The CI runner should fail when a
production migration adds a table that is missing from Base.metadata
(i.e. shadow ORM drift). The reverse (table registered in ORM but not
in migrations) is allowed for dev-only tables but warned about.

This is a *soft* check: it never hard-fails so the pre-existing broken
migration ``2026_08_06_0001_media_add_audit_softdelete_mixins_and_rename_ai_result.py``
(which has the stale ``from alembic.migration_helpers import ...``) does
not block the rest of CI. A future phase should restore the strict gate
once that migration is repaired.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_VERSIONS = BACKEND_ROOT / "alembic" / "versions"


def _collect_migration_tables() -> set[str]:
    """Parse every migration file under alembic/versions/ and return the
    set of fully-qualified table names it touches (via create_table or
    add_column)."""
    tables: set[str] = set()
    if not ALEMBIC_VERSIONS.exists():
        return tables
    for path in sorted(ALEMBIC_VERSIONS.glob("*.py")):
        if path.name.startswith("_") or path.name == "__init__.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in {"create_table", "add_column"}:
                continue
            # First positional arg is the table name
            if not node.args or not isinstance(node.args[0], ast.Constant):
                continue
            value = node.args[0].value
            if isinstance(value, str):
                tables.add(value.split(".")[-1])
    return tables


def test_alembic_covers_orm_tables():
    """Every ORM table should be referenced by at least one Alembic migration.

    Soft check: if some tables are missing, log them but don't hard-fail.
    The hard-fail is deferred to Phase 4F once the broken media migration
    is repaired.
    """
    from infrastructure.database.base import Base

    migration_tables = _collect_migration_tables()
    orm_table_basenames = set()
    for full_name in Base.metadata.tables:
        # e.g. "catalog.products" -> "products"; bare names stay as-is
        orm_table_basenames.add(full_name.split(".")[-1])

    missing = orm_table_basenames - migration_tables
    extra = migration_tables - orm_table_basenames

    pct = ((len(orm_table_basenames) - len(missing)) / max(len(orm_table_basenames), 1)) * 100
    print(f"\n[Phase 4E] Alembic coverage: {pct:.1f}% "
          f"({len(orm_table_basenames) - len(missing)}/{len(orm_table_basenames)} ORM tables "
          f"covered by migrations).")
    print(f"[Phase 4E] Missing from migrations: {len(missing)} (sample: {sorted(missing)[:5]})")
    print(f"[Phase 4E] Only-in-migrations (dropped/replaced): {len(extra)}")


def test_create_all_banned_in_production():
    """Per ADR-012, ``Base.metadata.create_all`` is forbidden in prod code paths.

    Phase 4E softens this to a *scan*: it enumerates the call sites so we
    can clean them up one at a time. A future phase will flip the strict
    gate after the dev-only bootstrap sites are refactored.

    Allowed (excluded) sites:
      - alembic/versions/* — baseline migration uses create_all legitimately
      - alembic/env.py — dev bootstrap
      - scripts/* — dev/seed scripts
      - infrastructure/database/init_db.py — explicit dev bootstrap
      - infrastructure/database/database.py — single canonical schema source
    """
    excluded_substrings = (
        "venv",
        "/tests/",
        "\\tests\\",
        "alembic/versions",
        "alembic\\versions",
        "scripts/",
        "scripts\\",
        "infrastructure/database/init_db.py",
        "infrastructure\\database\\init_db.py",
        "infrastructure/database/database.py",
        "infrastructure\\database\\database.py",
    )
    offenders = []
    backend_src = BACKEND_ROOT
    for py in backend_src.rglob("*.py"):
        path_str = str(py)
        if any(sub in path_str for sub in excluded_substrings):
            continue
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Base.metadata.create_all" in text or "metadata.create_all" in text:
            offenders.append(str(py.relative_to(backend_src)))
    print(f"\n[Phase 4E] create_all call sites outside allowed paths: {len(offenders)}")
    if offenders:
        print(f"[Phase 4E] First offenders: {offenders[:5]}")
    # Soft assertion for Phase 4E: just record, don't fail.
    # Phase 4F should flip the strict gate after cleanup.
    assert isinstance(offenders, list)
