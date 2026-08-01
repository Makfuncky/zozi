"""add_financial_ledger_and_treasury

Revision ID: 0bccd868b96e
Revises: a268796caed2
Create Date: 2026-06-22 14:38:27.838252

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0bccd868b96e'
down_revision = 'a268796caed2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # account_groups
    op.create_table('account_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['account_groups.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('code', name='uq_account_groups_code')
    )

    # accounts
    op.create_table('accounts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('normal_side', sa.String(length=10), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint("normal_side IN ('debit', 'credit')", name='ck_accounts_normal_side'),
    sa.ForeignKeyConstraint(['group_id'], ['account_groups.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('code', name='uq_accounts_code')
    )
    with op.batch_alter_table('accounts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_accounts_group_id'), ['group_id'], unique=False)

    # journal_entries
    op.create_table('journal_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('entry_date', sa.DateTime(), nullable=False),
    sa.Column('reference_type', sa.String(length=40), nullable=False),
    sa.Column('reference_id', sa.Integer(), nullable=False),
    sa.Column('reference_number', sa.String(length=100), nullable=True),
    sa.Column('description', sa.String(length=500), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('fx_rate', sa.Numeric(precision=12, scale=6), nullable=True),
    sa.Column('is_reconciled', sa.Boolean(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('journal_entries', schema=None) as batch_op:
        batch_op.create_index('ix_journal_entries_date', ['entry_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_journal_entries_entry_date'), ['entry_date'], unique=False)
        batch_op.create_index('ix_journal_entries_reference', ['reference_type', 'reference_id'], unique=False)

    # account_balances
    op.create_table('account_balances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('balance', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('last_entry_id', sa.Integer(), nullable=True),
    sa.Column('last_entry_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('account_id', 'currency', name='uq_account_balances_account_currency')
    )
    with op.batch_alter_table('account_balances', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_account_balances_account_id'), ['account_id'], unique=False)

    # journal_entry_lines
    op.create_table('journal_entry_lines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('entry_id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('side', sa.String(length=10), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('description', sa.String(length=300), nullable=True),
    sa.Column('entity_type', sa.String(length=40), nullable=True),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.CheckConstraint("side IN ('debit', 'credit')", name='ck_jel_side'),
    sa.CheckConstraint('amount > 0', name='ck_jel_amount_positive'),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
    sa.ForeignKeyConstraint(['entry_id'], ['journal_entries.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('journal_entry_lines', schema=None) as batch_op:
        batch_op.create_index('ix_jel_account', ['account_id'], unique=False)
        batch_op.create_index('ix_jel_entry', ['entry_id'], unique=False)

    # treasury_accounts
    op.create_table('treasury_accounts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=60), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('account_type', sa.String(length=30), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('gl_account_code', sa.String(length=20), nullable=True),
    sa.Column('balance', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint("account_type IN ('cash','reserve','receivable','payable')", name='ck_treasury_accounts_type'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug'),
    sa.UniqueConstraint('slug', name='uq_treasury_accounts_slug')
    )

    # cash_position_snapshots
    op.create_table('cash_position_snapshots',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('snapshot_date', sa.Date(), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('cash_operating', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('cash_gateway_settlement', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('reserve_supplier_payable', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('reserve_logistics_payable', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('reserve_refund', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('reserve_vat', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('reserve_commission', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('receivable_customer', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('total_cash', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('total_reserves', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('free_cash', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('net_working_capital', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('snapshot_date', 'currency', name='uq_cps_date_currency')
    )
    with op.batch_alter_table('cash_position_snapshots', schema=None) as batch_op:
        batch_op.create_index('ix_cps_date', ['snapshot_date'], unique=False)

    # cash_flow_forecasts
    op.create_table('cash_flow_forecasts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('forecast_date', sa.Date(), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('forecast_category', sa.String(length=40), nullable=False),
    sa.Column('forecast_type', sa.String(length=10), nullable=False),
    sa.Column('expected_amount', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('confidence', sa.String(length=20), nullable=False),
    sa.Column('source_entity', sa.String(length=40), nullable=True),
    sa.Column('source_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.String(length=300), nullable=True),
    sa.Column('expected_settlement_date', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('cash_flow_forecasts', schema=None) as batch_op:
        batch_op.create_index('ix_cff_date', ['forecast_date'], unique=False)

    # gateway_settlement_schedules
    op.create_table('gateway_settlement_schedules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('gateway_code', sa.String(length=60), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('transaction_id', sa.String(length=255), nullable=False),
    sa.Column('amount', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('gateway_fee', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('net_amount', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('transaction_date', sa.DateTime(), nullable=False),
    sa.Column('expected_settlement_date', sa.Date(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('settled_at', sa.DateTime(), nullable=True),
    sa.Column('settlement_reference', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('gateway_settlement_schedules', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_gateway_settlement_schedules_order_id'), ['order_id'], unique=False)
        batch_op.create_index('ix_gwss_date', ['expected_settlement_date'], unique=False)

    # treasury_transactions
    op.create_table('treasury_transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('from_account_id', sa.Integer(), nullable=True),
    sa.Column('to_account_id', sa.Integer(), nullable=True),
    sa.Column('journal_entry_id', sa.Integer(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('transaction_type', sa.String(length=40), nullable=False),
    sa.Column('description', sa.String(length=300), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['from_account_id'], ['treasury_accounts.id'], ),
    sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id'], ),
    sa.ForeignKeyConstraint(['to_account_id'], ['treasury_accounts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('treasury_transactions')
    with op.batch_alter_table('gateway_settlement_schedules', schema=None) as batch_op:
        batch_op.drop_index('ix_gwss_date')
        batch_op.drop_index(batch_op.f('ix_gateway_settlement_schedules_order_id'))
    op.drop_table('gateway_settlement_schedules')
    with op.batch_alter_table('cash_flow_forecasts', schema=None) as batch_op:
        batch_op.drop_index('ix_cff_date')
    op.drop_table('cash_flow_forecasts')
    with op.batch_alter_table('cash_position_snapshots', schema=None) as batch_op:
        batch_op.drop_index('ix_cps_date')
    op.drop_table('cash_position_snapshots')
    op.drop_table('treasury_accounts')
    with op.batch_alter_table('journal_entry_lines', schema=None) as batch_op:
        batch_op.drop_index('ix_jel_entry')
        batch_op.drop_index('ix_jel_account')
    op.drop_table('journal_entry_lines')
    with op.batch_alter_table('account_balances', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_account_balances_account_id'))
    op.drop_table('account_balances')
    with op.batch_alter_table('journal_entries', schema=None) as batch_op:
        batch_op.drop_index('ix_journal_entries_reference')
        batch_op.drop_index(batch_op.f('ix_journal_entries_entry_date'))
        batch_op.drop_index('ix_journal_entries_date')
    op.drop_table('journal_entries')
    with op.batch_alter_table('accounts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_accounts_group_id'))
    op.drop_table('accounts')
    op.drop_table('account_groups')

