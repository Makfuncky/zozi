"""Add RLS policies and country management tables

Revision ID: a1b2c3d4e5f7
Revises: m5n6o7p8q9r0
Create Date: 2026-06-24 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f7'
down_revision = 'm5n6o7p8q9r0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('country_staff_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('country_code', sa.String(length=10), nullable=False),
        sa.Column('role', sa.Enum('country_head', 'country_manager', name='country_role_enum'), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('status', sa.Boolean(), default=True),
        sa.Column('assigned_at', sa.DateTime(), default=sa.func.utcnow()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'country_code', 'role', name='uq_user_country_role')
    )
    
    op.create_index('ix_country_staff_assignments_user', 'country_staff_assignments', ['user_id'])
    op.create_index('ix_country_staff_assignments_country', 'country_staff_assignments', ['country_code'])
    
    op.create_table('country_config_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('country_code', sa.String(length=10), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('draft', 'approved', 'published', 'rolled_back', name='version_status_enum'), default='draft'),
        sa.Column('config_snapshot_json', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.utcnow()),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code']),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('country_communications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('country_code', sa.String(length=10), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('recipient_role', sa.Enum('country_head', 'country_manager', 'admin', name='recipient_role_enum'), nullable=False),
        sa.Column('recipient_user_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'urgent', name='priority_enum'), default='normal'),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('related_entity_type', sa.String(), nullable=True),
        sa.Column('related_entity_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('attachments_json', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code']),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('cross_country_customer_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('home_country_code', sa.String(length=10), nullable=False),
        sa.Column('operating_country_code', sa.String(length=10), nullable=False),
        sa.Column('currency_used', sa.String(length=10), nullable=False),
        sa.Column('applied_tax_rate', sa.Float(), nullable=False),
        sa.Column('available_payment_methods_json', sa.JSON(), nullable=True),
        sa.Column('available_logistics_json', sa.JSON(), nullable=True),
        sa.Column('session_started_at', sa.DateTime(), default=sa.func.utcnow()),
        sa.ForeignKeyConstraint(['home_country_code'], ['country_configs.code']),
        sa.ForeignKeyConstraint(['operating_country_code'], ['country_configs.code']),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('country_feature_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('country_code', sa.String(length=10), nullable=False),
        sa.Column('feature_key', sa.String(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('country_code', 'feature_key')
    )
    
    op.add_column('country_configs', sa.Column('active_version_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_country_configs_active_version', 'country_configs', 'country_config_versions', ['active_version_id'], ['id'])
    
    connection = op.get_bind()
    if connection.dialect.name == 'postgresql':
        op.execute(text("""
            CREATE POLICY country_isolation_policy ON country_configs
            FOR ALL TO country_manager
            USING (code = ANY(SELECT country_code FROM country_staff_assignments WHERE user_id = current_setting('app.user_id')::integer AND is_active = true));
        """))


def downgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute(text("DROP POLICY IF EXISTS country_isolation_policy ON country_configs"))
    
    op.drop_constraint('fk_country_configs_active_version', 'country_configs')
    op.drop_column('country_configs', 'active_version_id')
    op.drop_table('country_feature_flags')
    op.drop_table('cross_country_customer_records')
    op.drop_table('country_communications')
    op.drop_table('country_config_versions')
    op.drop_table('country_staff_assignments')
