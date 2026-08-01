"""add_country_management_tables

Revision ID: a1b2c3d4e5f7b
Revises: 5ca199ab0c03
Create Date: 2024-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f7b'
down_revision = '5ca199ab0c03'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'country_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(10), unique=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('currency_symbol', sa.String(10), nullable=True),
        sa.Column('phone_code', sa.String(10), nullable=True),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('timezone', sa.String(60), nullable=True),
        sa.Column('date_format', sa.String(20), default='DD/MM/YYYY'),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_country_configs_code', 'country_configs', ['code'], unique=True)
    op.create_index('ix_country_configs_is_active', 'country_configs', ['is_active'], unique=False)

    op.create_table(
        'country_cities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('country_code', sa.String(10), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('region', sa.String(200), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('population', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code']),
    )
    op.create_index('ix_country_cities_country', 'country_cities', ['country_code'], unique=False)


def downgrade():
    op.drop_index('ix_country_cities_country', table_name='country_cities')
    op.drop_table('country_cities')
    op.drop_index('ix_country_configs_is_active', table_name='country_configs')
    op.drop_index('ix_country_configs_code', table_name='country_configs')
    op.drop_table('country_configs')
