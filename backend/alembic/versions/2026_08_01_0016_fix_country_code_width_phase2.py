"""fix_country_code_width_phase2

Constitution §2.6 / App. F finding *(c)*: ``country_code`` must be
``VARCHAR(3)`` everywhere so that joins between country-scoped tables never
break.  Migration 0007 (Phase 5) fixed the split tables; this migration
catches the 9 tables that migration 0010 / 0000 / 0002 still created with
``VARCHAR(10)``.

Tables fixed (PostgreSQL only — SQLite ignores width at runtime):
  communication.internal_channels
  communication.notifications
  communication.faqs
  hr.employee_communication_threads
  hr.employee_active_tasks
  finance.commission_rules
  audit.worm_audit
  configuration.feature_flags
  public.country_blackout_dates  (no schema on PG; stays in public after 0005)

No data migration needed: ISO-3166-1 alpha-3 codes are at most 3 chars.
Any value > 3 chars would be a data bug surfaced immediately by the
``VARCHAR(3)`` cast.

Revision ID: 20260801_0016
Revises: 20260801_0015
Create Date: 2026-08-01
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260801_0016"
down_revision: Union[str, None] = "20260801_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLES: list[tuple[str | None, str]] = [
    ("communication", "internal_channels"),
    ("communication", "notifications"),
    ("communication", "faqs"),
    ("hr", "employee_communication_threads"),
    ("hr", "employee_active_tasks"),
    ("commerce", "commission_rules"),
    ("audit", "worm_audit"),
    ("configuration", "feature_flags"),
    (None, "country_blackout_dates"),
]


def _table_fqn(schema: str | None, table: str) -> str:
    if schema:
        return f'"{schema}"."{table}"'
    return f'"{table}"'


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    for schema, table in _TABLES:
        fqn = _table_fqn(schema, table)
        op.execute(
            f"ALTER TABLE IF EXISTS {fqn} "
            f'ALTER COLUMN country_code TYPE VARCHAR(3)'
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    for schema, table in _TABLES:
        fqn = _table_fqn(schema, table)
        op.execute(
            f"ALTER TABLE IF EXISTS {fqn} "
            f'ALTER COLUMN country_code TYPE VARCHAR(10)'
        )
