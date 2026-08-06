"""add_index_product_supplier_id

Revision ID: d3ec18c6ac15
Revises: w3x4y5z6a7b8
Create Date: 2026-03-31 20:16:30.656768

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'd3ec18c6ac15'
down_revision: Union[str, Sequence[str], None] = 'w3x4y5z6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add index on products.supplier_id for faster supplier-based queries."""
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = {index["name"] for index in inspector.get_indexes("products")}

    if "ix_products_supplier_id" in existing_indexes:
        return

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_products_supplier_id'), ['supplier_id'], unique=False)


def downgrade() -> None:
    """Remove products.supplier_id index."""
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = {index["name"] for index in inspector.get_indexes("products")}

    if 'ix_products_supplier_id' not in existing_indexes:
        return

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_products_supplier_id'))

    banner_fks = sa.inspect(op.get_bind()).get_foreign_keys('banners')
    banner_created_by_fk_exists = any(
        fk.get('referred_table') == 'users' and fk.get('constrained_columns') == ['created_by']
        for fk in banner_fks
    )
    if not banner_created_by_fk_exists:
        with op.batch_alter_table('banners', schema=None) as batch_op:
            batch_op.create_foreign_key('fk_banners_created_by_users', 'users', ['created_by'], ['id'])

    with op.batch_alter_table('chatbot_query_events', schema=None) as batch_op:
        batch_op.alter_column('result_count',
               existing_type=sa.INTEGER(),
               nullable=True,
               existing_server_default=sa.text("'0'"))
        batch_op.create_index(batch_op.f('ix_chatbot_query_events_clicked_product_id'), ['clicked_product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_chatbot_query_events_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_chatbot_query_events_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_chatbot_query_events_intent'), ['intent'], unique=False)
        batch_op.create_index(batch_op.f('ix_chatbot_query_events_normalized_query'), ['normalized_query'], unique=False)
        batch_op.create_index(batch_op.f('ix_chatbot_query_events_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_chatbot_query_events_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('email_campaigns', schema=None) as batch_op:
        batch_op.alter_column('ab_test_enabled',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('0'))

    with op.batch_alter_table('logistics_partner_payouts', schema=None) as batch_op:
        batch_op.alter_column('reference',
               existing_type=sa.TEXT(),
               type_=utils.encryption.EncryptedString(length=255),
               existing_nullable=True)
        batch_op.create_index(batch_op.f('ix_logistics_partner_payouts_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_logistics_partner_payouts_partner_id'), ['partner_id'], unique=False)

    with op.batch_alter_table('logistics_partners', schema=None) as batch_op:
        batch_op.alter_column('contact_email',
               existing_type=sa.VARCHAR(length=200),
               type_=utils.encryption.EncryptedString(length=255),
               existing_nullable=True)
        batch_op.alter_column('contact_phone',
               existing_type=sa.VARCHAR(length=50),
               type_=utils.encryption.EncryptedString(length=80),
               existing_nullable=True)

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('customer_phone',
               existing_type=sa.VARCHAR(length=30),
               type_=utils.encryption.EncryptedString(length=60),
               existing_nullable=True)

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_products_supplier_id'), ['supplier_id'], unique=False)

    with op.batch_alter_table('push_notification_tokens', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'])

    with op.batch_alter_table('referral_point_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_referral_point_events_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_referral_point_events_referred_user_id'), ['referred_user_id'], unique=False)

    with op.batch_alter_table('revoked_tokens', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'])

    with op.batch_alter_table('shipment_confirmations', schema=None) as batch_op:
        batch_op.alter_column('current_hub',
               existing_type=sa.TEXT(),
               type_=utils.encryption.EncryptedString(length=200),
               existing_nullable=True)
        batch_op.drop_index(batch_op.f('ix_shipment_confirmations_requested_status'))
        batch_op.create_index(batch_op.f('ix_shipment_confirmations_requester_user_id'), ['requester_user_id'], unique=False)

    with op.batch_alter_table('shipment_events', schema=None) as batch_op:
        batch_op.alter_column('location',
               existing_type=sa.VARCHAR(length=200),
               type_=utils.encryption.EncryptedString(length=255),
               existing_nullable=True)

    with op.batch_alter_table('supplier_profiles', schema=None) as batch_op:
        batch_op.alter_column('postal_code',
               existing_type=sa.VARCHAR(length=20),
               type_=utils.encryption.EncryptedString(length=50),
               existing_nullable=True)
        batch_op.alter_column('phone_business',
               existing_type=sa.VARCHAR(length=30),
               type_=utils.encryption.EncryptedString(length=60),
               existing_nullable=True)
        batch_op.alter_column('tax_id',
               existing_type=sa.VARCHAR(length=100),
               type_=utils.encryption.EncryptedString(length=150),
               existing_nullable=True)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'users', ['referred_by_user_id'], ['id'])

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('supplier_profiles', schema=None) as batch_op:
        batch_op.alter_column('tax_id',
               existing_type=utils.encryption.EncryptedString(length=150),
               type_=sa.VARCHAR(length=100),
               existing_nullable=True)
        batch_op.alter_column('phone_business',
               existing_type=utils.encryption.EncryptedString(length=60),
               type_=sa.VARCHAR(length=30),
               existing_nullable=True)
        batch_op.alter_column('postal_code',
               existing_type=utils.encryption.EncryptedString(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=True)

    with op.batch_alter_table('shipment_events', schema=None) as batch_op:
        batch_op.alter_column('location',
               existing_type=utils.encryption.EncryptedString(length=255),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)

    with op.batch_alter_table('shipment_confirmations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_shipment_confirmations_requester_user_id'))
        batch_op.create_index(batch_op.f('ix_shipment_confirmations_requested_status'), ['requested_status'], unique=False)
        batch_op.alter_column('current_hub',
               existing_type=utils.encryption.EncryptedString(length=200),
               type_=sa.TEXT(),
               existing_nullable=True)

    with op.batch_alter_table('revoked_tokens', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('referral_point_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_referral_point_events_referred_user_id'))
        batch_op.drop_index(batch_op.f('ix_referral_point_events_id'))

    with op.batch_alter_table('push_notification_tokens', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_products_supplier_id'))

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('customer_phone',
               existing_type=utils.encryption.EncryptedString(length=60),
               type_=sa.VARCHAR(length=30),
               existing_nullable=True)

    with op.batch_alter_table('logistics_partners', schema=None) as batch_op:
        batch_op.alter_column('contact_phone',
               existing_type=utils.encryption.EncryptedString(length=80),
               type_=sa.VARCHAR(length=50),
               existing_nullable=True)
        batch_op.alter_column('contact_email',
               existing_type=utils.encryption.EncryptedString(length=255),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)

    with op.batch_alter_table('logistics_partner_payouts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_logistics_partner_payouts_partner_id'))
        batch_op.drop_index(batch_op.f('ix_logistics_partner_payouts_id'))
        batch_op.alter_column('reference',
               existing_type=utils.encryption.EncryptedString(length=255),
               type_=sa.TEXT(),
               existing_nullable=True)

    with op.batch_alter_table('email_campaigns', schema=None) as batch_op:
        batch_op.alter_column('ab_test_enabled',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('0'))

    with op.batch_alter_table('chatbot_query_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_chatbot_query_events_user_id'))
        batch_op.drop_index(batch_op.f('ix_chatbot_query_events_session_id'))
        batch_op.drop_index(batch_op.f('ix_chatbot_query_events_normalized_query'))
        batch_op.drop_index(batch_op.f('ix_chatbot_query_events_intent'))
        batch_op.drop_index(batch_op.f('ix_chatbot_query_events_id'))
        batch_op.drop_index(batch_op.f('ix_chatbot_query_events_created_at'))
        batch_op.drop_index(batch_op.f('ix_chatbot_query_events_clicked_product_id'))
        batch_op.alter_column('result_count',
               existing_type=sa.INTEGER(),
               nullable=False,
               existing_server_default=sa.text("'0'"))

    with op.batch_alter_table('banners', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['created_by'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('addresses', schema=None) as batch_op:
        batch_op.alter_column('street',
               existing_type=utils.encryption.EncryptedString(),
               type_=sa.VARCHAR(),
               existing_nullable=False)

    # ### end Alembic commands ###

