"""add logistics entities created_at server_default

ARCHITECTURE_STACK.md Law 21: ``created_at``/``updated_at`` use
``server_default=func.now()`` **DB-side**, not Python-side.

The ORM half of Law 21 for the eight ``logistics`` tables owned by
``domains/logistics/models/logistics_entities.py`` was already corrected in the
model (audit TF-218..TF-225), but no Alembic revision ever produced the
DB-side default, so Alembic was not the schema source of truth for the column
(Law 6). Evidence: the only ``op.create_table`` for these tables,
``20260806_0003_baseline_sync_orm_tables.py``, emits
``sa.Column('created_at', sa.DateTime(), nullable=True)`` with no
``server_default`` (and for ``logistics.logistics_partners`` it omits
``created_at`` entirely, lines 3639-3676).

This revision makes the DB-side default authoritative for:

  - logistics.logistics_category_pricing_rules  (TF-218)
  - logistics.logistics_partner_profiles        (TF-219)
  - logistics.logistics_partner_service_areas   (TF-220)
  - logistics.logistics_partners                (TF-221)
  - logistics.logistics_pricing_profiles        (TF-222)
  - logistics.logistics_vehicle_rules           (TF-223)
  - logistics.shipment_events                   (TF-224)
  - logistics.shipments                         (TF-225)

Expand-contract (Law 57): adding a column default is purely additive and
backward compatible — existing rows are untouched, and old application code that
still supplies ``created_at`` keeps working. ``downgrade()`` removes only the
default that this revision introduced; it never drops a column the baseline
created.

Idempotent: every step inspects the live catalog first, so a database that was
bootstrapped from ORM metadata (dev/test) is a no-op, and a database built
purely from the migration chain ends up in exactly the same state. That
convergence is the point of the revision.

Skipped on SQLite: SQLite rejects ``DEFAULT (now())`` (it accepts only constant
defaults), and dev/test SQLite databases are rebuilt from ORM metadata, which
already carries ``server_default=func.now()``. Same rationale as
``20260930_0008_enforce_incident_model_audit_not_null.py``.
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


def _is_offline(conn) -> bool:
    if conn is None:
        return True
    try:
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy.exc import NoInspectionAvailable
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


revision: str = "20261003_0001"
down_revision: Union[str, None] = "20261001_0001"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")

SCHEMA = "logistics"

# Every table whose ``created_at`` is declared by
# domains/logistics/models/logistics_entities.py as
# Column(DateTime, server_default=func.now()).
TARGET_TABLES: tuple[str, ...] = (
    "logistics_category_pricing_rules",
    "logistics_partner_profiles",
    "logistics_partner_service_areas",
    "logistics_partners",
    "logistics_pricing_profiles",
    "logistics_vehicle_rules",
    "shipment_events",
    "shipments",
)

_COLUMN = "created_at"


def _columns(inspector: sa.Inspector, table: str) -> dict:
    """Catalog columns for ``logistics.<table>``; empty dict when absent."""
    try:
        return {c["name"]: c for c in inspector.get_columns(table, schema=SCHEMA)}
    except sa.exc.NoSuchTableError:
        return {}


def _has_now_default(col: dict) -> bool:
    """True when the catalog default is already a ``now()``-family expression."""
    default = col.get("default")
    if default is None:
        return False
    return "now()" in str(default) or "CURRENT_TIMESTAMP" in str(default).upper()


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        logger.info("A08 Law 21: sqlite does not accept DEFAULT now(); relying on ORM bootstrap")
        return

    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)

    for table in TARGET_TABLES:
        columns = _columns(inspector, table)
        if not columns:
            logger.warning("A08 Law 21: logistics.%s absent, nothing to default", table)
            continue

        if _COLUMN not in columns:
            # The baseline create_table for this table omitted created_at
            # entirely; add it with the same definition the ORM declares
            # (DateTime, nullable, server_default=now()) before defaulting.
            op.add_column(
                table,
                sa.Column(_COLUMN, sa.DateTime(), nullable=True, server_default=sa.func.now()),
                schema=SCHEMA,
            )
            logger.info("A08 Law 21: added logistics.%s.created_at with server_default now()", table)
            continue

        if _has_now_default(columns[_COLUMN]):
            logger.info("A08 Law 21: logistics.%s.created_at already defaults to now()", table)
            continue

        with op.batch_alter_table(table, schema=SCHEMA) as batch_op:
            batch_op.alter_column(
                _COLUMN,
                existing_type=sa.DateTime(),
                nullable=True,
                server_default=sa.func.now(),
            )
        logger.info("A08 Law 21: set server_default now() on logistics.%s.created_at", table)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)

    for table in TARGET_TABLES:
        col = _columns(inspector, table).get(_COLUMN)
        if col is None:
            continue
        if not _has_now_default(col):
            continue
        with op.batch_alter_table(table, schema=SCHEMA) as batch_op:
            batch_op.alter_column(
                _COLUMN,
                existing_type=sa.DateTime(),
                nullable=True,
                server_default=None,
            )
        logger.info("A08 Law 21: removed server_default from logistics.%s.created_at", table)
