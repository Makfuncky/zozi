"""merge divergent heads 20260831_0001 and 20260901_workspace

Revision ID: 2026_09_03_0000
Revises: 20260831_0001, 20260901_workspace
Create Date: 2026-09-03 07:34:36.000000+00:00
"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '2026_09_03_0000'
down_revision: Union[str, None] = ('20260831_0001', '20260901_workspace')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass