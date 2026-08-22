"""cross-cutting domains (audit / analytics / security) created

Re-homes the ``audit``, ``analytics``, ``ai`` and ``security`` schema tables out of
the accounts God-domain into owning domains (A3 / §26 ACC-01). Pure code move —
no physical schema change — so this revision is a no-op.

Revision ID: 20260821_crosscutting_domains
Revises: 20260821_hr_onboarding
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260821_crosscutting_domains"
down_revision = "20260821_hr_onboarding"
branch_labels = None
depends_on = None


def upgrade():
    # No schema change: tables only re-homed into owning domains.
    pass


def downgrade():
    pass
