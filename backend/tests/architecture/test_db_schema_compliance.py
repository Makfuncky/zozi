"""Phase 4E — database column sanity test.

Per ARCHITECTURE_DIAGRAM.md §4.4.1-4.4.5 every domain model must:

  - carry ``created_at`` and ``updated_at`` audit columns       (Law 23, 53)
  - carry a ``country_code`` String(2) column                   (Law 20, 53)
  - carry an ``is_deleted`` Boolean column                      (Law 51, 53)

This test is the moving-target gate enforced by CI. It inspects every
table registered on ``Base.metadata`` and fails if any table violates
the contract. The optional ``test_db_schema_summary`` prints current
stats for visibility.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


SYSTEM_TABLE_ALLOWLIST = {
    "accounts.audit_logs",
    "audit.audit_command_center_views",
}


def _iter_tables():
    from infrastructure.database.base import Base
    yield from Base.metadata.tables.items()


def _domain_schema_for(table_name: str) -> str | None:
    if "." in table_name:
        return table_name.split(".", 1)[0]
    return None


def test_table_args_has_schema():
    """Law 6, 50, 52 — every model declares its schema in __table_args__.

    Verified by inspecting the Table.schema attribute (which is the
    canonical SQLAlchemy source populated by ``{"schema": ...}``).
    """
    failures = []
    for table_name, table in _iter_tables():
        if table_name in SYSTEM_TABLE_ALLOWLIST:
            continue
        if table.schema is None:
            failures.append(table_name)

    assert not failures, (
        f"{len(failures)} tables are missing __table_args__['schema']. "
        f"Offenders: {failures[:10]}"
    )


def test_table_has_created_at():
    """Law 23, 53 — every model carries created_at."""
    failures = []
    for table_name, table in _iter_tables():
        if table_name in SYSTEM_TABLE_ALLOWLIST:
            continue
        if "created_at" not in {c.name for c in table.columns}:
            failures.append(table_name)

    assert not failures, (
        f"{len(failures)} tables are missing created_at. Offenders: {failures[:10]}"
    )


def test_table_has_updated_at():
    """Law 23, 53 — every model carries updated_at."""
    failures = []
    for table_name, table in _iter_tables():
        if table_name in SYSTEM_TABLE_ALLOWLIST:
            continue
        if "updated_at" not in {c.name for c in table.columns}:
            failures.append(table_name)

    assert not failures, (
        f"{len(failures)} tables are missing updated_at. Offenders: {failures[:10]}"
    )


def test_table_has_country_code():
    """Law 20, 53 — every model carries country_code (String(2))."""
    failures = []
    for table_name, table in _iter_tables():
        if table_name in SYSTEM_TABLE_ALLOWLIST:
            continue
        for col in table.columns:
            if col.name == "country_code":
                break
        else:
            failures.append(table_name)

    assert not failures, (
        f"{len(failures)} tables are missing country_code. Offenders: {failures[:10]}"
    )


def test_table_has_is_deleted():
    """Law 51, 53 — every model carries is_deleted (Boolean)."""
    failures = []
    for table_name, table in _iter_tables():
        if table_name in SYSTEM_TABLE_ALLOWLIST:
            continue
        if "is_deleted" not in {c.name for c in table.columns}:
            failures.append(table_name)

    assert not failures, (
        f"{len(failures)} tables are missing is_deleted. Offenders: {failures[:10]}"
    )


def test_db_schema_summary():
    """Soft print of current schema coverage. Always passes."""
    from infrastructure.database.base import Base
    schemas = {t.schema for t in Base.metadata.tables.values() if t.schema}
    tables = len(Base.metadata.tables)
    print(f"\n[Phase 4E] Tables registered: {tables}; distinct schemas: {len(schemas)}")
    print(f"[Phase 4E] Schemas: {sorted(schemas)}")
    assert tables > 0
