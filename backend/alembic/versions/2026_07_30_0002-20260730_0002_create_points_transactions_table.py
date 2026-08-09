"""create_points_transactions_table

Revision ID: 20260730_0002
Revises: 20260730_0001
Create Date: 2026-07-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260730_0002"
down_revision: Union[str, None] = "20260730_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        op.execute("CREATE TABLE IF NOT EXISTS points_transactions (id INTEGER NOT NULL PRIMARY KEY, user_id INTEGER NOT NULL, points INTEGER NOT NULL, transaction_type VARCHAR(30) NOT NULL, order_id INTEGER, source_description VARCHAR(200), balance_after INTEGER, admin_id INTEGER, created_at DATETIME, CONSTRAINT fk_points_transactions_user_id FOREIGN KEY(user_id) REFERENCES users (id), CONSTRAINT fk_points_transactions_order_id FOREIGN KEY(order_id) REFERENCES orders (id), CONSTRAINT fk_points_transactions_admin_id FOREIGN KEY(admin_id) REFERENCES users (id))")
        op.execute("CREATE INDEX IF NOT EXISTS ix_points_transactions_id ON points_transactions (id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_points_transactions_user_id ON points_transactions (user_id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_points_transactions_order_id ON points_transactions (order_id)")
    else:
        op.create_table(
            "points_transactions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("points", sa.Integer(), nullable=False),
            sa.Column("transaction_type", sa.String(length=30), nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=True),
            sa.Column("source_description", sa.String(length=200), nullable=True),
            sa.Column("balance_after", sa.Integer(), nullable=True),
            sa.Column("admin_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["admin_id"], ["users.id"], name="fk_points_transactions_admin_id"),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name="fk_points_transactions_order_id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_points_transactions_user_id"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_points_transactions_id", "points_transactions", ["id"], unique=False)
        op.create_index("ix_points_transactions_order_id", "points_transactions", ["order_id"], unique=False)
        op.create_index("ix_points_transactions_user_id", "points_transactions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_points_transactions_user_id", table_name="points_transactions")
    op.drop_index("ix_points_transactions_order_id", table_name="points_transactions")
    op.drop_index("ix_points_transactions_id", table_name="points_transactions")
    op.drop_table("points_transactions")
