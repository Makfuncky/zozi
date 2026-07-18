"""add chatbot query events

Revision ID: t1u2v3w4x5y6
Revises: s9t0u1v2w3x4
Create Date: 2026-03-29 23:58:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "t1u2v3w4x5y6"
down_revision: Union[str, Sequence[str], None] = "s9t0u1v2w3x4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "chatbot_query_events" in inspector.get_table_names():
        return

    op.create_table(
        "chatbot_query_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False, server_default="query"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("normalized_query", sa.String(length=500), nullable=True),
        sa.Column("intent", sa.String(length=100), nullable=True),
        sa.Column("filters_json", sa.Text(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("product_ids_json", sa.Text(), nullable=True),
        sa.Column("clicked_product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("result_count >= 0", name="ck_chatbot_events_result_count_nonnegative"),
    )
    op.create_index("ix_chatbot_events_user_created", "chatbot_query_events", ["user_id", "created_at"], unique=False)
    op.create_index("ix_chatbot_events_session_created", "chatbot_query_events", ["session_id", "created_at"], unique=False)
    op.create_index("ix_chatbot_events_type_created", "chatbot_query_events", ["event_type", "created_at"], unique=False)
    op.create_index("ix_chatbot_events_intent_created", "chatbot_query_events", ["intent", "created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "chatbot_query_events" not in inspector.get_table_names():
        return

    indexes = {index["name"] for index in inspector.get_indexes("chatbot_query_events") if index.get("name")}
    for index_name in [
        "ix_chatbot_events_intent_created",
        "ix_chatbot_events_type_created",
        "ix_chatbot_events_session_created",
        "ix_chatbot_events_user_created",
    ]:
        if index_name in indexes:
            op.drop_index(index_name, table_name="chatbot_query_events")
    op.drop_table("chatbot_query_events")
