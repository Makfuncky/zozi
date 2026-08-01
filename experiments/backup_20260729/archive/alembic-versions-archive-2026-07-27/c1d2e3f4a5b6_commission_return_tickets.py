"""commission_return_tickets

Revision ID: c1d2e3f4a5b6
Revises: x1y2z3a4b5c6
Create Date: 2026-04-06 19:00:00.000000

Adds:
  - products.return_window_days
  - supplier_profiles.max_return_days
  - support_tickets.ticket_category + raised_by_role
  - ticket_attachments table
  - commission_agreements table (supplier-level)
  - product_commission_overrides table (product-level)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "x1y2z3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Product return window ─────────────────────────────────────────────────
    op.add_column("products", sa.Column("return_window_days", sa.Integer(), nullable=True, server_default="10"))

    # ── SupplierProfile max return days ──────────────────────────────────────
    op.add_column("supplier_profiles", sa.Column("max_return_days", sa.Integer(), nullable=True, server_default="30"))

    # ── SupportTicket role disambiguation ────────────────────────────────────
    op.add_column("support_tickets", sa.Column("ticket_category", sa.String(30), nullable=True, server_default="customer"))
    op.add_column("support_tickets", sa.Column("raised_by_role", sa.String(30), nullable=True))
    op.add_column("support_tickets", sa.Column("related_entity_type", sa.String(30), nullable=True))
    op.add_column("support_tickets", sa.Column("related_entity_id", sa.Integer(), nullable=True))
    op.create_index("ix_support_tickets_category_status", "support_tickets", ["ticket_category", "status"])

    # ── Ticket attachments ────────────────────────────────────────────────────
    op.create_table(
        "ticket_attachments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reply_id", sa.Integer(), sa.ForeignKey("ticket_replies.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("uploader_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ticket_attachments_ticket", "ticket_attachments", ["ticket_id"])

    # ── Commission agreements (supplier-level) ────────────────────────────────
    op.create_table(
        "commission_agreements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("rate", sa.Numeric(5, 4), nullable=False),           # e.g. 0.1200 = 12%
        sa.Column("effective_from", sa.DateTime(), nullable=False),
        sa.Column("effective_to", sa.DateTime(), nullable=True),       # NULL = currently active
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("set_by_admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_commission_agreements_supplier_active", "commission_agreements", ["supplier_id", "is_active"])

    # ── Product commission overrides (product-level) ──────────────────────────
    op.create_table(
        "product_commission_overrides",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("rate", sa.Numeric(5, 4), nullable=False),           # e.g. 0.0800 = 8%
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("set_by_admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_product_commission_overrides_supplier", "product_commission_overrides", ["supplier_id"])


def downgrade() -> None:
    op.drop_table("product_commission_overrides")
    op.drop_table("commission_agreements")
    op.drop_table("ticket_attachments")
    op.drop_index("ix_support_tickets_category_status", table_name="support_tickets")
    op.drop_column("support_tickets", "related_entity_id")
    op.drop_column("support_tickets", "related_entity_type")
    op.drop_column("support_tickets", "raised_by_role")
    op.drop_column("support_tickets", "ticket_category")
    op.drop_column("supplier_profiles", "max_return_days")
    op.drop_column("products", "return_window_days")

