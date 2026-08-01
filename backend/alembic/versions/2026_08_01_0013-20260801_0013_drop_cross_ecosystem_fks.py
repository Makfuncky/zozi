"""Drop cross-ecosystem FK constraints (DB06 remediation)

Revision ID: 20260801_0013
Revises: 20260731_0012
Create Date: 2026-08-01

Removes 10 cross-ecosystem FK constraints that violate DB06 / ADR-014:

  hr.employee_work_logs.employee_id      -> logistics.employees.id
  hr.employee_leave_requests.employee_id -> logistics.employees.id
  hr.employee_assets.employee_id         -> logistics.employees.id
  hr.employee_certifications.employee_id -> logistics.employees.id
  hr.employee_documents.employee_id      -> logistics.employees.id
  hr.employee_dependents.employee_id     -> logistics.employees.id
  hr.employee_relations.employee_id      -> logistics.employees.id
  hr.employee_addresses.employee_id      -> logistics.employees.id
  logistics.employees.user_id            -> core.users.id
  commerce.product_variants.country_code -> country.country_configs.code

Per DATABASE_SCOPE.md 01_DATABASE.md §4.1 / ADR-014, cross-ecosystem
communication must use services/events, not FK chains. The ORM models
no longer define these ForeignKey relationships; this migration drops
the constraints from the production database to bring it in sync.

On PostgreSQL the constraint names are looked up dynamically via
pg_constraint so the migration is robust to naming-convention changes.
On SQLite (dev/test) the tables are created fresh from the ORM metadata
so no action is required.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_0013"
down_revision: Union[str, None] = "20260731_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (schema, table, column) for each cross-ecosystem FK being dropped.
# Derived from the DB06 findings in database_audit_fresh.json.
CROSS_ECOSYSTEM_FKS: list[tuple[str, str, str]] = [
    ("logistics", "employees", "user_id"),
    ("hr", "employee_work_logs", "employee_id"),
    ("hr", "employee_leave_requests", "employee_id"),
    ("hr", "employee_assets", "employee_id"),
    ("hr", "employee_certifications", "employee_id"),
    ("hr", "employee_documents", "employee_id"),
    ("hr", "employee_dependents", "employee_id"),
    ("hr", "employee_relations", "employee_id"),
    ("hr", "employee_addresses", "employee_id"),
    ("commerce", "product_variants", "country_code"),
]


def _pg_fk_name(conn, schema: str, table: str, column: str) -> str | None:
    """Look up the FK constraint name for *schema.table.column* in PostgreSQL."""
    result = conn.execute(
        sa.text(
            """
            SELECT con.conname
              FROM pg_constraint con
              JOIN pg_class rel ON rel.oid = con.conrelid
              JOIN pg_namespace ns ON ns.oid = rel.relnamespace
              JOIN pg_attribute col ON col.attrelid = rel.oid
                                   AND col.attnum = con.conkey[ord(array_position(con.conkey, col.attnum::smallint) - 1)]
             WHERE con.contype = 'f'
               AND ns.nspname = :schema
               AND rel.relname = :table
               AND col.attname = :column
            """
        ),
        {"schema": schema, "table": table, "column": column},
    )
    row = result.fetchone()
    return row[0] if row else None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        for schema, table, column in CROSS_ECOSYSTEM_FKS:
            constraint_name = _pg_fk_name(conn, schema, table, column)
            if constraint_name:
                op.execute(
                    sa.text(
                        f'ALTER TABLE "{schema}"."{table}" '
                        f'DROP CONSTRAINT IF EXISTS "{constraint_name}"'
                    )
                )

    # SQLite (dev/test): tables are created fresh from ORM metadata which no
    # longer declares these FKs, so no DROP CONSTRAINT action is needed.
    # If an existing SQLite DB must be migrated, use a fresh re-create.


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade is not supported for migration 20260801_0013. "
        "The 10 cross-ecosystem FK constraints removed by this migration "
        "have been permanently dropped per DB06 / ADR-014. Re-adding them "
        "would re-introduce cross-ecosystem FK violations."
    )
