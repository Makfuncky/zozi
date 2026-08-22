"""customer / communication / logistics / media tables re-homed

Re-homes the ``customer``, ``communication``, ``logistics`` and ``media`` schema
tables out of the accounts God-domain into their owning domains
(``customers``, ``comms``, ``logistics``, ``media``) (A3 / §26 ACC-01). Pure code
move — no physical schema change — so this revision is a no-op.

Revision ID: 20260821_customer_comm_logistics_media
Revises: 20260821_crosscutting_domains
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260821_customer_comm_logistics_media"
down_revision = "20260821_crosscutting_domains"
branch_labels = None
depends_on = None


def upgrade():
    # No schema change: tables only re-homed into owning domains.
    pass


def downgrade():
    pass
