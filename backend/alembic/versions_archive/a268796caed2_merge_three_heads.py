"""merge_three_heads

Revision ID: a268796caed2
Revises: m9n0o1p2q3r4, p1q2r3s4t5u6, q5r6s7t8u9v0
Create Date: 2026-06-22 13:50:43.495694

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a268796caed2'
down_revision = ('m9n0o1p2q3r4', 'p1q2r3s4t5u6', 'q5r6s7t8u9v0')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

