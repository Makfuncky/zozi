"""Create Employee System tables

Revision ID: c1d2e3f4a5b6
Revises: q1r2s3t4u5v6
Create Date: 2026-06-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from utils.encryption import EncryptedString


revision = 'c1d2e3f4a5b6b'
down_revision = 'q1r2s3t4u5v6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('offices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('country_code', sa.String(10), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_offices_country', 'offices', ['country_code'])

    op.create_table('employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('employee_code', sa.String(40), nullable=True),
        sa.Column('office_id', sa.Integer(), nullable=True),
        sa.Column('department', sa.String(120), nullable=True),
        sa.Column('position', sa.String(120), nullable=True),
        sa.Column('employment_type', sa.String(30), nullable=True),
        sa.Column('employment_status', sa.String(30), nullable=True),
        sa.Column('salary', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(10), nullable=True),
        sa.Column('country_code', sa.String(10), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['office_id'], ['offices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_code')
    )
    op.create_index('ix_employees_country_status', 'employees', ['country_code', 'employment_status'])

    op.create_table('employee_addresses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('address_type', sa.String(20), nullable=False),
        sa.Column('street', sa.String(200), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('country_code', sa.String(10), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('employee_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('related_person_name', sa.String(160), nullable=False),
        sa.Column('relation_type', sa.String(20), nullable=False),
        sa.Column('is_internal_employee', sa.Boolean(), nullable=True),
        sa.Column('internal_employee_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['internal_employee_id'], ['employees.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('employee_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('asset_type', sa.String(50), nullable=False),
        sa.Column('asset_id', sa.String(100), nullable=False),
        sa.Column('serial_no', sa.String(100), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('returned_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('employee_attendance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('scan_in_time', sa.DateTime(), nullable=True),
        sa.Column('scan_out_time', sa.DateTime(), nullable=True),
        sa.Column('scan_type', sa.String(20), nullable=True),
        sa.Column('location_lat', sa.Float(), nullable=True),
        sa.Column('location_long', sa.Float(), nullable=True),
        sa.Column('device_fingerprint', sa.String(255), nullable=True),
        sa.Column('is_anomaly', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attendance_employee_date', 'employee_attendance', ['employee_id', 'date'])

    op.create_table('employee_certifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('cert_type', sa.String(100), nullable=False),
        sa.Column('cert_name', sa.String(200), nullable=False),
        sa.Column('issued_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('employee_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('doc_type', sa.String(50), nullable=False),
        sa.Column('file_url', sa.String(500), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('verified_by', sa.Integer(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('employee_dependents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(160), nullable=False),
        sa.Column('relation', sa.String(50), nullable=False),
        sa.Column('dob', sa.Date(), nullable=True),
        sa.Column('is_insured', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('employee_work_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('task_category', sa.String(100), nullable=True),
        sa.Column('tickets_resolved', sa.Integer(), nullable=True),
        sa.Column('hours_logged', sa.Numeric(5, 2), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('employee_leave_ledger',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('leave_type', sa.String(50), nullable=False),
        sa.Column('total_days', sa.Numeric(5, 2), nullable=True),
        sa.Column('used_days', sa.Numeric(5, 2), nullable=True),
        sa.Column('accrued_days', sa.Numeric(5, 2), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('employee_shift_rosters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('shift_date', sa.Date(), nullable=False),
        sa.Column('shift_name', sa.String(50), nullable=False),
        sa.Column('start_time', sa.String(10), nullable=False),
        sa.Column('end_time', sa.String(10), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('employee_shift_rosters')
    op.drop_table('employee_leave_ledger')
    op.drop_table('employee_work_logs')
    op.drop_table('employee_dependents')
    op.drop_table('employee_documents')
    op.drop_table('employee_certifications')
    op.drop_table('employee_attendance')
    op.drop_table('employee_assets')
    op.drop_table('employee_relations')
    op.drop_table('employee_addresses')
    op.drop_table('employees')
    op.drop_table('offices')
    op.drop_index('ix_employees_country_status', table_name='employees')
    op.drop_index('ix_offices_country', table_name='offices')

