"""add_cash_management_tables

Revision ID: 79b533c27897
Revises: z9a0b1c2d3e4
Create Date: 2026-04-02 21:20:36.671454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79b533c27897'
down_revision: Union[str, Sequence[str], None] = 'z9a0b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- Cash Management tables ---
    op.create_table('bank_transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('transaction_ref', sa.String(length=200), nullable=False),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('transaction_type', sa.String(length=50), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('linked_order_id', sa.Integer(), nullable=True),
    sa.Column('linked_supplier_id', sa.Integer(), nullable=True),
    sa.Column('linked_logistics_id', sa.Integer(), nullable=True),
    sa.Column('linked_payout_id', sa.Integer(), nullable=True),
    sa.Column('linked_refund_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('reconciled', sa.Boolean(), nullable=False),
    sa.Column('reconciled_at', sa.DateTime(), nullable=True),
    sa.Column('reconciled_by', sa.Integer(), nullable=True),
    sa.Column('flagged', sa.Boolean(), nullable=True),
    sa.Column('flag_reason', sa.Text(), nullable=True),
    sa.Column('transaction_date', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['linked_logistics_id'], ['logistics_partners.id'], ),
    sa.ForeignKeyConstraint(['linked_order_id'], ['orders.id'], ),
    sa.ForeignKeyConstraint(['linked_refund_id'], ['return_requests.id'], ),
    sa.ForeignKeyConstraint(['linked_supplier_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['reconciled_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('bank_transactions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_bank_transactions_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_bank_transactions_linked_order_id'), ['linked_order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_bank_transactions_transaction_ref'), ['transaction_ref'], unique=True)
        batch_op.create_index('ix_bank_txn_date', ['transaction_date'], unique=False)
        batch_op.create_index('ix_bank_txn_reconciled', ['reconciled'], unique=False)
        batch_op.create_index('ix_bank_txn_source_type', ['source', 'transaction_type'], unique=False)

    op.create_table('transaction_ledger',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('order_item_id', sa.Integer(), nullable=True),
    sa.Column('supplier_id', sa.Integer(), nullable=False),
    sa.Column('logistics_partner_id', sa.Integer(), nullable=True),
    sa.Column('shipment_id', sa.Integer(), nullable=True),
    sa.Column('payment_method', sa.String(length=20), nullable=False),
    sa.Column('product_subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('delivery_pickup_charge', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('delivery_dropoff_charge', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('delivery_total', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('vat_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('zozi_commission_rate', sa.Numeric(precision=5, scale=4), nullable=False),
    sa.Column('zozi_commission', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('net_supplier_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('net_logistics_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('net_zozi_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('cod_collected_amount', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('cod_remittance_due', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('settlement_status', sa.String(length=30), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint('product_subtotal >= 0', name='ck_txn_ledger_product_subtotal_nonneg'),
    sa.CheckConstraint('vat_amount >= 0', name='ck_txn_ledger_vat_nonneg'),
    sa.CheckConstraint('zozi_commission >= 0', name='ck_txn_ledger_commission_nonneg'),
    sa.ForeignKeyConstraint(['logistics_partner_id'], ['logistics_partners.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.ForeignKeyConstraint(['order_item_id'], ['order_items.id'], ),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('transaction_ledger', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_transaction_ledger_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_transaction_ledger_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_transaction_ledger_logistics_partner_id'), ['logistics_partner_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_transaction_ledger_order_id'), ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_transaction_ledger_order_item_id'), ['order_item_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_transaction_ledger_shipment_id'), ['shipment_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_transaction_ledger_supplier_id'), ['supplier_id'], unique=False)
        batch_op.create_index('ix_txn_ledger_logistics', ['logistics_partner_id'], unique=False)
        batch_op.create_index('ix_txn_ledger_order', ['order_id'], unique=False)
        batch_op.create_index('ix_txn_ledger_status_created', ['settlement_status', 'created_at'], unique=False)
        batch_op.create_index('ix_txn_ledger_supplier', ['supplier_id'], unique=False)

    op.create_table('logistics_settlements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('partner_id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('ledger_id', sa.Integer(), nullable=True),
    sa.Column('payout_id', sa.Integer(), nullable=True),
    sa.Column('shipment_id', sa.Integer(), nullable=True),
    sa.Column('pickup_charge', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('dropoff_charge', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total_delivery_fee', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('cod_collected', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('cod_remitted', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('cod_retained', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('cod_remittance_status', sa.String(length=30), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('eligible_at', sa.DateTime(), nullable=True),
    sa.Column('settled_at', sa.DateTime(), nullable=True),
    sa.Column('bank_transaction_id', sa.Integer(), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint('dropoff_charge >= 0', name='ck_logistics_settlements_dropoff_nonneg'),
    sa.CheckConstraint('pickup_charge >= 0', name='ck_logistics_settlements_pickup_nonneg'),
    sa.ForeignKeyConstraint(['bank_transaction_id'], ['bank_transactions.id'], ),
    sa.ForeignKeyConstraint(['ledger_id'], ['transaction_ledger.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.ForeignKeyConstraint(['partner_id'], ['logistics_partners.id'], ),
    sa.ForeignKeyConstraint(['payout_id'], ['logistics_partner_payouts.id'], ),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('logistics_settlements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_logistics_settlements_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_logistics_settlements_ledger_id'), ['ledger_id'], unique=False)
        batch_op.create_index('ix_logistics_settlements_order', ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_logistics_settlements_order_id'), ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_logistics_settlements_partner_id'), ['partner_id'], unique=False)
        batch_op.create_index('ix_logistics_settlements_partner_status', ['partner_id', 'status'], unique=False)
        batch_op.create_index(batch_op.f('ix_logistics_settlements_payout_id'), ['payout_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_logistics_settlements_shipment_id'), ['shipment_id'], unique=False)

    op.create_table('refund_ledger',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('return_request_id', sa.Integer(), nullable=True),
    sa.Column('ledger_id', sa.Integer(), nullable=True),
    sa.Column('refund_reason', sa.String(length=100), nullable=False),
    sa.Column('refund_method', sa.String(length=30), nullable=False),
    sa.Column('customer_refund_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('supplier_reversal', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('logistics_reversal', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('commission_reversal', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('vat_adjustment', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('bank_transaction_id', sa.Integer(), nullable=True),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('processed_by', sa.Integer(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['bank_transaction_id'], ['bank_transactions.id'], ),
    sa.ForeignKeyConstraint(['ledger_id'], ['transaction_ledger.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.ForeignKeyConstraint(['processed_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['return_request_id'], ['return_requests.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('refund_ledger', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_refund_ledger_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_refund_ledger_ledger_id'), ['ledger_id'], unique=False)
        batch_op.create_index('ix_refund_ledger_order', ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_refund_ledger_order_id'), ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_refund_ledger_return_request_id'), ['return_request_id'], unique=False)
        batch_op.create_index('ix_refund_ledger_status', ['status'], unique=False)

    op.create_table('supplier_settlements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('supplier_id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('ledger_id', sa.Integer(), nullable=True),
    sa.Column('payout_id', sa.Integer(), nullable=True),
    sa.Column('gross_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('commission_rate', sa.Numeric(precision=5, scale=4), nullable=False),
    sa.Column('commission_deducted', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('vat_on_commission', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('net_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('eligible_at', sa.DateTime(), nullable=True),
    sa.Column('settled_at', sa.DateTime(), nullable=True),
    sa.Column('bank_transaction_id', sa.Integer(), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint('commission_deducted >= 0', name='ck_supplier_settlements_commission_nonneg'),
    sa.CheckConstraint('gross_amount >= 0', name='ck_supplier_settlements_gross_nonneg'),
    sa.CheckConstraint('net_amount >= 0', name='ck_supplier_settlements_net_nonneg'),
    sa.ForeignKeyConstraint(['bank_transaction_id'], ['bank_transactions.id'], ),
    sa.ForeignKeyConstraint(['ledger_id'], ['transaction_ledger.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.ForeignKeyConstraint(['payout_id'], ['payouts.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('supplier_settlements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_supplier_settlements_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supplier_settlements_ledger_id'), ['ledger_id'], unique=False)
        batch_op.create_index('ix_supplier_settlements_order', ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supplier_settlements_order_id'), ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supplier_settlements_payout_id'), ['payout_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supplier_settlements_supplier_id'), ['supplier_id'], unique=False)
        batch_op.create_index('ix_supplier_settlements_supplier_status', ['supplier_id', 'status'], unique=False)

    # --- Add shipping columns to orders ---
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('shipping_city', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('shipping_country', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('shipping_postal_code', sa.String(length=40), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('shipping_postal_code')
        batch_op.drop_column('shipping_country')
        batch_op.drop_column('shipping_city')

    with op.batch_alter_table('supplier_settlements', schema=None) as batch_op:
        batch_op.drop_index('ix_supplier_settlements_supplier_status')
        batch_op.drop_index(batch_op.f('ix_supplier_settlements_supplier_id'))
        batch_op.drop_index(batch_op.f('ix_supplier_settlements_payout_id'))
        batch_op.drop_index(batch_op.f('ix_supplier_settlements_order_id'))
        batch_op.drop_index('ix_supplier_settlements_order')
        batch_op.drop_index(batch_op.f('ix_supplier_settlements_ledger_id'))
        batch_op.drop_index(batch_op.f('ix_supplier_settlements_id'))

    op.drop_table('supplier_settlements')
    with op.batch_alter_table('refund_ledger', schema=None) as batch_op:
        batch_op.drop_index('ix_refund_ledger_status')
        batch_op.drop_index(batch_op.f('ix_refund_ledger_return_request_id'))
        batch_op.drop_index(batch_op.f('ix_refund_ledger_order_id'))
        batch_op.drop_index('ix_refund_ledger_order')
        batch_op.drop_index(batch_op.f('ix_refund_ledger_ledger_id'))
        batch_op.drop_index(batch_op.f('ix_refund_ledger_id'))

    op.drop_table('refund_ledger')
    with op.batch_alter_table('logistics_settlements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_logistics_settlements_shipment_id'))
        batch_op.drop_index(batch_op.f('ix_logistics_settlements_payout_id'))
        batch_op.drop_index('ix_logistics_settlements_partner_status')
        batch_op.drop_index(batch_op.f('ix_logistics_settlements_partner_id'))
        batch_op.drop_index(batch_op.f('ix_logistics_settlements_order_id'))
        batch_op.drop_index('ix_logistics_settlements_order')
        batch_op.drop_index(batch_op.f('ix_logistics_settlements_ledger_id'))
        batch_op.drop_index(batch_op.f('ix_logistics_settlements_id'))

    op.drop_table('logistics_settlements')
    with op.batch_alter_table('transaction_ledger', schema=None) as batch_op:
        batch_op.drop_index('ix_txn_ledger_supplier')
        batch_op.drop_index('ix_txn_ledger_status_created')
        batch_op.drop_index('ix_txn_ledger_order')
        batch_op.drop_index('ix_txn_ledger_logistics')
        batch_op.drop_index(batch_op.f('ix_transaction_ledger_supplier_id'))
        batch_op.drop_index(batch_op.f('ix_transaction_ledger_shipment_id'))
        batch_op.drop_index(batch_op.f('ix_transaction_ledger_order_item_id'))
        batch_op.drop_index(batch_op.f('ix_transaction_ledger_order_id'))
        batch_op.drop_index(batch_op.f('ix_transaction_ledger_logistics_partner_id'))
        batch_op.drop_index(batch_op.f('ix_transaction_ledger_id'))
        batch_op.drop_index(batch_op.f('ix_transaction_ledger_created_at'))

    op.drop_table('transaction_ledger')
    with op.batch_alter_table('bank_transactions', schema=None) as batch_op:
        batch_op.drop_index('ix_bank_txn_source_type')
        batch_op.drop_index('ix_bank_txn_reconciled')
        batch_op.drop_index('ix_bank_txn_date')
        batch_op.drop_index(batch_op.f('ix_bank_transactions_transaction_ref'))
        batch_op.drop_index(batch_op.f('ix_bank_transactions_linked_order_id'))
        batch_op.drop_index(batch_op.f('ix_bank_transactions_id'))

    op.drop_table('bank_transactions')

