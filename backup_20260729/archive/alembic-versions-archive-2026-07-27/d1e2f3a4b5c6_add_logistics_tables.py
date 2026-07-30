"""Add logistics tables: shipping_carriers, shipping_zones, shipments

Revision ID: d1e2f3a4b5c6
Revises: c9d2e3f4a5b6
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa

revision = 'd1e2f3a4b5c6'
down_revision = "c9d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shipping_carriers",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("tracking_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "shipping_zones",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("countries", sa.Text(), nullable=False),
        sa.Column("carrier_id", sa.Integer(), sa.ForeignKey("shipping_carriers.id"), nullable=True),
        sa.Column("carrier_name", sa.String(100), nullable=True),
        sa.Column("base_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_per_kg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("free_shipping_above", sa.Float(), nullable=True),
        sa.Column("estimated_days_min", sa.Integer(), nullable=True),
        sa.Column("estimated_days_max", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_shipping_zones_supplier_active", "shipping_zones", ["supplier_id", "is_active"])

    op.create_table(
        "shipments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False, index=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("carrier_id", sa.Integer(), sa.ForeignKey("shipping_carriers.id"), nullable=True),
        sa.Column("carrier_name", sa.String(100), nullable=True),
        sa.Column("tracking_number", sa.String(200), nullable=True, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("shipped_at", sa.DateTime(), nullable=True),
        sa.Column("estimated_delivery", sa.DateTime(), nullable=True),
        sa.Column("actual_delivery", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_shipments_supplier_status", "shipments", ["supplier_id", "status"])
    op.create_index("ix_shipments_order_supplier", "shipments", ["order_id", "supplier_id"])

    # Seed default global carriers
    op.execute("""
        INSERT INTO shipping_carriers (supplier_id, name, code, tracking_url, is_active, created_at)
        VALUES
            (NULL, 'DHL Express',    'dhl',      'https://www.dhl.com/en/express/tracking.html?AWB={number}', TRUE, CURRENT_TIMESTAMP),
            (NULL, 'FedEx',          'fedex',    'https://www.fedex.com/fedextrack/?trknbr={number}', TRUE, CURRENT_TIMESTAMP),
            (NULL, 'Aramex',         'aramex',   'https://www.aramex.com/track/{number}', TRUE, CURRENT_TIMESTAMP),
            (NULL, 'UPS',            'ups',      'https://www.ups.com/track?tracknum={number}', TRUE, CURRENT_TIMESTAMP),
            (NULL, 'Emirates Post',  'empost',   'https://epg.ae/tracking/{number}', TRUE, CURRENT_TIMESTAMP),
            (NULL, 'Other',          'other',    NULL, TRUE, CURRENT_TIMESTAMP)
    """)


def downgrade() -> None:
    op.drop_index("ix_shipments_order_supplier", "shipments")
    op.drop_index("ix_shipments_supplier_status", "shipments")
    op.drop_table("shipments")
    op.drop_index("ix_shipping_zones_supplier_active", "shipping_zones")
    op.drop_table("shipping_zones")
    op.drop_table("shipping_carriers")

