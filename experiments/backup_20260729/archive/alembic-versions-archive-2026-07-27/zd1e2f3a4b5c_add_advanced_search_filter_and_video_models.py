"""add_advanced_search_filter_and_video_models

Revision ID: zd1e2f3a4b5c
Revises: zc1d2e3f4a5
Create Date: 2026-06-30 22:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'zd1e2f3a4b5c'
down_revision = 'zc1d2e3f4a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("filter_attributes", sa.JSON(), nullable=True))
    op.add_column("products", sa.Column("search_vector", sa.JSON(), nullable=True))
    op.add_column("products", sa.Column("video_count", sa.Integer(), nullable=False, server_default="0"))

    op.create_table(
        "product_videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("video_url", sa.String(length=500), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("video_type", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("views_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("upload_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_videos_product_id", "product_videos", ["product_id"], unique=False)
    op.create_index("ix_product_videos_featured", "product_videos", ["is_featured"], unique=False)

    op.create_table(
        "video_analytics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("watch_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("device_type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["video_id"], ["product_videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_video_analytics_video_id", "video_analytics", ["video_id"], unique=False)
    op.create_index("ix_video_analytics_user_id", "video_analytics", ["user_id"], unique=False)

    op.create_table(
        "product_filter_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("filter_name", sa.String(length=100), nullable=False),
        sa.Column("filter_type", sa.String(length=50), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_filter_metadata_category_id", "product_filter_metadata", ["category_id"], unique=False)

    op.create_table(
        "product_filter_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filter_metadata_id", sa.Integer(), nullable=False),
        sa.Column("option_value", sa.String(length=255), nullable=False),
        sa.Column("option_display_name", sa.String(length=255), nullable=False),
        sa.Column("product_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["filter_metadata_id"], ["product_filter_metadata.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_filter_options_filter_metadata_id", "product_filter_options", ["filter_metadata_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_product_filter_options_filter_metadata_id", table_name="product_filter_options")
    op.drop_table("product_filter_options")

    op.drop_index("ix_product_filter_metadata_category_id", table_name="product_filter_metadata")
    op.drop_table("product_filter_metadata")

    op.drop_index("ix_video_analytics_user_id", table_name="video_analytics")
    op.drop_index("ix_video_analytics_video_id", table_name="video_analytics")
    op.drop_table("video_analytics")

    op.drop_index("ix_product_videos_featured", table_name="product_videos")
    op.drop_index("ix_product_videos_product_id", table_name="product_videos")
    op.drop_table("product_videos")

    op.drop_column("products", "video_count")
    op.drop_column("products", "search_vector")
    op.drop_column("products", "filter_attributes")

