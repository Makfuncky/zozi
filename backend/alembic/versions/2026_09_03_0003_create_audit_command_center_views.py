"""Create audit.command_center_views table (Alembic single-source-of-truth).

The model lives in ``domains/audit/models/audit_schema_models.py`` but the
table was never formalised in an Alembic migration, so prod NEON instances
rely on ``Base.metadata.create_all`` at boot — a Law 6/56 violation. This
migration makes the table explicit and applies schema discipline (Law 23/52).

Revision ID: 2026_09_03_0003
Revises: 2026_09_03_0002
Create Date: 2026-09-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2026_09_03_0003"
down_revision: Union[str, None] = "2026_09_03_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "command_center_views" in inspector.get_table_names(schema="audit"):
        return

    op.create_table(
        "command_center_views",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "uuid",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("accounts.users.id", ondelete="SET NULL"),
            nullable=False,
            index=True,
        ),
        sa.Column("view_name", sa.String(length=100), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "country_code",
            sa.String(length=2),
            sa.ForeignKey("country.country_configs.code", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        schema="audit",
    )

    op.create_index(
        "ix_command_center_user_default",
        "command_center_views",
        ["user_id", "is_default"],
        schema="audit",
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "command_center_views" not in inspector.get_table_names(schema="audit"):
        return
    op.drop_index(
        "ix_command_center_user_default",
        table_name="command_center_views",
        schema="audit",
        if_exists=True,
    )
    op.drop_table("command_center_views", schema="audit")
