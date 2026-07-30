"""add feed and campaign indexes

Revision ID: v2w3x4y5z6a7
Revises: h7i8j9k0l1m2, u1v2w3x4y5z6
Create Date: 2026-03-30 10:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "v2w3x4y5z6a7"
down_revision: Union[str, Sequence[str], None] = ("h7i8j9k0l1m2", "u1v2w3x4y5z6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = {
        "products": {index["name"] for index in inspector.get_indexes("products")},
        "categories": {index["name"] for index in inspector.get_indexes("categories")},
        "flash_sales": {index["name"] for index in inspector.get_indexes("flash_sales")},
        "email_campaigns": {index["name"] for index in inspector.get_indexes("email_campaigns")},
        "campaign_recipients": {index["name"] for index in inspector.get_indexes("campaign_recipients")},
        "banners": {index["name"] for index in inspector.get_indexes("banners")},
    }

    if "ix_products_public_visibility_created" not in existing_indexes["products"]:
        op.create_index(
            "ix_products_public_visibility_created",
            "products",
            ["is_deleted", "is_active", "is_approved", "created_at"],
            unique=False,
        )
    if "ix_products_public_visibility_sales" not in existing_indexes["products"]:
        op.create_index(
            "ix_products_public_visibility_sales",
            "products",
            ["is_deleted", "is_active", "is_approved", "sales_count"],
            unique=False,
        )
    if "ix_products_public_visibility_rating" not in existing_indexes["products"]:
        op.create_index(
            "ix_products_public_visibility_rating",
            "products",
            ["is_deleted", "is_active", "is_approved", "rating"],
            unique=False,
        )
    if "ix_categories_active_parent_sort_name" not in existing_indexes["categories"]:
        op.create_index(
            "ix_categories_active_parent_sort_name",
            "categories",
            ["is_active", "parent_id", "sort_order", "name"],
            unique=False,
        )
    if "ix_flash_sales_active_window" not in existing_indexes["flash_sales"]:
        op.create_index(
            "ix_flash_sales_active_window",
            "flash_sales",
            ["is_active", "ends_at", "starts_at"],
            unique=False,
        )
    if "ix_email_campaigns_status_send_at" not in existing_indexes["email_campaigns"]:
        op.create_index(
            "ix_email_campaigns_status_send_at",
            "email_campaigns",
            ["status", "send_at"],
            unique=False,
        )
    if "ix_email_campaigns_created_at" not in existing_indexes["email_campaigns"]:
        op.create_index(
            "ix_email_campaigns_created_at",
            "email_campaigns",
            ["created_at"],
            unique=False,
        )
    if "ix_campaign_recipients_campaign_status" not in existing_indexes["campaign_recipients"]:
        op.create_index(
            "ix_campaign_recipients_campaign_status",
            "campaign_recipients",
            ["campaign_id", "status"],
            unique=False,
        )
    if "ix_banners_public_feed" not in existing_indexes["banners"]:
        op.create_index(
            "ix_banners_public_feed",
            "banners",
            ["is_active", "banner_type", "sort_order", "starts_at", "ends_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = {
        "products": {index["name"] for index in inspector.get_indexes("products")},
        "categories": {index["name"] for index in inspector.get_indexes("categories")},
        "flash_sales": {index["name"] for index in inspector.get_indexes("flash_sales")},
        "email_campaigns": {index["name"] for index in inspector.get_indexes("email_campaigns")},
        "campaign_recipients": {index["name"] for index in inspector.get_indexes("campaign_recipients")},
        "banners": {index["name"] for index in inspector.get_indexes("banners")},
    }

    if "ix_banners_public_feed" in existing_indexes["banners"]:
        op.drop_index("ix_banners_public_feed", table_name="banners")
    if "ix_campaign_recipients_campaign_status" in existing_indexes["campaign_recipients"]:
        op.drop_index("ix_campaign_recipients_campaign_status", table_name="campaign_recipients")
    if "ix_email_campaigns_created_at" in existing_indexes["email_campaigns"]:
        op.drop_index("ix_email_campaigns_created_at", table_name="email_campaigns")
    if "ix_email_campaigns_status_send_at" in existing_indexes["email_campaigns"]:
        op.drop_index("ix_email_campaigns_status_send_at", table_name="email_campaigns")
    if "ix_flash_sales_active_window" in existing_indexes["flash_sales"]:
        op.drop_index("ix_flash_sales_active_window", table_name="flash_sales")
    if "ix_categories_active_parent_sort_name" in existing_indexes["categories"]:
        op.drop_index("ix_categories_active_parent_sort_name", table_name="categories")
    if "ix_products_public_visibility_rating" in existing_indexes["products"]:
        op.drop_index("ix_products_public_visibility_rating", table_name="products")
    if "ix_products_public_visibility_sales" in existing_indexes["products"]:
        op.drop_index("ix_products_public_visibility_sales", table_name="products")
    if "ix_products_public_visibility_created" in existing_indexes["products"]:
        op.drop_index("ix_products_public_visibility_created", table_name="products")

