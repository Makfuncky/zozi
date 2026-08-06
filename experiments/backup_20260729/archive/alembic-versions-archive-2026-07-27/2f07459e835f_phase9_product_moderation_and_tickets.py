"""phase9_product_moderation_and_tickets

Revision ID: 2f07459e835f
Revises: 1abf0fe5acce
Create Date: 2026-03-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = '2f07459e835f'
down_revision: Union[str, Sequence[str], None] = '1abf0fe5acce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(inspector, table: str) -> set[str]:
    return {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "support_tickets" not in tables:
        op.create_table(
            'support_tickets',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('subject', sa.String(200), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('status', sa.String(), nullable=True, server_default='open'),
            sa.Column('priority', sa.String(), nullable=True, server_default='normal'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_support_tickets_id', 'support_tickets', ['id'])
        op.create_index('ix_support_tickets_user_id', 'support_tickets', ['user_id'])

    if "ticket_replies" not in tables:
        op.create_table(
            'ticket_replies',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('support_tickets.id'), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('is_admin', sa.Boolean(), nullable=True, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_ticket_replies_id', 'ticket_replies', ['id'])
        op.create_index('ix_ticket_replies_ticket_id', 'ticket_replies', ['ticket_id'])

    if "products" in tables:
        cols = _column_names(inspector, 'products')
        with op.batch_alter_table('products', schema=None) as batch_op:
            if 'is_approved' not in cols:
                batch_op.add_column(sa.Column('is_approved', sa.Boolean(), nullable=True, server_default=sa.true()))
            if 'moderation_status' not in cols:
                batch_op.add_column(sa.Column('moderation_status', sa.String(40), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "ticket_replies" in tables:
        op.drop_table('ticket_replies')

    if "support_tickets" in tables:
        op.drop_table('support_tickets')

    if "products" in tables:
        cols = _column_names(inspector, 'products')
        with op.batch_alter_table('products', schema=None) as batch_op:
            if 'moderation_status' in cols:
                batch_op.drop_column('moderation_status')
            if 'is_approved' in cols:
                batch_op.drop_column('is_approved')

