"""Add Employee HCM models for enterprise workforce management"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b2c3d4e5f6g7_add_employee_hcm_models"
down_revision = "a1b2c3d4e5f7_add_audit_log_table"
branch_labels = None
depends_on = None

def upgrade():
    # Employees table
    op.create_table('employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.String(50), nullable=True),
        sa.Column('country_code', sa.String(10), sa.ForeignKey('country_configs.code'), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('national_id', sa.Text(), nullable=True),
        sa.Column('passport_no', sa.Text(), nullable=True),
        sa.Column('passport_expiry', sa.Date(), nullable=True),
        sa.Column('hiring_manager_id', sa.Integer(), nullable=True),
        sa.Column('reports_to_id', sa.Integer(), nullable=True),
        sa.Column('employment_type', sa.String(30), default='full_time'),
        sa.Column('employment_status', sa.String(30), default='active'),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.Column('termination_date', sa.Date(), nullable=True),
        sa.Column('termination_reason', sa.String(255), nullable=True),
        sa.Column('base_salary', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(10), default='OMR'),
        sa.Column('created_at', sa.DateTime(), default=sa.text('now')),
        sa.Column('updated_at', sa.DateTime(), default=sa.text('now')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_employees_country_status', 'employees', ['country_code', 'employment_status'])
    
    # Employee addresses
    op.create_table('employee_addresses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('address_type', sa.String(20), nullable=False),
        sa.Column('address_line1', sa.String(200), nullable=True),
        sa.Column('address_line2', sa.String(200), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('country_code', sa.String(10), sa.ForeignKey('country_configs.code'), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.text('now')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Employee dependents
    op.create_table('employee_dependents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('relationship', sa.String(30), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('document_number', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.text('now')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Employee assets
    op.create_table('employee_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('asset_type', sa.String(50), nullable=False),
        sa.Column('asset_tag', sa.String(100), nullable=True),
        sa.Column('serial_number', sa.String(200), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), default=sa.text('now')),
        sa.Column('returned_at', sa.DateTime(), nullable=True),
        sa.Column('recovery_status', sa.String(30), default='active'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_tag')
    )
    
    # Employee certifications
    op.create_table('employee_certifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('certification_name', sa.String(200), nullable=False),
        sa.Column('issuing_authority', sa.String(200), nullable=True),
        sa.Column('certificate_number', sa.String(200), nullable=True),
        sa.Column('issued_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('renewal_required', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.text('now')),
        sa.Column('updated_at', sa.DateTime(), default=sa.text('now')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Employee leave ledger
    op.create_table('employee_leave_ledger',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('leave_type', sa.String(50), nullable=False),
        sa.Column('accrued_days', sa.Numeric(5, 2), default=0),
        sa.Column('used_days', sa.Numeric(5, 2), default=0),
        sa.Column('carried_forward', sa.Numeric(5, 2), default=0),
        sa.Column('financial_year', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.text('now')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Employee expenses
    op.create_table('employee_expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('expense_type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(10), default='OMR'),
        sa.Column('expense_date', sa.Date(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), default=sa.text('now')),
        sa.Column('status', sa.String(30), default='submitted'),
        sa.Column('receipt_url', sa.String(500), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('employee_expenses')
    op.drop_table('employee_leave_ledger')
    op.drop_table('employee_certifications')
    op.drop_table('employee_assets')
    op.drop_table('employee_dependents')
    op.drop_table('employee_addresses')
    op.drop_table('employees')
