"""Phase 4E — mixin adoption enforcement test.

Per ARCHITECTURE_DIAGRAM.md Laws 23, 45, 50, 51, 52, 53 every domain model must
adopt the canonical mixins from ``infrastructure.database.mixins``:

  - AuditMixin      — created_at / updated_at / created_by / updated_by
  - SoftDeleteMixin — is_deleted / deleted_at / deleted_by
  - TenantMixin     — country_code (Law 5)
  - VersionMixin    — optimistic-lock counter

Phase 2H only refactored ``WishlistItem``. Phase 4E expands adoption to all
16 domains. This test enforces the moving target: any domain model that has
not been refactored yet fails; once refactored, it passes.

The test reads from ``Base.metadata.tables`` (the authoritative SQLAlchemy
source) to survive the ``test_architecture_gates::TestAppBoot`` re-import
side-effects — see ``test_mixin_reuse.py`` for the same rationale.
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


REQUIRED_COLUMNS = {
    "created_at",
    "updated_at",
    "is_deleted",
    "country_code",
    "version",
}

SYSTEM_TABLE_ALLOWLIST = {
    # tables that legitimately opt out of mixin columns (cross-domain enums,
    # append-only WORM stores, etc.)
    "accounts.audit_logs",          # WORM audit chain, separate schema
    "audit.audit_command_center_views",  # view, not table
}


def _iter_domain_tables():
    """Yield (table_name, sqlalchemy.Table) for every domain ORM table."""
    from infrastructure.database.base import Base
    for name, table in Base.metadata.tables.items():
        yield name, table


def _domain_tables():
    """Yield only tables owned by a bounded-context schema (not accounts/audit/governance)."""
    skip = {"accounts", "audit", "governance", "kernel", "rbac", "public"}
    for name, table in _iter_domain_tables():
        schema = (table.schema or "public").lower()
        if schema in skip:
            continue
        yield name, table


def test_all_domain_models_have_mixin_columns():
    """Every domain table must carry the 5 mixin columns.

    This is the moving-target test. Once a model is refactored to inherit
    the 4 mixins, this test passes for that model. Until then, the test
    fails and points to the file that still declares the columns inline.
    """
    from infrastructure.database.base import Base

    failures: list[tuple[str, set[str]]] = []
    checked = 0
    for table_name, table in _domain_tables():
        if table_name in SYSTEM_TABLE_ALLOWLIST:
            continue
        checked += 1
        column_names = {c.name for c in table.columns}
        missing = REQUIRED_COLUMNS - column_names
        if missing:
            failures.append((table_name, missing))

    assert not failures, (
        f"{len(failures)}/{checked} domain tables are missing canonical mixin columns. "
        "Refactor the model to inherit AuditMixin, SoftDeleteMixin, TenantMixin, VersionMixin. "
        f"First failures: {failures[:5]}"
    )


def test_mixin_adoption_percentage():
    """Log the % of domain tables that now use mixins. This is a soft
    assertion that always passes; the previous test is the strict gate.
    """
    from infrastructure.database.base import Base

    total = 0
    using_mixins = 0
    for table_name, table in _domain_tables():
        if table_name in SYSTEM_TABLE_ALLOWLIST:
            continue
        total += 1
        column_names = {c.name for c in table.columns}
        if REQUIRED_COLUMNS.issubset(column_names):
            using_mixins += 1

    pct = (using_mixins / total * 100) if total else 0
    print(f"\n[Phase 4E] Mixin adoption: {using_mixins}/{total} domain tables ({pct:.1f}%)")
    assert total > 0, "No domain tables found in Base.metadata"
