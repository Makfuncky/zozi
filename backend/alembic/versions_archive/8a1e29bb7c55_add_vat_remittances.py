"""add_vat_remittances

Revision ID: 8a1e29bb7c55
Revises: 5d9f3a1c2b44
Create Date: 2026-04-03 21:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8a1e29bb7c55'
down_revision: Union[str, Sequence[str], None] = '5d9f3a1c2b44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'vat_remittances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('vat_collected_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('vat_adjustment_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('amount_due', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('amount_remitted', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('bank_transaction_id', sa.Integer(), nullable=True),
        sa.Column('remitted_at', sa.DateTime(), nullable=True),
        sa.Column('remitted_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('amount_due >= 0', name='ck_vat_remittances_due_nonnegative'),
        sa.CheckConstraint('amount_remitted >= 0', name='ck_vat_remittances_remitted_nonnegative'),
        sa.CheckConstraint('vat_adjustment_amount >= 0', name='ck_vat_remittances_adjustment_nonnegative'),
        sa.CheckConstraint('vat_collected_amount >= 0', name='ck_vat_remittances_collected_nonnegative'),
        sa.ForeignKeyConstraint(['bank_transaction_id'], ['bank_transactions.id']),
        sa.ForeignKeyConstraint(['remitted_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('vat_remittances', schema=None) as batch_op:
        batch_op.create_index('ix_vat_remittances_period', ['period_start', 'period_end'], unique=False)
        batch_op.create_index('ix_vat_remittances_status', ['status', 'created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_vat_remittances_period_end'), ['period_end'], unique=False)
        batch_op.create_index(batch_op.f('ix_vat_remittances_period_start'), ['period_start'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('vat_remittances', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_vat_remittances_period_start'))
        batch_op.drop_index(batch_op.f('ix_vat_remittances_period_end'))
        batch_op.drop_index('ix_vat_remittances_status')
        batch_op.drop_index('ix_vat_remittances_period')

    op.drop_table('vat_remittances')

