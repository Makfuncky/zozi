"""re-home user Referral tables to customer domain

Re-homes ``Referral`` / ``ReferralPointEvent`` (``customer`` schema) out of
``domains.accounts.models.user`` into ``domains.customers.models`` (A3 /
§26 ACC-01). Pure code move — no physical schema change — so this revision is
a no-op.

Revision ID: 20260821_user_referral_to_customer
Revises: 20260821_customer_comm_logistics_media
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260821_user_referral_to_customer"
down_revision = "20260821_customer_comm_logistics_media"
branch_labels = None
depends_on = None


def upgrade():
    # No schema change: tables only re-homed into the customer domain.
    pass


def downgrade():
    pass
