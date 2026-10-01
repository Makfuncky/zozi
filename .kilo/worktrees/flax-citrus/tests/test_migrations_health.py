"""Regression tests for the database migrations module (DBA13 / DBA27).

Verifies the Alembic chain is healthy:
- no syntax/broken migration files (DBA27: BOM / parse errors)
- exactly ONE Alembic head (DBA13: no multiple heads)
- no migration references a non-existent down_revision
- backend/migration_helpers.py exists and exports the idempotent safe_* helpers
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKEND = REPO / "backend"
VERSIONS = BACKEND / "alembic" / "versions"
MIGRATION_HELPERS = BACKEND / "migration_helpers.py"


def _revisions():
    revs: dict[str, Path] = {}
    downs: dict[str, object] = {}
    for f in sorted(VERSIONS.glob("*.py")):
        if f.name == "__init__.py":
            continue
        text = f.read_text(encoding="utf-8")
        ast.parse(text)  # raises on BOM / syntax error (DBA27)
        m = re.search(r"^revision\b[^=]*=\s*['\"]([^'\"]+)['\"]", text, re.M)
        d = re.search(r"^down_revision\b[^=]*=\s*(.+)$", text, re.M)
        if not m:
            continue
        rev = m.group(1)
        revs[rev] = f
        if d:
            try:
                downs[rev] = ast.literal_eval(d.group(1).strip())
            except Exception:
                downs[rev] = d.group(1).strip()
    return revs, downs


def test_no_broken_migration_files():
    for f in sorted(VERSIONS.glob("*.py")):
        if f.name == "__init__.py":
            continue
        src = f.read_text(encoding="utf-8")
        assert not src.startswith("\ufeff"), f"BOM present in {f.name} (DBA27)"
        ast.parse(src)  # raises SyntaxError if broken


def test_single_alembic_head():
    revs, downs = _revisions()
    referenced: set = set()
    for targets in downs.values():
        items = targets if isinstance(targets, (tuple, list)) else ([targets] if targets else [])
        for t in items:
            if t:
                referenced.add(t)
    heads = [r for r in revs if r not in referenced]
    assert heads, "migration graph has no head"
    assert len(heads) == 1, f"multiple Alembic heads (DBA13): {heads}"
    for rev, targets in downs.items():
        items = targets if isinstance(targets, (tuple, list)) else ([targets] if targets else [])
        for t in items:
            assert t in revs or t is None, (
                f"{revs[rev].name} references missing revision {t}"
            )


def test_migration_helpers_present():
    assert MIGRATION_HELPERS.exists(), "backend/migration_helpers.py missing (DBA27 dependency)"
    tree = ast.parse(MIGRATION_HELPERS.read_text(encoding="utf-8"))
    defined = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    for helper in ("safe_add_column", "safe_drop_column", "safe_create_index", "safe_drop_index"):
        assert helper in defined, f"migration_helpers missing {helper}"


def _orm_tables():
    names: set[str] = set()
    for f in sorted((BACKEND / "models").glob("*.py")):
        if f.name == "__init__.py":
            continue
        for m in re.finditer(r"__tablename__\s*=\s*['\"]([^'\"]+)['\"]", f.read_text(encoding="utf-8")):
            names.add(m.group(1))
    return names


def _migration_create_tables():
    names: set[str] = set()
    for f in sorted(VERSIONS.glob("*.py")):
        if f.name == "__init__.py":
            continue
        for m in re.finditer(r"op\.create_table\(\s*['\"]([^'\"]+)['\"]", f.read_text(encoding="utf-8")):
            names.add(m.group(1))
    return names


def test_orm_tables_have_migrations():
    orm = _orm_tables()
    created = _migration_create_tables()
    missing = sorted(orm - created)
    assert not missing, f"ORM tables with no migration create_table (DBA13): {missing}"
