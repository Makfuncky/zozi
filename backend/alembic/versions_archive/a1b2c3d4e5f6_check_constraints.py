"""Add CHECK constraints and GIN indexes for financial/payment tables

Revision ID: a1b2c3d4e5f6
Revises: a268796caed2
Create Date: 2026-06-29 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = 'a1b2c3d4e5f6'
down_revision = 's_a1b2c3d4e5f6'
branch_labels = None
depends_on = None
def upgrade() -> None:
    # Check if we're using PostgreSQL to create check constraints
    # SQLite doesn't support check constraints in the same way, skip for SQLite
    if hasattr(op, 'get_context') and op.get_context().dialect.supports_check_constraints:
        # TransactionLedger constraints (PostgreSQL)
        op.create_check_constraint(
            'chk_transaction_ledger_amount_non_negative',
            'transaction_ledgers',
            sa.text('amount >= 0')
        )
        op.create_check_constraint(
            'chk_transaction_ledger_currency_valid',
            'transaction_ledgers',
            sa.text("currency IN ('USD', 'EUR', 'GBP', 'AED', 'OMR', 'KWD', 'BHD', 'QAR', 'SAR', 'JOD')")
        )
        
        # SupplierSettlement constraints
        op.create_check_constraint(
            'chk_supplier_settlement_gross_non_negative',
            'supplier_settlements',
            sa.text('gross_amount >= 0')
        )
        op.create_check_constraint(
            'chk_supplier_settlement_commission_non_negative',
            'supplier_settlements',
            sa.text('commission_amount >= 0')
        )
        op.create_check_constraint(
            'chk_supplier_settlement_net_non_negative',
            'supplier_settlements',
            sa.text('net_amount >= 0')
        )
        
        # JournalEntryLine constraints
        op.create_check_constraint(
            'chk_jel_amount_non_negative',
            'journal_entry_lines',
            sa.text('amount >= 0')
        )
        op.create_check_constraint(
            'chk_jel_side_valid',
            'journal_entry_lines',
            sa.text("side IN ('debit', 'credit')")
        )
        
        # Account constraints
        op.create_check_constraint(
            'chk_account_normal_side_valid',
            'accounts',
            sa.text("normal_side IN ('debit', 'credit')")
        )
        
        # Payment constraints
        op.create_check_constraint(
            'chk_payment_amount_non_negative',
            'payments',
            sa.text('amount >= 0')
        )
        op.create_check_constraint(
            'chk_payment_status_valid',
            'payments',
            sa.text("status IN ('pending', 'completed', 'failed', 'refunded')")
        )
        
        # SupplierProfile constraints
        op.create_check_constraint(
            'chk_supplier_verification_status_valid',
            'supplier_profiles',
            sa.text("verification_status IN ('pending', 'documents_submitted', 'under_review', 'approved', 'rejected')")
        )
        op.create_check_constraint(
            'chk_supplier_business_type_valid',
            'supplier_profiles',
            sa.text("business_type IN ('retailer', 'wholesaler', 'manufacturer', 'distributor', 'service_provider')")
        )
    else:
        # SQLite: Skip check constraints, just log a warning or skip
        op.execute("SELECT 1")  # No-op for SQLite
    
    # GIN indexes for JSONB columns
    try:
        # PaymentGatewayConnections
        op.create_index('idx_pgc_credentials_gin', 'payment_gateway_connections', ['credentials'], postgresql_using='gin')
        # SupplierAccounts
        op.create_index('idx_sa_data_gin', 'supplier_accounts', ['account_data'], postgresql_using='gin')
        # SupplierLedgers
        op.create_index('idx_sl_data_gin', 'supplier_ledgers', ['ledger_data'], postgresql_using='gin')
        # CommissionStatements
        op.create_index('idx_cs_data_gin', 'commission_statements', ['commission_data'], postgresql_using='gin')
        # SupplierSettlements
        op.create_index('idx_ss_data_gin', 'supplier_settlements', ['settlement_data'], postgresql_using='gin')
        # TransactionLedgers
        op.create_index('idx_tl_data_gin', 'transaction_ledgers', ['ledger_data'], postgresql_using='gin')
    except Exception:
        # If GIN indexes fail, continue without them
        pass
def downgrade() -> None:
    # Drop check constraints
    if hasattr(op, 'get_context') and op.get_context().dialect.supports_check_constraints:
        for constraint in [
            'chk_transaction_ledger_amount_non_negative',
            'chk_transaction_ledger_currency_valid',
            'chk_supplier_settlement_gross_non_negative',
            'chk_supplier_settlement_commission_non_negative',
            'chk_supplier_settlement_net_non_negative',
            'chk_jel_amount_non_negative',
            'chk_jel_side_valid',
            'chk_account_normal_side_valid',
            'chk_payment_amount_non_negative',
            'chk_payment_status_valid',
            'chk_supplier_verification_status_valid',
            'chk_supplier_business_type_valid',
        ]:
            try:
                op.drop_constraint(constraint, None, type_='check')
            except Exception:
                pass
    
    # Drop GIN indexes
    for index_name in [
        'idx_pgc_credentials_gin',
        'idx_sa_data_gin',
        'idx_sl_data_gin',
        'idx_cs_data_gin',
        'idx_ss_data_gin',
        'idx_tl_data_gin',
    ]:
        try:
            op.drop_index(index_name, table_name=None)
        except Exception:
            pass

# Note: This migration uses conditional execution for SQLite compatibility:
