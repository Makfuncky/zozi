"""Audit logs full-text search (Law 55 — tsvector + GIN).

Adds a generated ``search_vector`` tsvector column on ``audit.audit_logs``,
populated by trigger from action / username / user_agent / ip_address /
details. Backfills existing rows and creates a GIN index for fast lookup.

Revision ID: 2026_09_03_0004
Revises: 2026_09_03_0003
Create Date: 2026-09-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2026_09_03_0004"
down_revision: Union[str, None] = "2026_09_03_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION audit.audit_logs_search_vector_update()
RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', coalesce(NEW.action, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(NEW.username, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(NEW.user_agent, '')), 'C') ||
    setweight(to_tsvector('english', coalesce(NEW.ip_address, '')), 'C') ||
    setweight(to_tsvector('english', coalesce(NEW.details::text, '')), 'D');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;
"""


_TRIGGER = """
DROP TRIGGER IF EXISTS trg_audit_logs_search_vector ON audit.audit_logs;
CREATE TRIGGER trg_audit_logs_search_vector
BEFORE INSERT OR UPDATE OF action, username, user_agent, ip_address, details
ON audit.audit_logs
FOR EACH ROW EXECUTE FUNCTION audit.audit_logs_search_vector_update();
"""


def upgrade() -> None:
    bind = op.get_bind()
    # ADR-019 / ADR-028: tsvector + GIN + plpgsql trigger are PG-only.
    if bind.dialect.name != "postgresql":
        return
    inspector = sa.inspect(bind)
    if "audit_logs" not in inspector.get_table_names(schema="audit"):
        return

    existing = {c["name"] for c in inspector.get_columns("audit_logs", schema="audit")}
    if "search_vector" not in existing:
        op.execute(
            "ALTER TABLE audit.audit_logs ADD COLUMN search_vector tsvector"
        )

    op.execute(_TRIGGER_FN)
    op.execute(_TRIGGER)

    # backfill existing rows
    op.execute(
        """
        UPDATE audit.audit_logs
        SET search_vector =
            setweight(to_tsvector('english', coalesce(action, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(username, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(user_agent, '')), 'C') ||
            setweight(to_tsvector('english', coalesce(ip_address, '')), 'C') ||
            setweight(to_tsvector('english', coalesce(details::text, '')), 'D')
        WHERE search_vector IS NULL
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_audit_logs_search_vector_gin "
        "ON audit.audit_logs USING GIN (search_vector)"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_search_vector ON audit.audit_logs")
    op.execute("DROP FUNCTION IF EXISTS audit.audit_logs_search_vector_update()")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_search_vector_gin")
    op.execute("ALTER TABLE audit.audit_logs DROP COLUMN IF EXISTS search_vector")
