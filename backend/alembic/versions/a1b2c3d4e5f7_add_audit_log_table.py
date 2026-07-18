"""Add AuditLog table for immutable audit trails"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f7_add_audit_log_table"
down_revision = "a1b2c3d4e5f6_add_country_code_fields"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('country_code', sa.String(length=10), nullable=True),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False, default='info'),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('request_id', sa.String(length=64), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_event_type_occurred', 'audit_logs', ['event_type', 'occurred_at'])
    op.create_index('ix_audit_logs_actor_occurred', 'audit_logs', ['actor_id', 'occurred_at'])
    op.create_index('ix_audit_logs_resource_occurred', 'audit_logs', ['resource_type', 'resource_id', 'occurred_at'])
    op.create_index('ix_audit_logs_country_occurred', 'audit_logs', ['country_code', 'occurred_at'])

def downgrade():
    op.drop_index('ix_audit_logs_country_occurred', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource_occurred', table_name='audit_logs')
    op.drop_index('ix_audit_logs_actor_occurred', table_name='audit_logs')
    op.drop_index('ix_audit_logs_event_type_occurred', table_name='audit_logs')
    op.drop_table('audit_logs')
