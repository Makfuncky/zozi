"""add_payment_provider_runtime_config

Revision ID: d6e7f8a9b0c1
Revises: c2d3e4f5a6b7
Create Date: 2026-04-05 10:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "d6e7f8a9b0c1"
down_revision: Union[str, Sequence[str], None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    if "payment_provider_configs" not in existing:
        op.create_table(
            "payment_provider_configs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("online_provider", sa.String(length=20), nullable=False, server_default="stripe"),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint(
                "online_provider IN ('stripe', 'tap', 'both')",
                name="ck_payment_provider_configs_online_provider_valid",
            ),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    if "payment_provider_configs" in existing:
        op.drop_table("payment_provider_configs")
