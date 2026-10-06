"""add comms faqs/announcements/internal_emails/proxy_channels timestamp server_default

ARCHITECTURE_STACK.md Law 21: ``created_at``/``updated_at`` use
``server_default=func.now()`` **DB-side**, not Python-side.

Audit block FILE 75 (``backend/domains/comms/models/communication.py``,
dimension ``07_tables_fields``) asserted Law 21 across the file. Adjudication
showed exactly one ``created_at`` column in the file still used a Python-side
default — ``FAQ.created_at``, declared as ``Column(DateTime, default=utcnow)`` —
plus three ``updated_at`` columns carrying the identical
``default=utcnow, onupdate=utcnow`` Python-side pattern (``Announcement``,
``InternalEmail``, ``ProxyChannel``). Those four declarations are corrected here.

The other 21 audit findings in that block pointed at columns that already carried
``server_default=func.now()`` (every ``created_at`` except ``FAQ``) or at a
``country_code`` column that is present on all 20 models (explicitly declared, or
supplied by ``TenantMixin.country_code`` which is ``String(2)``). Those were
false positives and are addressed by
``backend/tests/domains/comms/test_communication_model_laws.py``, not by schema
change.

Why a migration is still required — Alembic is the schema source of truth (Law 6).
The only ``op.create_table`` for these four tables,
``20260806_0003-20260806_0003_baseline_sync_orm_tables.py``, emits them without
any ``server_default``:

  - ``faqs``            line 2461  ``sa.Column('created_at', sa.DateTime(), nullable=True)``
  - ``announcements``   line 398   ``sa.Column('updated_at', sa.DateTime(), nullable=True)``
  - ``internal_emails`` line 3102  ``sa.Column('updated_at', sa.DateTime(), nullable=True)``
  - ``proxy_channels``  line 4986  ``sa.Column('updated_at', sa.DateTime(), nullable=True)``

and no later revision in the chain alters a default on any of them. So a database
built purely by ``alembic upgrade head`` would disagree with the corrected ORM,
while a database bootstrapped from ORM metadata already agrees. This revision makes
the chain authoritative and the two paths converge. The live schema was observed
to carry ``now()`` on all four columns already, which this revision preserves
rather than rewrites.

Expand-contract (Law 57): attaching a column default is purely additive and
backward compatible. Existing rows are untouched, the column is never dropped or
retyped, and old writers that still supply the value keep working.
``downgrade()`` removes only the default this revision introduced.

Idempotent: every step inspects the live catalog first, so a database already
carrying ``now()`` is a no-op and re-running converges to the same state.

Skipped on SQLite: SQLite rejects ``DEFAULT (now())`` (it accepts only constant
defaults), and dev/test SQLite databases are rebuilt from ORM metadata, which now
carries ``server_default=func.now()``. Same rationale as
``20261003_0001_add_logistics_entities_created_at_server_default.py``.
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


revision: str = "20261003_0011"
down_revision: Union[str, None] = "20261003_0010"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")

SCHEMA = "comms"

# (table, column) pairs whose ORM declaration in
# domains/comms/models/communication.py is
# Column(DateTime, server_default=func.now()).
# FAQ.created_at is the audited column (TF-077); the three updated_at entries are
# the same Python-side-default defect the Law 21 audit surfaced in this file.
TARGET_COLUMNS: tuple[tuple[str, str], ...] = (
    ("faqs", "created_at"),
    ("announcements", "updated_at"),
    ("internal_emails", "updated_at"),
    ("proxy_channels", "updated_at"),
)


def _columns(inspector: sa.Inspector, table: str) -> dict:
    """Catalog columns for ``comms.<table>``; empty dict when absent."""
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


def _nullable(col: dict) -> bool:
    """Preserve the column's current nullability instead of forcing one."""
    return bool(col.get("nullable", True))


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        logger.info("A06 Law 21: sqlite does not accept DEFAULT now(); relying on ORM bootstrap")
        return

    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)

    for table, column in TARGET_COLUMNS:
        columns = _columns(inspector, table)
        if not columns:
            logger.warning("A06 Law 21: comms.%s absent, nothing to default", table)
            continue

        if column not in columns:
            logger.warning(
                "A06 Law 21: comms.%s.%s absent, leaving the schema untouched", table, column
            )
            continue

        if _has_now_default(columns[column]):
            logger.info("A06 Law 21: comms.%s.%s already defaults to now()", table, column)
            continue

        with op.batch_alter_table(table, schema=SCHEMA) as batch_op:
            batch_op.alter_column(
                column,
                existing_type=sa.DateTime(),
                nullable=_nullable(columns[column]),
                server_default=sa.func.now(),
            )
        logger.info(
            "A06 Law 21: set server_default now() on comms.%s.%s", table, column
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)

    for table, column in TARGET_COLUMNS:
        col = _columns(inspector, table).get(column)
        if col is None:
            continue
        if not _has_now_default(col):
            continue
        with op.batch_alter_table(table, schema=SCHEMA) as batch_op:
            batch_op.alter_column(
                column,
                existing_type=sa.DateTime(),
                nullable=_nullable(col),
                server_default=None,
            )
        logger.info(
            "A06 Law 21: removed server_default from comms.%s.%s", table, column
        )
