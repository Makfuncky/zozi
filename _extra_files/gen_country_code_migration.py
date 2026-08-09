"""Rebuild the DBA04 migration targets by parsing model source (AST).

The earlier run used ORM introspection but hit a Base-registry mismatch, so
this parses every model file directly to collect (schema, table, nullable) for
each ``country_code`` column. The emitted migration narrows every
``country_code`` to String(3) on PostgreSQL (idempotent; SQLite ignores width).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
MODELS = BACKEND / "models"
VERSIONS = BACKEND / "alembic" / "versions"

REVISION = "ccw_unify_20260809"
DOWN = "02ebc285f66f"


def _literal_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _schema_from_table_args(node: ast.AST) -> str | None:
    """Find {'schema': 'X'} inside a __table_args__ tuple/dict."""
    if isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            if _literal_str(k) == "schema":
                return _literal_str(v)
    if isinstance(node, (ast.Tuple, ast.List)):
        for elt in node.elts:
            s = _schema_from_table_args(elt)
            if s:
                return s
    return None


def _column_nullable(call: ast.Call) -> bool:
    for kw in call.keywords:
        if kw.arg == "nullable":
            if isinstance(kw.value, ast.Constant):
                return bool(kw.value.value)
    return True  # SQLAlchemy default


def _string_width(call: ast.Call) -> int | None:
    """First positional arg is String(N); return N if present."""
    if call.args:
        first = call.args[0]
        if isinstance(first, ast.Call) and getattr(first.func, "id", None) == "String":
            if first.args and isinstance(first.args[0], ast.Constant):
                return int(first.args[0].value)
    return None


targets: list[tuple[str | None, str, bool]] = []

for path in sorted(MODELS.rglob("*.py")):
    if path.name == "__init__.py":
        continue
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        tablename = None
        schema = None
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for tgt in stmt.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "__tablename__":
                        tablename = _literal_str(stmt.value)
                    if isinstance(tgt, ast.Name) and tgt.id == "__table_args__":
                        schema = _schema_from_table_args(stmt.value)
                # country_code = Column(String(N), ...)
                if (
                    isinstance(tgt := stmt.targets[0], ast.Name)
                    and tgt.id == "country_code"
                    and isinstance(stmt.value, ast.Call)
                    and getattr(stmt.value.func, "id", None) == "Column"
                ):
                    width = _string_width(stmt.value)
                    if width is not None:
                        targets.append((schema, tablename, _column_nullable(stmt.value)))
        # if schema was defined after columns, re-scan whole class body for it
        if schema is None:
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Assign):
                    for tgt in stmt.targets:
                        if isinstance(tgt, ast.Name) and tgt.id == "__table_args__":
                            schema = _schema_from_table_args(stmt.value)
            # re-collect with found schema
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and isinstance(stmt.targets[0], ast.Name)
                    and stmt.targets[0].id == "country_code"
                    and isinstance(stmt.value, ast.Call)
                    and getattr(stmt.value.func, "id", None) == "Column"
                ):
                    width = _string_width(stmt.value)
                    if width is not None:
                        targets[-1] = (schema, tablename, _column_nullable(stmt.value))

# dedupe (schema, table)
seen = set()
deduped = []
for schema, table, nullable in targets:
    key = (schema, table)
    if key in seen or table is None:
        continue
    seen.add(key)
    deduped.append((schema, table, nullable))

deduped.sort(key=lambda t: (str(t[0]), t[1]))
print(f"[ast] found {len(deduped)} country_code columns")

targets_literal = ",\n".join(
    f"    ({s!r}, {t!r}, {n})" for s, t, n in deduped
)

migration = f'''"""unify country_code width to String(3) (DBA04)

All ``country_code`` columns are normalised to ``String(3)`` to match the
referenced ``country.country_configs.code`` (ISO alpha-3, max 3 chars). This
removes the width drift flagged by DBA04. SQLite ignores VARCHAR length, so the
ORM rebuild already handles it; this migration applies the narrowing on
PostgreSQL only (idempotent: re-ALTERing an already-String(3) column is a no-op).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = {REVISION!r}
down_revision: Union[str, None] = {DOWN!r}
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (schema, table, existing_nullable) for every country_code column
_TARGETS = (
{targets_literal}
)


def _apply(new_len: int, existing_len: int) -> None:
    if op.get_context().dialect.name != "postgresql":
        return
    for schema, table, nullable in _TARGETS:
        op.alter_column(
            table,
            "country_code",
            type_=sa.String(new_len),
            existing_type=sa.String(existing_len),
            existing_nullable=nullable,
            schema=schema,
        )


def upgrade() -> None:
    _apply(3, 10)


def downgrade() -> None:
    _apply(10, 3)
'''

out = VERSIONS / f"2026_08_09_0000-{REVISION}_unify_country_code_width.py"
out.write_text(migration, encoding="utf-8")
print(f"[migration] wrote {out.relative_to(BACKEND)}")
