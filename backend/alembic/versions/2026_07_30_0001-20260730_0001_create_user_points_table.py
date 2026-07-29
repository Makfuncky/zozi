"""create_user_points_table

Revision ID: 20260730_0001
Revises: 20260729_2030
Create Date: 2026-07-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260730_0001"
down_revision: Union[str, None] = "20260729_2030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        op.execute("CREATE TABLE IF NOT EXISTS user_points (id INTEGER NOT NULL PRIMARY KEY, user_id INTEGER NOT NULL, balance INTEGER NOT NULL, lifetime_earned INTEGER NOT NULL, lifetime_redeemed INTEGER NOT NULL, loyalty_tier VARCHAR(20) NOT NULL, points_expire_at DATETIME, created_at DATETIME, updated_at DATETIME, CONSTRAINT fk_user_points_user_id FOREIGN KEY(user_id) REFERENCES users (id))")
        op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_user_points_user_id ON user_points (user_id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_user_points_id ON user_points (id)")
    else:
        op.create_table(
            "user_points",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("balance", sa.Integer(), nullable=False),
            sa.Column("lifetime_earned", sa.Integer(), nullable=False),
            sa.Column("lifetime_redeemed", sa.Integer(), nullable=False),
            sa.Column("loyalty_tier", sa.String(length=20), nullable=False),
            sa.Column("points_expire_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_points_user_id"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_user_points_id", "user_points", ["id"], unique=False)
        op.create_index("ix_user_points_user_id", "user_points", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_points_user_id", table_name="user_points")
    op.drop_index("ix_user_points_id", table_name="user_points")
    op.drop_table("user_points")
