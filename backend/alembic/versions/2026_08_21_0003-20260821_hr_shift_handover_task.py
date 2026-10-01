"""re-home ``ShiftHandoverTask`` into the hr domain (code move only)

A3 (RESOLVER.md §26 ACC-01): the ``shift_handover_tasks`` table (schema ``hr``)
was defined inside the accounts God-domain module
(``domains.governance.models.core``) but belongs to the ``hr`` bounded context.
Its canonical ORM definition is now ``domains.hr.models.hr_schema_models``;
``domains.governance.models.core`` keeps a re-export for legacy imports.

This is a pure code relocation. The physical table already exists under the
``hr`` schema in both environments -- SQLite (dev) via ``create_all`` and
PostgreSQL (prod) -- so no DDL is required. The revision exists only to record
the re-home in the migration chain and is intentionally a no-op on every
supported dialect.

Revision ID: 20260821_hr_shift_handover_task
Revises: 20260821_core_to_accounts
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260821_hr_shift_handover_task"
down_revision: Union[str, None] = "20260821_core_to_accounts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No DDL: the ``hr.shift_handover_tasks`` table is unchanged.
    pass


def downgrade() -> None:
    # No DDL: reverting this code move does not alter the physical table.
    pass
