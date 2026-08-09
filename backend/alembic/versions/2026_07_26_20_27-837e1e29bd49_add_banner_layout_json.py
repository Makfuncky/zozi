"""add_banner_layout_json

Revision ID: 837e1e29bd49
Revises: c9e8f7d6a5b4
Create Date: 2026-07-26 20:27:05.469636+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '837e1e29bd49'
down_revision: Union[str, None] = 'c9e8f7d6a5b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add layout_json column to banners table for the canvas editor."""
    op.add_column('banners', sa.Column('layout_json', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove layout_json column from banners table."""
    op.drop_column('banners', 'layout_json')
