"""add_banner_appearance_columns

Revision ID: e1f2a3b4c5d6
Revises: d5477adebb01
Create Date: 2026-03-25 00:00:00.000000

Adds 8 admin-controllable appearance columns to the banners table:
  bg_color, text_color, subtitle_color, btn_bg_color, btn_text_color,
  badge_text, badge_color, effect
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d5477adebb01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("banners") as batch_op:
        batch_op.add_column(sa.Column("bg_color", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("text_color", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("subtitle_color", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("btn_bg_color", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("btn_text_color", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("badge_text", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("badge_color", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("effect", sa.String(50), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("banners") as batch_op:
        batch_op.drop_column("effect")
        batch_op.drop_column("badge_color")
        batch_op.drop_column("badge_text")
        batch_op.drop_column("btn_text_color")
        batch_op.drop_column("btn_bg_color")
        batch_op.drop_column("subtitle_color")
        batch_op.drop_column("text_color")
        batch_op.drop_column("bg_color")

