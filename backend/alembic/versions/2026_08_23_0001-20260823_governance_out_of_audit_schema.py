"""move governance-owned tables out of the catch-all ``audit`` schema into ``governance``

RESOLVER.md AUD-001 follow-up (audit-schema pollution): five governance-domain
models (``admin_activity_logs``, ``admin_analytics_snapshots``,
``admin_change_audit_logs``, ``chatbot_query_events``, ``retention_job_runs``)
were physically created in the ``audit`` bounded-context schema, but their ORM
classes live in ``domains/governance/models/`` and the ORM now declares
``schema="governance"``. Law 6 (one Postgres schema per domain, diagram §9)
requires every table in its owning domain schema, so these tables are moved
from ``audit`` into ``governance``.

PostgreSQL moves a table between schemas atomically via
``ALTER TABLE ... SET SCHEMA`` -- every index, constraint, owned sequence and
cross-reference follows the table with no data rewrite. The statements are
guarded with ``IF EXISTS`` so the migration is idempotent and safe to re-run on
a DB that was already upgraded.

On SQLite (dev) the ORM + ``schema_translate_map`` already resolve the declared
schema, so this migration is a no-op there.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260822_governance_out_of_audit_schema"
down_revision: Union[str, None] = "20260822_communication_to_comms_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables owned by the governance domain that were parked in the audit schema.
_MOVES = (
    "admin_activity_logs",
    "admin_analytics_snapshots",
    "admin_change_audit_logs",
    "chatbot_query_events",
    "retention_job_runs",
)


def _exec(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    _exec("CREATE SCHEMA IF NOT EXISTS governance")
    for table in _MOVES:
        _exec(f'ALTER TABLE IF EXISTS audit.{table} SET SCHEMA governance')


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    _exec("CREATE SCHEMA IF NOT EXISTS audit")
    for table in _MOVES:
        _exec(f'ALTER TABLE IF EXISTS governance.{table} SET SCHEMA audit')
