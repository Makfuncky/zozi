"""Add chat_reactions, chat_legal_holds, is_deleted columns for message soft-delete.

Revision ID: ems_chat_enrichment_20260726
Revises: ems_gap_tables_20260725
Create Date: 2026-07-26
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "ems_chat_enrichment_20260726"
down_revision = "ems_gap_tables_20260725"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ──────────────────────────────────────────────────────────────
    # 1. Chat Reactions (emoji reaction to any message)
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "chat_reactions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("message_id", sa.Integer(), nullable=False, index=True),
        sa.Column("message_type", sa.String(30), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("emoji", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_chat_reaction", "chat_reactions", ["message_id", "message_type", "employee_id", "emoji"])
    op.create_index("ix_chat_reaction_msg", "chat_reactions", ["message_id", "message_type"])

    # ──────────────────────────────────────────────────────────────
    # 2. Chat Legal Holds (freeze room against deletion)
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "chat_legal_holds",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("room_type", sa.String(30), nullable=False),
        sa.Column("placed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("placed_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("released_at", sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint("uq_legal_hold_room", "chat_legal_holds", ["room_id", "room_type"])

    # ──────────────────────────────────────────────────────────────
    # 3. Soft-delete columns on chat messages
    # ──────────────────────────────────────────────────────────────
    op.add_column("direct_chat_messages", sa.Column("is_deleted", sa.Boolean(), default=False))
    op.add_column("group_chat_messages", sa.Column("is_deleted", sa.Boolean(), default=False))
    op.add_column("internal_messages", sa.Column("is_deleted", sa.Boolean(), default=False))


def downgrade() -> None:
    op.drop_column("internal_messages", "is_deleted")
    op.drop_column("group_chat_messages", "is_deleted")
    op.drop_column("direct_chat_messages", "is_deleted")
    op.drop_constraint("uq_legal_hold_room", "chat_legal_holds")
    op.drop_table("chat_legal_holds")
    op.drop_constraint("uq_chat_reaction", "chat_reactions")
    op.drop_index("ix_chat_reaction_msg", table_name="chat_reactions")
    op.drop_table("chat_reactions")
