"""add_product_variants_and_video

Revision ID: p9q8r7s6t5u4
Revises: h7i8j9k0l1m2
Create Date: 2026-04-07 18:25:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'p9q8r7s6t5u4'
down_revision = "h7i8j9k0l1m2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("video_url", sa.String(length=500), nullable=True))

    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("size", sa.String(length=100), nullable=True),
        sa.Column("color", sa.String(length=100), nullable=True),
        sa.Column("material", sa.String(length=160), nullable=True),
        sa.Column("sku", sa.String(length=120), nullable=True),
        sa.Column("barcode", sa.String(length=160), nullable=True),
        sa.Column("product_code", sa.String(length=120), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("media_url", sa.String(length=500), nullable=True),
        sa.Column("attributes_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("stock >= 0", name="ck_product_variants_stock_nonnegative"),
        sa.CheckConstraint("price IS NULL OR price >= 0", name="ck_product_variants_price_nonnegative"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("barcode", name="uq_product_variants_barcode"),
        sa.UniqueConstraint("product_code", name="uq_product_variants_product_code"),
        sa.UniqueConstraint("sku", name="uq_product_variants_sku"),
    )
    op.create_index("ix_product_variants_product_sort", "product_variants", ["product_id", "sort_order"], unique=False)
    op.create_index("ix_product_variants_product_active", "product_variants", ["product_id", "is_active"], unique=False)
    op.create_index(op.f("ix_product_variants_product_id"), "product_variants", ["product_id"], unique=False)
    op.create_index(op.f("ix_product_variants_sku"), "product_variants", ["sku"], unique=False)
    op.create_index(op.f("ix_product_variants_barcode"), "product_variants", ["barcode"], unique=False)
    op.create_index(op.f("ix_product_variants_product_code"), "product_variants", ["product_code"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_product_variants_product_code"), table_name="product_variants")
    op.drop_index(op.f("ix_product_variants_barcode"), table_name="product_variants")
    op.drop_index(op.f("ix_product_variants_sku"), table_name="product_variants")
    op.drop_index(op.f("ix_product_variants_product_id"), table_name="product_variants")
    op.drop_index("ix_product_variants_product_active", table_name="product_variants")
    op.drop_index("ix_product_variants_product_sort", table_name="product_variants")
    op.drop_table("product_variants")
    op.drop_column("products", "video_url")

