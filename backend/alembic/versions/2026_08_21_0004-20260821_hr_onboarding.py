"""re-home ``OnboardingPipeline`` / ``OnboardingStep`` into the hr domain (code move only)

A3 (RESOLVER.md §26 ACC-01): the ``onboarding_pipelines`` and ``onboarding_steps``
tables (schema ``hr``) were defined inside the accounts God-domain module
(``domains.governance.models.onboarding``) but belong to the ``hr`` bounded context.
Their canonical ORM definitions are now in ``domains.hr.models.hr_schema_models``;
``domains.governance.models.onboarding`` keeps re-exports for legacy imports.

This is a pure code relocation. The physical tables already exist under the ``hr``
schema in both environments -- SQLite (dev) via ``create_all`` and PostgreSQL
(prod) -- so no DDL is required. The revision exists only to record the re-home in
the migration chain and is intentionally a no-op on every supported dialect.

Revision ID: 20260821_hr_onboarding
Revises: 20260821_hr_shift_handover_task
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260821_hr_onboarding"
down_revision: Union[str, None] = "20260821_hr_shift_handover_task"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No DDL: the ``hr.onboarding_pipelines`` / ``hr.onboarding_steps`` tables are unchanged.
    pass


def downgrade() -> None:
    # No DDL: reverting this code move does not alter the physical tables.
    pass
