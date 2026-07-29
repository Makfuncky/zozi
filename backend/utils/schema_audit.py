#!/usr/bin/env python
"""
Schema Audit — Compare ORM ``Base.metadata`` against the live database.

Usage::

    # Full audit — every table, every column, every index
    python -m utils.schema_audit

    # Summary only (no per-column detail)
    python -m utils.schema_audit --summary

    # JSON output (for pipelines / dashboards)
    python -m utils.schema_audit --json

    # Filter by table name pattern (SQL ``LIKE`` syntax)
    python -m utils.schema_audit --table "orders%"

    # Fix mode — generate SQL to sync DB to ORM (dry-run by default)
    python -m utils.schema_audit --fix

    # Actually execute fix SQL against the database
    python -m utils.schema_audit --fix --apply

    # Importable — call from your own code:
    #
    #   from utils.schema_audit import audit_schema
    #   report = audit_schema()
    #   for issue in report.issues:
    #       print(issue)
    #
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# ── Ensure project root is importable ─────────────────────────────────────
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(_BACKEND_ROOT))

# Windows console needs UTF-8 for check-mark / cross-mark symbols
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class IssueKind(Enum):
    TABLE_MISSING_IN_DB = "table_missing_in_db"
    TABLE_EXTRA_IN_DB = "table_extra_in_db"
    COLUMN_MISSING_IN_DB = "column_missing_in_db"
    COLUMN_EXTRA_IN_DB = "column_extra_in_db"
    COLUMN_TYPE_MISMATCH = "column_type_mismatch"
    COLUMN_NULLABLE_MISMATCH = "column_nullable_mismatch"
    COLUMN_DEFAULT_MISMATCH = "column_default_mismatch"
    INDEX_MISSING_IN_DB = "index_missing_in_db"
    INDEX_EXTRA_IN_DB = "index_extra_in_db"
    INDEX_COLUMNS_MISMATCH = "index_columns_mismatch"
    INDEX_UNIQUE_MISMATCH = "index_unique_mismatch"
    FK_MISSING_IN_DB = "fk_missing_in_db"
    FK_EXTRA_IN_DB = "fk_extra_in_db"
    FK_COLUMNS_MISMATCH = "fk_columns_mismatch"
    DB_CONNECTION_ERROR = "db_connection_error"
    # ── Alembic / migration-tree issues ───────────────────────────────
    ALEMBIC_STAMP_MISSING = "alembic_stamp_missing"
    ALEMBIC_HEAD_MISMATCH = "alembic_head_mismatch"
    ALEMBIC_TREE_NOT_LINEAR = "alembic_tree_not_linear"
    ALEMBIC_MULTIPLE_ROOTS = "alembic_multiple_roots"
    ALEMBIC_MULTIPLE_HEADS = "alembic_multiple_heads"

PRIORITY: dict[IssueKind, int] = {
    IssueKind.TABLE_MISSING_IN_DB: 1,
    IssueKind.TABLE_EXTRA_IN_DB: 1,
    IssueKind.COLUMN_MISSING_IN_DB: 2,
    IssueKind.COLUMN_EXTRA_IN_DB: 2,
    IssueKind.COLUMN_TYPE_MISMATCH: 3,
    IssueKind.COLUMN_NULLABLE_MISMATCH: 3,
    IssueKind.COLUMN_DEFAULT_MISMATCH: 4,
    IssueKind.INDEX_MISSING_IN_DB: 3,
    IssueKind.INDEX_EXTRA_IN_DB: 3,
    IssueKind.INDEX_COLUMNS_MISMATCH: 4,
    IssueKind.INDEX_UNIQUE_MISMATCH: 4,
    IssueKind.FK_MISSING_IN_DB: 3,
    IssueKind.FK_EXTRA_IN_DB: 3,
    IssueKind.FK_COLUMNS_MISMATCH: 4,
    IssueKind.DB_CONNECTION_ERROR: 0,
    # Alembic issues are priority 1 — they block safe migrations
    IssueKind.ALEMBIC_STAMP_MISSING: 1,
    IssueKind.ALEMBIC_HEAD_MISMATCH: 1,
    IssueKind.ALEMBIC_TREE_NOT_LINEAR: 1,
    IssueKind.ALEMBIC_MULTIPLE_ROOTS: 1,
    IssueKind.ALEMBIC_MULTIPLE_HEADS: 1,
}


@dataclass
class Issue:
    kind: IssueKind
    table: str
    column: str | None = None
    db_value: str | None = None
    orm_value: str | None = None
    detail: str | None = None

    def __str__(self) -> str:
        parts = [f"[{self.kind.value}] {self.table}"]
        if self.column:
            parts.append(f".{self.column}")
        if self.detail:
            parts.append(f" — {self.detail}")
        elif self.db_value is not None and self.orm_value is not None:
            parts.append(f"  DB={self.db_value}  ORM={self.orm_value}")
        return "".join(parts)


@dataclass
class AlembicInfo:
    """Result of inspecting the Alembic migration state."""

    stamped_version: str | None = None
    """The version number stored in ``alembic_version`` table, or ``None`` if table is empty."""

    migration_file_count: int = 0
    """Number of migration files in ``alembic/versions/``."""

    total_revisions: int = 0
    """Unique revision IDs found across all migration files."""

    roots: list[str] = field(default_factory=list)
    """Revisions whose ``down_revision`` is ``None`` (should be exactly 1)."""

    heads: list[str] = field(default_factory=list)
    """Revisions not referenced as ``down_revision`` by any other revision (should be 1)."""

    head_version: str | None = None
    """The single head revision if the tree is linear, else ``None``."""

    @property
    def is_stamped(self) -> bool:
        return self.stamped_version is not None

    @property
    def is_linear(self) -> bool:
        return len(self.roots) == 1 and len(self.heads) == 1

    @property
    def head_matches_stamp(self) -> bool | None:
        if not self.is_stamped or self.head_version is None:
            return None
        return self.stamped_version == self.head_version


@dataclass
class AuditReport:
    """Container for the full schema audit result."""

    db_table_count: int = 0
    orm_table_count: int = 0
    issues: list[Issue] = field(default_factory=list)
    per_table: dict[str, list[Issue]] = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    alembic: AlembicInfo | None = None

    @property
    def healthy(self) -> bool:
        """True when there are zero issues."""
        return len(self.issues) == 0

    def group_by_kind(self) -> dict[IssueKind, list[Issue]]:
        groups: dict[IssueKind, list[Issue]] = {}
        for issue in self.issues:
            groups.setdefault(issue.kind, []).append(issue)
        return groups

    def summary_lines(self) -> list[str]:
        groups = self.group_by_kind()
        lines = [
            f"Tables: DB={self.db_table_count}  ORM={self.orm_table_count}",
            f"Issues: {len(self.issues)} total",
        ]
        if self.alembic:
            a = self.alembic
            stamp_str = a.stamped_version or "(empty)"
            head_str = a.head_version or "(multiple or none)"
            match_str = "✓" if a.head_matches_stamp else ("✗" if a.head_matches_stamp is False else "?")
            lines.append(f"  Alembic: stamp={stamp_str}  head={head_str}  {match_str}")
            if not a.is_linear:
                lines.append(f"    Tree: {len(a.roots)} root(s), {len(a.heads)} head(s) — NOT LINEAR")
        for kind in sorted(groups, key=lambda k: PRIORITY.get(k, 99)):
            n = len(groups[kind])
            lines.append(f"  [{kind.value}] {n}")
        return lines

    def fix_sql(self, engine=None) -> list[str]:
        """Generate ALTER TABLE statements to sync DB to ORM (SQLite dialect).

        For production databases (PostgreSQL), use Alembic instead.
        """
        statements: list[str] = []
        for issue in self.issues:
            if issue.kind == IssueKind.COLUMN_MISSING_IN_DB and issue.column and issue.orm_value:
                # orm_value looks like "VARCHAR(100)" or "INTEGER"
                stmt = f"ALTER TABLE {issue.table} ADD COLUMN {issue.column} {issue.orm_value};"
                statements.append(stmt)
            elif issue.kind == IssueKind.INDEX_MISSING_IN_DB and issue.detail:
                statements.append(issue.detail)
        return statements


# ── internal helpers ──────────────────────────────────────────────────────


def _normalise_type_str(raw: str) -> str:
    """Normalise SQLAlchemy / DB-API type strings for comparison.

    ``INTEGER`` → ``INTEGER``
    ``VARCHAR(100)`` → ``VARCHAR(100)``
    ``BOOLEAN`` → ``BOOLEAN``
    ``DATETIME`` → ``DATETIME``
    ``JSON`` → ``JSON``  (SQLite stores JSON as TEXT, but ORM sees JSON)
    """
    return raw.upper().strip()


def _load_models() -> None:
    """Idempotently import the models package so ``Base.metadata`` is populated."""
    if "models" in sys.modules:
        return
    import models  # noqa: F401


def _get_orm_type_str(orm_col: Any) -> str:
    """Return a human-readable type string for an ORM ``Column``.

    Handles common SQLAlchemy types so the output is comparable with DB-API
    ``get_columns`` output.
    """
    from sqlalchemy import types as sa_types

    col_type = orm_col.type
    raw = str(col_type)

    if isinstance(col_type, sa_types.Boolean):
        return "BOOLEAN"
    if isinstance(col_type, sa_types.Integer):
        return "INTEGER"
    if isinstance(col_type, sa_types.BigInteger):
        return "BIGINT"
    if isinstance(col_type, sa_types.SmallInteger):
        return "SMALLINT"
    if isinstance(col_type, sa_types.Float):
        return "FLOAT"
    if isinstance(col_type, sa_types.Numeric):
        return raw  # NUMERIC(precision, scale)
    if isinstance(col_type, sa_types.String):
        return raw  # VARCHAR(length)
    if isinstance(col_type, sa_types.Text):
        return "TEXT"
    if isinstance(col_type, sa_types.DateTime):
        return "DATETIME"
    if isinstance(col_type, sa_types.Date):
        return "DATE"
    if isinstance(col_type, sa_types.Time):
        return "TIME"
    if isinstance(col_type, sa_types.JSON):
        return "JSON"
    if isinstance(col_type, sa_types.LargeBinary):
        return "BLOB"

    return raw


# ══════════════════════════════════════════════════════════════════════════
#  Alembic Audit
# ══════════════════════════════════════════════════════════════════════════

_ALEMBIC_VERSIONS_DIR = os.path.join(
    str(_BACKEND_ROOT),
    "alembic",
    "versions",
)

# Regex for Alembic revision identifiers — handles both styles:
#   revision = 'abc123'
#   revision: str = 'abc123'
#   down_revision: Union[str, None] = 'abc123'
_REV_PATTERN = re.compile(
    r"""(?:revision|down_revision)
    \s*
    (?::\s*(?:Union\[)?[\w,\s]*\]?)?  # optional type annotation
    \s*=\s*
    ['"]([^'"]+)['"]
    """,
    re.VERBOSE,
)


def check_alembic(
    engine: Any = None,
    versions_dir: str | None = None,
) -> AlembicInfo:
    """Inspect the Alembic migration state.

    Reads the ``alembic_version`` table from the database and scans the
    migration files in ``alembic/versions/`` to determine the tree shape
    (roots, heads, linearity) and whether the stamped version matches
    the head revision.

    Returns
    -------
    AlembicInfo
    """
    from sqlalchemy import text

    info = AlembicInfo()

    versions_path = versions_dir or _ALEMBIC_VERSIONS_DIR

    # ── Read DB stamp ─────────────────────────────────────────────────
    if engine is None:
        try:
            from db.database import engine as _engine
            engine = _engine
        except Exception:
            pass

    if engine is not None:
        try:
            with engine.connect() as conn:
                rows = conn.execute(
                    text("SELECT version_num FROM alembic_version")
                ).fetchall()
            if rows:
                info.stamped_version = rows[0][0]
        except Exception:
            pass  # table may not exist yet

    # ── Scan migration files ──────────────────────────────────────────
    if not os.path.isdir(versions_path):
        info.total_revisions = 0
        return info

    revisions: dict[str, str | None] = {}
    for fname in sorted(os.listdir(versions_path)):
        if not fname.endswith(".py") or fname == "__init__.py":
            continue
        fpath = os.path.join(versions_path, fname)
        try:
            with open(fpath) as fh:
                content = fh.read()
        except Exception:
            continue

        rev_id: str | None = None
        down_id: str | None = None

        for match in _REV_PATTERN.finditer(content):
            matched_text = match.group(0)
            value = match.group(1)
            if matched_text.startswith("revision") and rev_id is None:
                rev_id = value
            elif matched_text.startswith("down_revision") and down_id is None:
                down_id = value

        if rev_id is None:
            continue  # not a valid migration file

        revisions[rev_id] = down_id if down_id and down_id != "None" else None

    info.migration_file_count = sum(
        1 for f in os.listdir(versions_path)
        if f.endswith(".py") and f != "__init__.py"
    )
    info.total_revisions = len(revisions)

    if not revisions:
        return info

    # ── Find roots (revisions with down_revision=None) ────────────────
    roots = [rid for rid, down in revisions.items() if down is None]
    info.roots = sorted(roots)

    # ── Find heads (revisions not referenced as down_revision) ────────
    all_down_refs = {d for d in revisions.values() if d is not None}
    heads = [rid for rid in revisions if rid not in all_down_refs]
    info.heads = sorted(heads)

    if len(heads) == 1:
        info.head_version = heads[0]

    return info


# ══════════════════════════════════════════════════════════════════════════
#  Main Audit
# ══════════════════════════════════════════════════════════════════════════


def audit_schema(
    engine: Any = None,
    table_filter: str | None = None,
    check_indexes: bool = True,
    check_fks: bool = True,
    include_alembic: bool = True,
) -> AuditReport:
    """Run a full audit of ORM vs database schema.

    Parameters
    ----------
    engine :
        SQLAlchemy engine.  If ``None``, uses ``db.database.engine``.
    table_filter :
        Optional glob pattern (e.g. ``"orders*"``).
    check_indexes :
        Whether to compare indexes between ORM and DB.
    check_fks :
        Whether to compare foreign keys between ORM and DB.
    include_alembic :
        Whether to inspect the Alembic migration state (stamp, head, tree
        linearity).  Default ``True``.

    Returns
    -------
    AuditReport
    """
    import time
    from sqlalchemy import inspect, text
    from db.base import Base

    t0 = time.time()
    _load_models()

    if engine is None:
        from db.database import engine as _engine
        engine = _engine

    report = AuditReport()

    # ── Alembic check (before schema comparison) ──────────────────────
    if include_alembic:
        alembic_info = check_alembic(engine=engine)
        report.alembic = alembic_info

        # Emit issues for migration-tree problems
        if not alembic_info.is_stamped:
            report.issues.append(Issue(
                kind=IssueKind.ALEMBIC_STAMP_MISSING,
                table="alembic_version",
                detail="No version is stamped in the alembic_version table — migrations may not have been applied",
            ))

        if alembic_info.is_stamped and alembic_info.head_version is not None:
            if not alembic_info.head_matches_stamp:
                report.issues.append(Issue(
                    kind=IssueKind.ALEMBIC_HEAD_MISMATCH,
                    table="alembic_version",
                    db_value=alembic_info.stamped_version,
                    orm_value=alembic_info.head_version,
                    detail=f"Stamped version '{alembic_info.stamped_version}' differs from head revision '{alembic_info.head_version}'",
                ))

        if len(alembic_info.roots) > 1:
            report.issues.append(Issue(
                kind=IssueKind.ALEMBIC_MULTIPLE_ROOTS,
                table="alembic_version",
                detail=f"Migration tree has {len(alembic_info.roots)} roots (should be 1): {', '.join(alembic_info.roots)}",
            ))

        if len(alembic_info.heads) > 1:
            report.issues.append(Issue(
                kind=IssueKind.ALEMBIC_MULTIPLE_HEADS,
                table="alembic_version",
                detail=f"Migration tree has {len(alembic_info.heads)} heads (should be 1): {', '.join(alembic_info.heads)}",
            ))

        if alembic_info.migration_file_count > 0 and not alembic_info.is_linear:
            report.issues.append(Issue(
                kind=IssueKind.ALEMBIC_TREE_NOT_LINEAR,
                table="alembic_version",
                detail=f"Migration tree is not linear ({len(alembic_info.roots)} root(s), {len(alembic_info.heads)} head(s))",
            ))

    try:
        inspector = inspect(engine)
        db_table_names = set(inspector.get_table_names())
    except Exception as exc:
        issue = Issue(
            kind=IssueKind.DB_CONNECTION_ERROR,
            table="",
            detail=str(exc),
        )
        report.issues.append(issue)
        return report

    orm_table_names = set(Base.metadata.tables.keys())

    report.db_table_count = len(db_table_names)
    report.orm_table_count = len(orm_table_names)

    # ── Filter ─────────────────────────────────────────────────────────
    if table_filter:
        matched = set()
        for t in db_table_names:
            if fnmatch.fnmatch(t, table_filter):
                matched.add(t)
        for t in orm_table_names:
            if fnmatch.fnmatch(t, table_filter):
                matched.add(t)
        db_table_names &= matched
        # We keep orm_table_names for intersection but also filter

    # ── Table-level issues ─────────────────────────────────────────────
    for table in sorted(orm_table_names - db_table_names):
        if table_filter and not fnmatch.fnmatch(table, table_filter):
            continue
        issue = Issue(
            kind=IssueKind.TABLE_MISSING_IN_DB,
            table=table,
            detail="ORM has this table but it does not exist in the database",
        )
        report.issues.append(issue)
        report.per_table.setdefault(table, []).append(issue)

    for table in sorted(db_table_names - orm_table_names):
        if table_filter and not fnmatch.fnmatch(table, table_filter):
            continue
        issue = Issue(
            kind=IssueKind.TABLE_EXTRA_IN_DB,
            table=table,
            detail="Database has this table but it is not registered in the ORM",
        )
        report.issues.append(issue)
        report.per_table.setdefault(table, []).append(issue)

    # ── Column-level issues ────────────────────────────────────────────
    common_tables = sorted(db_table_names & orm_table_names)

    for table in common_tables:
        if table_filter and not fnmatch.fnmatch(table, table_filter):
            continue

        try:
            db_cols = {c["name"]: c for c in inspector.get_columns(table)}
        except Exception as exc:
            report.issues.append(
                Issue(kind=IssueKind.DB_CONNECTION_ERROR, table=table, detail=str(exc))
            )
            continue

        orm_table = Base.metadata.tables[table]
        orm_cols = dict(orm_table.columns)

        all_cols = set(list(db_cols.keys()) + list(orm_cols.keys()))

        for col_name in sorted(all_cols):
            db_c = db_cols.get(col_name)
            orm_c = orm_cols.get(col_name)

            if db_c is None:
                # Column in ORM only
                orm_type = _get_orm_type_str(orm_c) if orm_c else "?"
                report.issues.append(
                    Issue(
                        kind=IssueKind.COLUMN_MISSING_IN_DB,
                        table=table,
                        column=col_name,
                        orm_value=orm_type,
                        detail=f"Column '{col_name}' exists in ORM but not in DB",
                    )
                )
                continue

            if orm_c is None:
                report.issues.append(
                    Issue(
                        kind=IssueKind.COLUMN_EXTRA_IN_DB,
                        table=table,
                        column=col_name,
                        db_value=str(db_c["type"]),
                        detail=f"Column '{col_name}' exists in DB but not in ORM",
                    )
                )
                continue

            # Type comparison
            db_type = _normalise_type_str(str(db_c["type"]))
            orm_type = _normalise_type_str(_get_orm_type_str(orm_c))

            if db_type != orm_type:
                report.issues.append(
                    Issue(
                        kind=IssueKind.COLUMN_TYPE_MISMATCH,
                        table=table,
                        column=col_name,
                        db_value=db_type,
                        orm_value=orm_type,
                    )
                )

            # Nullable comparison
            db_nullable = db_c.get("nullable", True)
            orm_nullable = orm_c.nullable
            if db_nullable != orm_nullable:
                report.issues.append(
                    Issue(
                        kind=IssueKind.COLUMN_NULLABLE_MISMATCH,
                        table=table,
                        column=col_name,
                        db_value="nullable" if db_nullable else "NOT NULL",
                        orm_value="nullable" if orm_nullable else "NOT NULL",
                    )
                )

            # Default comparison (handles TextClause server_default safely)
            db_default = db_c.get("default")
            try:
                orm_default_raw = orm_c.server_default.arg if orm_c.server_default else None
                orm_default = str(orm_default_raw) if orm_default_raw is not None else None
            except Exception:
                orm_default = f"<{type(orm_c.server_default.arg).__name__}>" if orm_c.server_default else None
            if str(db_default) != str(orm_default):
                report.issues.append(
                    Issue(
                        kind=IssueKind.COLUMN_DEFAULT_MISMATCH,
                        table=table,
                        column=col_name,
                        db_value=str(db_default) if db_default is not None else "None",
                        orm_value=str(orm_default) if orm_default is not None else "None",
                    )
                )

        # ── Index-level issues ─────────────────────────────────────────
        if check_indexes:
            try:
                db_indexes = {i["name"]: i for i in inspector.get_indexes(table)}
            except Exception:
                db_indexes = {}

            orm_indexes = {}
            for idx in orm_table.indexes:
                orm_indexes[idx.name] = {
                    "name": idx.name,
                    "columns": [c.name for c in idx.columns],
                    "unique": idx.unique,
                }

            all_idx_names = set(list(db_indexes.keys()) + list(orm_indexes.keys()))
            for idx_name in sorted(all_idx_names):
                db_idx = db_indexes.get(idx_name)
                orm_idx = orm_indexes.get(idx_name)

                if db_idx is None:
                    assert orm_idx is not None
                    cols_str = ", ".join(orm_idx["columns"])
                    create_sql = (
                        f"CREATE {'UNIQUE ' if orm_idx['unique'] else ''}"
                        f"INDEX {idx_name} ON {table} ({cols_str});"
                    )
                    report.issues.append(
                        Issue(
                            kind=IssueKind.INDEX_MISSING_IN_DB,
                            table=table,
                            column=idx_name,
                            detail=create_sql,
                        )
                    )
                elif orm_idx is None:
                    report.issues.append(
                        Issue(
                            kind=IssueKind.INDEX_EXTRA_IN_DB,
                            table=table,
                            column=idx_name,
                            detail=f"Index '{idx_name}' exists in DB but not in ORM",
                        )
                    )
                else:
                    # Compare columns
                    db_cols_list = db_idx.get("columns", [])
                    orm_cols_list = orm_idx.get("columns", [])
                    if db_cols_list != orm_cols_list:
                        report.issues.append(
                            Issue(
                                kind=IssueKind.INDEX_COLUMNS_MISMATCH,
                                table=table,
                                column=idx_name,
                                db_value=str(db_cols_list),
                                orm_value=str(orm_cols_list),
                            )
                        )
                    if db_idx.get("unique") != orm_idx.get("unique"):
                        report.issues.append(
                            Issue(
                                kind=IssueKind.INDEX_UNIQUE_MISMATCH,
                                table=table,
                                column=idx_name,
                                db_value="unique" if db_idx.get("unique") else "non-unique",
                                orm_value="unique" if orm_idx.get("unique") else "non-unique",
                            )
                        )

        # ── Foreign-key issues ─────────────────────────────────────────
        if check_fks:
            try:
                db_fks = inspector.get_foreign_keys(table)
            except Exception:
                db_fks = []

            orm_fks = list(orm_table.foreign_keys)

            # Compare by referred table + column
            db_fk_set: set[tuple[str, str]] = set()
            for fk in db_fks:
                referred_table = fk.get("referred_table", "")
                referred_cols = fk.get("referred_columns", [])
                constrained_cols = fk.get("constrained_columns", [])
                for c in constrained_cols:
                    for r in referred_cols:
                        db_fk_set.add((c, f"{referred_table}.{r}"))

            orm_fk_set: set[tuple[str, str]] = set()
            for fk in orm_fks:
                col_name = fk.parent.name
                referred = f"{fk.column.table.name}.{fk.column.name}"
                orm_fk_set.add((col_name, referred))

            for col_name, ref in sorted(orm_fk_set - db_fk_set):
                report.issues.append(
                    Issue(
                        kind=IssueKind.FK_MISSING_IN_DB,
                        table=table,
                        column=col_name,
                        detail=f"FK {col_name} → {ref} exists in ORM but not in DB",
                    )
                )

            for col_name, ref in sorted(db_fk_set - orm_fk_set):
                report.issues.append(
                    Issue(
                        kind=IssueKind.FK_EXTRA_IN_DB,
                        table=table,
                        column=col_name,
                        detail=f"FK {col_name} → {ref} exists in DB but not in ORM",
                    )
                )

            # Detailed column match
            db_fk_map: dict[str, str] = {}
            for fk in db_fks:
                constrained = fk.get("constrained_columns", [])
                referred = fk.get("referred_columns", [])
                referred_table = fk.get("referred_table", "")
                for i, c in enumerate(constrained):
                    r = referred[i] if i < len(referred) else "?"
                    db_fk_map[c] = f"{referred_table}.{r}"

            orm_fk_map: dict[str, str] = {}
            for fk in orm_fks:
                col_name = fk.parent.name
                referred = f"{fk.column.table.name}.{fk.column.name}"
                orm_fk_map[col_name] = referred

            common_fk_cols = set(db_fk_map.keys()) & set(orm_fk_map.keys())
            for col_name in sorted(common_fk_cols):
                db_ref = db_fk_map[col_name]
                orm_ref = orm_fk_map[col_name]
                if db_ref != orm_ref:
                    report.issues.append(
                        Issue(
                            kind=IssueKind.FK_COLUMNS_MISMATCH,
                            table=table,
                            column=col_name,
                            db_value=db_ref,
                            orm_value=orm_ref,
                        )
                    )

    report.elapsed_seconds = time.time() - t0
    return report


# ── CLI ──────────────────────────────────────────────────────────────────


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Schema Audit — compare ORM metadata against the live database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--table", "-t",
        type=str,
        default=None,
        help="Filter by table name (glob pattern, e.g. 'order*' or 'user*')",
    )
    p.add_argument(
        "--summary", "-s",
        action="store_true",
        help="Show summary only, no per-column detail",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (for pipelines)",
    )
    p.add_argument(
        "--no-indexes",
        action="store_true",
        help="Skip index comparison",
    )
    p.add_argument(
        "--no-fks",
        action="store_true",
        help="Skip foreign-key comparison",
    )
    p.add_argument(
        "--fix",
        action="store_true",
        help="Generate SQL to sync DB to ORM (dry-run, no execution)",
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="With --fix, actually execute fix SQL against the database",
    )
    p.add_argument(
        "--min-priority",
        type=int,
        default=0,
        help="Minimum priority level (0=all, 1=tables, 2=+columns, 3=+types/indexes/FKs, 4=+defaults)",
    )
    p.add_argument(
        "--no-alembic",
        action="store_true",
        help="Skip Alembic migration-tree integrity check",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    report = audit_schema(
        table_filter=args.table,
        check_indexes=not args.no_indexes,
        check_fks=not args.no_fks,
        include_alembic=not args.no_alembic,
    )

    if args.json:
        alembic_json = None
        if report.alembic:
            a = report.alembic
            alembic_json = {
                "stamped_version": a.stamped_version,
                "migration_file_count": a.migration_file_count,
                "total_revisions": a.total_revisions,
                "roots": a.roots,
                "heads": a.heads,
                "head_version": a.head_version,
                "is_stamped": a.is_stamped,
                "is_linear": a.is_linear,
                "head_matches_stamp": a.head_matches_stamp,
            }
        data = {
            "db_table_count": report.db_table_count,
            "orm_table_count": report.orm_table_count,
            "elapsed_seconds": round(report.elapsed_seconds, 2),
            "issue_count": len(report.issues),
            "healthy": report.healthy,
            "alembic": alembic_json,
            "issues": [
                {
                    "kind": i.kind.value,
                    "table": i.table,
                    "column": i.column,
                    "db_value": i.db_value,
                    "orm_value": i.orm_value,
                    "detail": i.detail,
                }
                for i in report.issues
            ],
        }
        print(json.dumps(data, indent=2))
        return 0 if report.healthy else 1

    # ── Print summary ──────────────────────────────────────────────────
    print("=" * 72)
    print("  SCHEMA AUDIT REPORT")
    print("=" * 72)
    for line in report.summary_lines():
        print(f"  {line}")
    print(f"  Elapsed: {report.elapsed_seconds:.2f}s")
    print()

    if args.summary:
        return 0 if report.healthy else 1

    # ── Print per-table issues ─────────────────────────────────────────
    groups = report.group_by_kind()
    for kind in sorted(groups, key=lambda k: PRIORITY.get(k, 99)):
        priority = PRIORITY.get(kind, 99)
        if priority < args.min_priority:
            continue
        issues = groups[kind]
        print(f"── [{kind.value}] ({len(issues)}) ─────────────────────")
        for issue in sorted(issues, key=lambda i: f"{i.table}.{i.column or ''}"):
            print(f"    {issue}")
        print()

    # ── Fix SQL ────────────────────────────────────────────────────────
    if args.fix:
        sql = report.fix_sql()
        if sql:
            print("── FIX SQL (dry-run) ────────────────────────────────")
            print("  ⚠ SQLite limitations: only ADD COLUMN and CREATE INDEX supported.")
            print("  ⚠ Use Alembic migrations for NOT NULL changes, column drops, or FK changes.")
            print()
            for stmt in sql:
                print(f"  {stmt}")
            print()
            if args.apply:
                from db.database import engine
                from sqlalchemy import text
                print("  Applying fixes...")
                with engine.connect() as conn:
                    for stmt in sql:
                        try:
                            conn.execute(text(stmt))
                            print(f"  ✓ {stmt[:60]}...")
                        except Exception as exc:
                            print(f"  ✗ {stmt[:60]}...  {exc}")
                    conn.commit()
                print("  Done.")
        else:
            print("  No fix SQL generated — all schema issues require Alembic migrations.")
        print()

    final = "✅ SCHEMA IS HEALTHY" if report.healthy else f"❌ {len(report.issues)} ISSUES FOUND"
    print(final)
    return 0 if report.healthy else 1


if __name__ == "__main__":
    sys.exit(main())
