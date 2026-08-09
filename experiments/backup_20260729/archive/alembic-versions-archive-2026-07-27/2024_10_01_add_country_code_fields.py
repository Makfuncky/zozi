"""Add country_code foreign keys to key tables

Revision ID: 2024_10_01
Revises: a1b2c3d4e5f6
Create Date: 2024-10-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2024_10_01_add_country_code_fields'
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

def upgrade():
    # Add country_code to SupplierProfile
    op.add_column('supplier_profiles', sa.Column('country_code', sa.String(10), sa.ForeignKey('country_configs.code'), nullable=True, index=True))
    # Add country_code to LogisticsPartner
    op.add_column('logistics_partners', sa.Column('country_code', sa.String(10), sa.ForeignKey('country_configs.code'), nullable=True, index=True))
    # Add country_code to CommissionAgreement
    op.add_column('commission_agreements', sa.Column('country_code', sa.String(10), sa.ForeignKey('country_configs.code'), nullable=True, index=True))
    # Add country_code to User
    op.add_column('users', sa.Column('country_code', sa.String(10), sa.ForeignKey('country_configs.code'), nullable=True, index=True))
    # Add country_code to Product
    op.add_column('products', sa.Column('country_code', sa.String(10), sa.ForeignKey('country_configs.code'), nullable=True, index=True))
    # Add country_code to Payment
    op.add_column('payments', sa.Column('country_code', sa.String(10), sa.ForeignKey('country_configs.code'), nullable=True, index=True))

def downgrade():
    op.drop_column('supplier_profiles', 'country_code')
    op.drop_column('logistics_partners', 'country_code')
    op.drop_column('commission_agreements', 'country_code')
    op.drop_column('users', 'country_code')
    op.drop_column('products', 'country_code')
    op.drop_column('payments', 'country_code')

