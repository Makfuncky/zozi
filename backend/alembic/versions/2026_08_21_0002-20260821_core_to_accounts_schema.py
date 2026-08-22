"""rename the ``core`` schema to ``accounts``

Data-preserving migration. The ``core`` schema accumulated the accounts
domain's tables (users, login history, devices, addresses, sessions/tokens,
OTP, social links) plus the RBAC tables (permissions, permission_categories,
roles, role_permissions, user_permission_overrides) and two governance/admin
tables. The Python domain module is ``domains/accounts`` but its SQL schema
was still named ``core``, which is misaligned. This renames the schema so
``core.users`` becomes ``accounts.users``, matching the module name and the
rest of the bounded-context schema layout established by the F-1 commerce
split.

PostgreSQL renames the schema (and every table, index, constraint, owned
sequence, foreign key and RLS policy it contains) atomically via
``ALTER SCHEMA ... RENAME TO ...`` -- no data is rewritten. The statement is
guarded with an existence check so the migration is idempotent and safe to
re-run on a DB that was already upgraded (or built from scratch, since the
earlier migrations still create these tables under ``core`` first).

On SQLite (dev) the ORM + ``create_all`` already produce the correctly-named
tables, so this migration is a no-op there.

Revision ID: 20260821_core_to_accounts
Revises: 20260821_split_commerce
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260821_core_to_accounts"
down_revision: Union[str, None] = "20260821_split_commerce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _exec(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    # Idempotent: only rename if the schema still exists under the old name.
    _exec(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'core') "
        "THEN ALTER SCHEMA core RENAME TO accounts; "
        "END IF; END $$;"
    )


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    _exec(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'accounts') "
        "THEN ALTER SCHEMA accounts RENAME TO core; "
        "END IF; END $$;"
    )
