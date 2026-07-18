"""merge_feature_heads

Revision ID: h7i8j9k0l1m2
Revises: b1c2d3e4f5a6, e1f2a3b4c5d6, g1h2i3j4k5l6
Create Date: 2026-03-26 09:50:00.000000

Collapses the parallel feature heads into a single canonical head so
runtime bootstrap and local Alembic upgrades always apply the email A/B
campaign columns together with the other March feature migrations.
"""
from typing import Sequence, Union


revision: str = "h7i8j9k0l1m2"
down_revision: Union[str, Sequence[str], None] = (
    "b1c2d3e4f5a6",
    "e1f2a3b4c5d6",
    "g1h2i3j4k5l6",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

