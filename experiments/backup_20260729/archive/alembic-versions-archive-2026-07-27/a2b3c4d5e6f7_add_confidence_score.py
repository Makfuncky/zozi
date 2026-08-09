"""Migration to add confidence_score field to CountryConfig."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a2b3c4d5e6f7_add_confidence_score'
down_revision = 's_a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('country_configs', sa.Column('confidence_score', sa.Numeric(5, 4), nullable=True, server_default='0.0000'))


def downgrade():
    op.drop_column('country_configs', 'confidence_score')
