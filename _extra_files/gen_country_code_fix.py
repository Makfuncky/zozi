"""One-off generator for DBA04 country_code width unification.

1. Rewrites every model `country_code = Column(String(10) ...)` -> `String(3)`
   to match the referenced `country.country_configs.code` (ISO alpha-3, max 3).
2. Introspects the ORM and emits a single Alembic migration that ALTERs the
   existing (already-String(10)) columns to String(3) on PostgreSQL.

This script is a maintenance tool, not part of the runtime. It lives in
_extra_files and is never imported by the app.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
MODELS = BACKEND / "models"
VERSIONS = BACKEND / "alembic" / "versions"

# Only target the country_code column; never phone_code/postal_code/employee_code etc.
PATTERN = re.compile(r"(country_code = Column\()String\(10\)")

# --- Step 1: rewrite model files ------------------------------------------------
edited_files = 0
edited_cols = 0
for path in sorted(MODELS.rglob("*.py")):
    if path.name == "__init__.py":
        continue
    text = path.read_text(encoding="utf-8")
    new_text, n = PATTERN.subn(r"\1String(3)", text)
    if n:
        path.write_text(new_text, encoding="utf-8")
        edited_files += 1
        edited_cols += n
        print(f"[model] {path.relative_to(BACKEND)} : {n} country_code -> String(3)")
print(f"[model] edited {edited_cols} columns across {edited_files} files")

# --- Step 2: introspect ORM to build migration targets -------------------------
sys.path.insert(0, str(BACKEND))
import models  # noqa: E402  (populates Base.metadata)
from db.base import Base  # noqa: E402
from sqlalchemy import String  # noqa: E402

targets = []
for table in Base.metadata.tables.values():
    col = table.columns.get("country_code")
    if col is None:
        continue
    if isinstance(col.type, String) and col.type.length == 10:
        targets.append((table.schema, table.name, bool(col.nullable)))

targets.sort(key=lambda t: (str(t[0]), t[1]))
print(f"[orm] found {len(targets)} String(10) country_code columns to migrate")

# --- Step 3: emit the migration ------------------------------------------------
REVISION = "ccw_unify_20260809"
DOWN = "02ebc285f66f"
targets_literal = ",\n".join(
    f"    ({s!r}, {t!r}, {n})" for s, t, n in targets
)

migration = f'''"""unify country_code width to String(3) (DBA04)

All ``country_code`` columns are normalised to ``String(3)`` to match the
referenced ``country.country_configs.code`` (ISO alpha-3, max 3 chars). This
removes the width drift flagged by DBA04. SQLite ignores VARCHAR length, so the
ORM rebuild already handles it; this migration applies the narrowing on
PostgreSQL only.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = {REVISION!r}
down_revision: Union[str, None] = {DOWN!r}
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (schema, table, existing_nullable) for every String(10) country_code column
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
