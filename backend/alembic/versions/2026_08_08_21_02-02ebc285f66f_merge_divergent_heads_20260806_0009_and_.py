"""merge divergent heads 20260806_0009 and 20260808_0001

Revision ID: 02ebc285f66f
Revises: 20260806_0009, 20260808_0001
Create Date: 2026-08-08 21:02:06.273990+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02ebc285f66f'
down_revision: Union[str, None] = ('20260806_0009', '20260808_0001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
