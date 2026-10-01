"""rename the ``communication`` schema to ``comms`` (COMMS-SCHEMA)

RESOLVER.md §11.3 COMMS-SCHEMA: the true-comms tables lived in a catch-all
``communication`` schema that is not one of the 13 sanctioned bounded-context
schemas. They are moved into the canonical ``comms`` schema (one Postgres
schema per domain, ARCHITECTURE_DIAGRAM.md §9, Law 6).

PostgreSQL renames the schema atomically via ``ALTER SCHEMA ... RENAME TO`` --
every table, index, constraint, owned sequence and cross-reference under
``communication`` is moved with no data rewrite. The statements are guarded
with ``IF EXISTS`` so the migration is idempotent and safe to re-run on a DB
that was already upgraded (or built from scratch, since the earlier
migrations still create these tables under ``communication`` first).

Also folds ``email_runtime_config`` out of the catch-all ``configuration``
schema into ``comms`` (COMMS-STRUCT): it is a comms runtime concern.

On SQLite (dev) the ORM + ``create_all`` already produce the correctly-named
tables under the declared schema, so this migration is a no-op there.

NOTE: the application ``DB_SEARCH_PATH`` (infrastructure/database/database.py)
must include ``comms`` (it does after this change) so unqualified raw-SQL
references (e.g. ``FROM internal_messages``) continue to resolve.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260822_communication_to_comms_schema"
down_revision: Union[str, None] = "20260822_country_to_country_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _exec(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    _exec("CREATE SCHEMA IF NOT EXISTS comms")
    # Atomic rename: moves every table/index/constraint/sequence under
    # ``communication`` into ``comms`` (support_tickets, notifications,
    # proxy_*, internal_*, group_chat_*, incident_*, email_*, ...).
    _exec("ALTER SCHEMA IF EXISTS communication RENAME TO comms")
    # email_runtime_config lived in the catch-all configuration schema.
    _exec(
        "ALTER TABLE IF EXISTS configuration.email_runtime_config SET SCHEMA comms"
    )


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    _exec("CREATE SCHEMA IF NOT EXISTS communication")
    _exec("ALTER SCHEMA IF EXISTS comms RENAME TO communication")
    _exec(
        "ALTER TABLE IF EXISTS comms.email_runtime_config SET SCHEMA configuration"
    )
