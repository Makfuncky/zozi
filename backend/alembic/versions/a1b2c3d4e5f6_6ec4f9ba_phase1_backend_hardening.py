"""phase1_backend_hardening

Adds the following to the schema:
  - addresses table (normalised address book per user)
  - coupon_usages table (per-user coupon usage tracking)
  - flash_sales table (time-limited discount campaigns)
  - processed_webhook_events table (idempotency log for Stripe/Tap webhooks)
  - UniqueConstraint uq_wishlist_user_product on wishlists(user_id, product_id)

Revision ID: a1b2c3d4e5f6
Revises: f2c3d4e5f6a7
Create Date: 2026-03-07 01:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(col['name'] == column_name for col in inspector.get_columns(table_name))


def _index_exists(inspector, table_name: str, index_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(idx['name'] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # ── addresses ─────────────────────────────────────────────────────────────
    if not _table_exists(inspector, 'addresses'):
        op.create_table(
            'addresses',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('label', sa.String(), nullable=True, server_default='Home'),
            sa.Column('street', sa.String(), nullable=False),
            sa.Column('city', sa.String(), nullable=False),
            sa.Column('state', sa.String(), nullable=True),
            sa.Column('postal_code', sa.String(), nullable=True),
            sa.Column('country', sa.String(), nullable=True, server_default='AE'),
            sa.Column('is_default', sa.Boolean(), nullable=True, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_addresses_user_id', 'addresses', ['user_id'])

    # ── coupon_usages ─────────────────────────────────────────────────────────
    if not _table_exists(inspector, 'coupon_usages'):
        op.create_table(
            'coupon_usages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('coupon_id', sa.Integer(), sa.ForeignKey('coupons.id'), nullable=True),
            sa.Column('used_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'coupon_id', name='uq_coupon_usage_user_coupon'),
        )
        op.create_index('ix_coupon_usages_user_id', 'coupon_usages', ['user_id'])
        op.create_index('ix_coupon_usages_coupon_id', 'coupon_usages', ['coupon_id'])

    # ── flash_sales ───────────────────────────────────────────────────────────
    if not _table_exists(inspector, 'flash_sales'):
        op.create_table(
            'flash_sales',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('discount_pct', sa.Float(), nullable=False),
            sa.Column('starts_at', sa.DateTime(), nullable=False),
            sa.Column('ends_at', sa.DateTime(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true()),
            sa.Column('product_ids', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )

    # ── processed_webhook_events ──────────────────────────────────────────────
    if not _table_exists(inspector, 'processed_webhook_events'):
        op.create_table(
            'processed_webhook_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.String(), nullable=False),
            sa.Column('processor', sa.String(), nullable=False),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_processed_webhook_events_event_id', 'processed_webhook_events', ['event_id'])
        op.create_index('ix_processed_webhook_processor_event', 'processed_webhook_events', ['processor', 'event_id'])

    # ── wishlists UniqueConstraint ────────────────────────────────────────────
    # SQLite does not support ADD CONSTRAINT directly; use batch_alter_table
    if _table_exists(inspector, 'wishlists'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('wishlists') if idx['name']}
        if 'uq_wishlist_user_product' not in existing_indexes:
            with op.batch_alter_table('wishlists', schema=None) as batch_op:
                batch_op.create_unique_constraint(
                    'uq_wishlist_user_product', ['user_id', 'product_id']
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # Remove wishlist unique constraint
    if _table_exists(inspector, 'wishlists'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('wishlists') if idx['name']}
        if 'uq_wishlist_user_product' in existing_indexes:
            with op.batch_alter_table('wishlists', schema=None) as batch_op:
                batch_op.drop_constraint('uq_wishlist_user_product', type_='unique')

    # Drop tables in reverse order
    for table in ('processed_webhook_events', 'flash_sales', 'coupon_usages', 'addresses'):
        if _table_exists(inspector, table):
            op.drop_table(table)
