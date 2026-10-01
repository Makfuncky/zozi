"""create employee_activity_logs table (DBA13)

Resolves the audit finding that ``employee_activity_logs`` (the HCM
security/audit trail defined in ``models/employee_models.py`` as
``EmployeeActivityLog``) has no Alembic migration. In development the table
is produced by ``create_all``; in production (PostgreSQL) it was never
created by a migration, so any code path querying it would fail at runtime.

The table is created in the ``logistics`` schema with the exact column set,
types, foreign key, and indexes declared on the ORM model, so the migration
and the ORM stay in agreement for this table (mitigating the broader DBA12
dual-source drift rather than adding to it).

DBA23 (partitioning parity with audit_logs/notifications/shipment_events)
is intentionally NOT applied here: PostgreSQL requires a partitioned table's
PRIMARY KEY to include the partition key column, but the ORM defines ``id``
as the sole PK. Partitioning this table would require changing the ORM model
(arithmetic change to the DBA12 consolidation effort) and would reproduce the
ORM/DB drift that ``audit_logs`` already exhibits. It is tracked as part of
the DBA12 dual-source unification and left flat for now.

Revision ID: 20260810_emp_act_log
Revises: ccw_unify_20260809
Create Date: 2026-08-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260810_emp_act_log"
down_revision: Union[str, None] = "ccw_unify_20260809"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "employee_activity_logs"
_SCHEMA = "logistics"


def upgrade() -> None:
    # This table is only managed by Alembic on PostgreSQL. On SQLite (dev)
    # it is produced by create_all, matching the project's existing split
    # between dev (create_all) and prod (alembic) — see ccw_unify migration.
    if op.get_context().dialect.name != "postgresql":
        return

    op.execute("CREATE SCHEMA IF NOT EXISTS logistics")

    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "actor_employee_id",
            sa.Integer,
            sa.ForeignKey(_SCHEMA + ".employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("metadata_json", sa.JSON, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("device_fingerprint", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        schema=_SCHEMA,
    )

    op.create_index(
        "ix_employee_activity_actor",
        _TABLE,
        ["actor_employee_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_employee_activity_created",
        _TABLE,
        ["created_at"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_employee_activity_logs_metadata_json",
        _TABLE,
        ["metadata_json"],
        postgresql_using="gin",
        schema=_SCHEMA,
    )


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    op.drop_index("ix_employee_activity_logs_metadata_json", table_name=_TABLE, schema=_SCHEMA)
    op.drop_index("ix_employee_activity_created", table_name=_TABLE, schema=_SCHEMA)
    op.drop_index("ix_employee_activity_actor", table_name=_TABLE, schema=_SCHEMA)
    op.drop_table(_TABLE, schema=_SCHEMA)
