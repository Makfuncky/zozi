"""merge_runtime_bootstrap_heads

Revision ID: z0y1x2w3v4u5
Revises: 97126a91bc8e, b0c1d2e3f4a5, e3f4a5b6c7d8, h1j2k3l4m5n6, s1t2u3v4w5x6
Create Date: 2026-04-21 10:40:00.000000

Normalize repository migration history to a single reachable head used by
runtime bootstrap assertions.
"""

from typing import Sequence, Union


revision: str = "z0y1x2w3v4u5"
down_revision: Union[str, Sequence[str], None] = (
    "97126a91bc8e",
    "b0c1d2e3f4a5",
    "e3f4a5b6c7d8",
    "h1j2k3l4m5n6",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

