"""merge_variant_runtime_heads

Revision ID: s1t2u3v4w5x6
Revises: q1r2s3t4u5v6, p9q8r7s6t5u4, n9o8p7q6r5s4
Create Date: 2026-04-07 19:10:00.000000

Collapses the active April feature branches into a single canonical head so
local runtime bootstrap and Alembic upgrade head work against SQLite.
"""
from typing import Sequence, Union


revision: str = "s1t2u3v4w5x6"
down_revision: Union[str, Sequence[str], None] = (
    "q1r2s3t4u5v6",
    "p9q8r7s6t5u4",
    "n9o8p7q6r5s4",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

