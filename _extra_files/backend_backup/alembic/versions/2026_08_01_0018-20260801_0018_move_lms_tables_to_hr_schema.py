"""move_lms_tables_to_hr_schema

Revision ID: 20260801_0018
Revises: 20260801_0017
Create Date: 2026-08-01

Moves the training_modules / employee_trainings tables out of the public
schema into the hr domain schema, matching the bounded-context migration
that already moved every other hr.* table (employees, employee_leave_requests,
...) but omitted these two. Idempotent and skipped on SQLite.
"""
from __future__ import annotations
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = "20260801_0018"
down_revision: Union[str, None] = "20260801_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_in_schema(conn, table_name: str, schema_name: str) -> bool:
    row = conn.execute(
        text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_name = :name"
        ),
        {"schema": schema_name, "name": table_name},
    ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    for table_name in ["training_modules", "employee_trainings"]:
        if _table_in_schema(conn, table_name, "public"):
            op.execute('ALTER TABLE IF EXISTS public."%s" SET SCHEMA "hr"' % table_name)


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    for table_name in ["training_modules", "employee_trainings"]:
        if _table_in_schema(conn, table_name, "hr"):
            op.execute('ALTER TABLE IF EXISTS "hr"."%s" SET SCHEMA "public"' % table_name)
