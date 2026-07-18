"""phase10_push_tokens_revoked_tokens_banner

Revision ID: a3b4c5d6e7f8
Revises: 2f07459e835f
Create Date: 2026-03-24 00:00:00.000000

Adds:
  - push_notification_tokens table (push token registry per user/device)
  - revoked_tokens table (JWT JTI blacklist persisted to DB)
  - banners table (replaces banner.json file-based storage)
  - cart_items.selected_color column (was missing despite UniqueConstraint referencing it)
  - products.category_id FK column (soft migration alongside existing category string)
  - supplier_profiles.credibility_score + badge fields
  - users.browsing_history_json for customer preference tracking
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "2f07459e835f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # ── push_notification_tokens ────────────────────────────────────────────
    if "push_notification_tokens" not in existing_tables:
        op.create_table(
            "push_notification_tokens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token", sa.String(length=512), nullable=False),
            sa.Column("platform", sa.String(length=20), nullable=True),
            sa.Column("device_name", sa.String(length=100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "token", name="uq_push_user_token"),
        )
        with op.batch_alter_table("push_notification_tokens", schema=None) as batch_op:
            batch_op.create_index("ix_push_tokens_user_id", ["user_id"], unique=False)
            batch_op.create_index("ix_push_tokens_token", ["token"], unique=False)

    # ── revoked_tokens ──────────────────────────────────────────────────────
    if "revoked_tokens" not in existing_tables:
        op.create_table(
            "revoked_tokens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("jti", sa.String(length=64), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("jti", name="uq_revoked_jti"),
        )
        with op.batch_alter_table("revoked_tokens", schema=None) as batch_op:
            batch_op.create_index("ix_revoked_tokens_jti", ["jti"], unique=True)
            batch_op.create_index("ix_revoked_tokens_expires_at", ["expires_at"], unique=False)

    # ── banners ─────────────────────────────────────────────────────────────
    if "banners" not in existing_tables:
        op.create_table(
            "banners",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("subtitle", sa.String(length=500), nullable=True),
            sa.Column("image_url", sa.String(length=500), nullable=True),
            sa.Column("cta_label", sa.String(length=100), nullable=True),
            sa.Column("cta_url", sa.String(length=500), nullable=True),
            sa.Column("banner_type", sa.String(length=50), nullable=True, default="hero"),
            sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
            sa.Column("sort_order", sa.Integer(), nullable=True, default=0),
            sa.Column("starts_at", sa.DateTime(), nullable=True),
            sa.Column("ends_at", sa.DateTime(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("banners", schema=None) as batch_op:
            batch_op.create_index("ix_banners_banner_type", ["banner_type"], unique=False)
            batch_op.create_index("ix_banners_is_active", ["is_active"], unique=False)

    # ── cart_items: add missing selected_color column ───────────────────────
    if "cart_items" in existing_tables:
        cart_cols = {c["name"] for c in inspector.get_columns("cart_items")}
    else:
        cart_cols = set()
    if "cart_items" in existing_tables and "selected_color" not in cart_cols:
        with op.batch_alter_table("cart_items", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("selected_color", sa.String(length=50), nullable=True)
            )

    # ── supplier_profiles: credibility badge fields ─────────────────────────
    if "supplier_profiles" in existing_tables:
        sp_cols = {c["name"] for c in inspector.get_columns("supplier_profiles")}
    else:
        sp_cols = set()
    new_sp_cols = {
        "credibility_score": sa.Column("credibility_score", sa.Integer(), nullable=True, default=0),
        "badge_level": sa.Column("badge_level", sa.String(length=20), nullable=True),
        "badge_granted_at": sa.Column("badge_granted_at", sa.DateTime(), nullable=True),
        "verified_documents": sa.Column("verified_documents", sa.Text(), nullable=True),
        "document_expires_at": sa.Column("document_expires_at", sa.DateTime(), nullable=True),
    }
    sp_to_add = {k: v for k, v in new_sp_cols.items() if k not in sp_cols}
    if "supplier_profiles" in existing_tables and sp_to_add:
        with op.batch_alter_table("supplier_profiles", schema=None) as batch_op:
            for col in sp_to_add.values():
                batch_op.add_column(col)

    # ── users: browsing history + preference fields ──────────────────────────
    if "users" in existing_tables:
        user_cols = {c["name"] for c in inspector.get_columns("users")}
    else:
        user_cols = set()
    new_user_cols = {
        "browsing_history_json": sa.Column("browsing_history_json", sa.Text(), nullable=True),
        "preferred_currency": sa.Column("preferred_currency", sa.String(length=10), nullable=True, default="AED"),
        "preferred_country": sa.Column("preferred_country", sa.String(length=10), nullable=True, default="AE"),
    }
    user_to_add = {k: v for k, v in new_user_cols.items() if k not in user_cols}
    if "users" in existing_tables and user_to_add:
        with op.batch_alter_table("users", schema=None) as batch_op:
            for col in user_to_add.values():
                batch_op.add_column(col)


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("preferred_country")
        batch_op.drop_column("preferred_currency")
        batch_op.drop_column("browsing_history_json")

    with op.batch_alter_table("supplier_profiles", schema=None) as batch_op:
        batch_op.drop_column("document_expires_at")
        batch_op.drop_column("verified_documents")
        batch_op.drop_column("badge_granted_at")
        batch_op.drop_column("badge_level")
        batch_op.drop_column("credibility_score")

    with op.batch_alter_table("cart_items", schema=None) as batch_op:
        batch_op.drop_column("selected_color")

    with op.batch_alter_table("banners", schema=None) as batch_op:
        batch_op.drop_index("ix_banners_is_active")
        batch_op.drop_index("ix_banners_banner_type")
    op.drop_table("banners")

    with op.batch_alter_table("revoked_tokens", schema=None) as batch_op:
        batch_op.drop_index("ix_revoked_tokens_expires_at")
        batch_op.drop_index("ix_revoked_tokens_jti")
    op.drop_table("revoked_tokens")

    with op.batch_alter_table("push_notification_tokens", schema=None) as batch_op:
        batch_op.drop_index("ix_push_tokens_token")
        batch_op.drop_index("ix_push_tokens_user_id")
    op.drop_table("push_notification_tokens")

