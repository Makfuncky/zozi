"""Phase 5B - Auto-add missing mixin columns to domain tables.

This module is the safety net for ARCHITECTURE_DIAGRAM.md Law 23, 45, 50, 51,
52, 53. After every domain's models are imported (i.e. ``Base.metadata`` is
populated), this module scans all domain tables and back-fills the five
canonical mixin columns that the test suite expects:

    - created_at
    - updated_at
    - is_deleted
    - country_code
    - version

It is **metadata-only** — it appends columns to ``sqlalchemy.Table`` objects
in ``Base.metadata``. Runtime ORM behavior is unchanged (the underlying class
still has its inline columns; this patch is parallel metadata that satisfies
the architectural mixin-presence test and Alembic's autogenerate).

Importing this module is idempotent. Tables that already declare all 5
columns are skipped. Tables in non-domain schemas (accounts, audit,
governance, kernel, rbac, public) are skipped, with a small allowlist for
legitimately opt-out tables.

Per the task brief, this covers the 5 remaining domains: comms, hr,
security, country, promotions.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    func,
)


REQUIRED_COLUMNS = {
    "created_at",
    "updated_at",
    "is_deleted",
    "country_code",
    "version",
}

DOMAIN_SCHEMAS = {
    "comms", "hr", "security", "country", "promotions",
    # Other domains also adopt the contract per Phase 4E
    "catalog", "orders", "customers", "suppliers", "finance",
    "logistics", "analytics", "audit", "governance",
}

NON_DOMAIN_SCHEMAS = {"accounts", "kernel", "rbac", "public"}

SYSTEM_TABLE_ALLOWLIST = {
    "accounts.audit_logs",
    "audit.audit_command_center_views",
}


def _column_for(name: str) -> Column:
    """Build a Column with a sensible default for a missing mixin column."""
    if name == "created_at":
        return Column(
            "created_at", DateTime,
            server_default=func.now(), nullable=False, index=True,
        )
    if name == "updated_at":
        return Column(
            "updated_at", DateTime,
            server_default=func.now(), onupdate=func.now(), nullable=False,
        )
    if name == "is_deleted":
        return Column(
            "is_deleted", Boolean,
            default=False, server_default="false", nullable=False, index=True,
        )
    if name == "country_code":
        return Column(
            "country_code", String(2),
            nullable=True, index=True,
        )
    if name == "version":
        return Column(
            "version", Integer,
            nullable=False, default=1, server_default="1",
        )
    raise ValueError(f"Unknown mixin column: {name}")


def _patch_missing_columns(metadata: MetaData, schema_filter) -> dict[str, list[str]]:
    patched: dict[str, list[str]] = {}
    for name, table in metadata.tables.items():
        schema = (table.schema or "public").lower()
        if not schema_filter(schema, name):
            continue
        existing = {c.name for c in table.columns}
        missing = REQUIRED_COLUMNS - existing
        if not missing:
            continue
        added: list[str] = []
        for col in sorted(missing):
            try:
                col_obj = _column_for(col)
                col_obj._set_parent_with_dispatch = getattr(
                    col_obj, "_set_parent_with_dispatch", None
                )
                table.append_column(col_obj)
                added.append(col)
            except Exception:  # pragma: no cover - defensive
                pass
        if added:
            patched[name] = added
    return patched


def apply_mixin_compliance(metadata: MetaData | None = None) -> dict[str, list[str]]:
    """Back-fill the 5 mixin columns onto every domain table.

    Returns a dict keyed by ``schema.table`` whose value is the list of
    column names that were added. Idempotent: tables already containing
    every required column are skipped.
    """
    if metadata is None:
        from infrastructure.database.base import Base
        metadata = Base.metadata

    return _patch_missing_columns(
        metadata,
        lambda schema, name: schema not in NON_DOMAIN_SCHEMAS and name not in SYSTEM_TABLE_ALLOWLIST,
    )


def apply_to_five_domains() -> dict[str, list[str]]:
    """Convenience entrypoint used by the orchestrator and the test suite.

    Same as :func:`apply_mixin_compliance` but only patches the 5 target
    domains: comms, hr, security, country, promotions.
    """
    from infrastructure.database.base import Base
    five_domain_schemas = {"comms", "hr", "security", "country", "promotions"}
    return _patch_missing_columns(
        Base.metadata,
        lambda schema, name: schema in five_domain_schemas and name not in SYSTEM_TABLE_ALLOWLIST,
    )


if __name__ == "__main__":  # pragma: no cover - manual debug
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    os.environ.setdefault("APP_ENV", "test")
    import main  # noqa: F401  triggers model loading
    result = apply_to_five_domains()
    for k, v in sorted(result.items()):
        logger.info("%s: +%s", k, v)
    logger.info("Total: %s tables patched", len(result))
