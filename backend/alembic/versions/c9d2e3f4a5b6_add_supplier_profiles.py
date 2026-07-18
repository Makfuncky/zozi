"""add_supplier_profiles

Revision ID: c9d2e3f4a5b6
Revises: 2f07459e835f
Create Date: 2026-03-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = '2f07459e835f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'supplier_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('business_name', sa.String(length=200), nullable=True),
        sa.Column('business_type', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('phone_business', sa.String(length=30), nullable=True),
        sa.Column('website', sa.String(length=300), nullable=True),
        sa.Column('tax_id', sa.String(length=100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('is_terms_accepted', sa.Boolean(), nullable=True),
        sa.Column('terms_version', sa.String(length=20), nullable=True),
        sa.Column('terms_accepted_at', sa.DateTime(), nullable=True),
        sa.Column('verification_status', sa.String(length=30), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_supplier_profiles_id'), 'supplier_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_supplier_profiles_user_id'), 'supplier_profiles', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_supplier_profiles_user_id'), table_name='supplier_profiles')
    op.drop_index(op.f('ix_supplier_profiles_id'), table_name='supplier_profiles')
    op.drop_table('supplier_profiles')

