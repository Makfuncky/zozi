"""merge divergent heads

Revision ID: f88d0dc00ece
Revises: 20260831_0006, 20260822_pluralize_supplier_table_names, 2026_09_04_0001
Create Date: 2026-09-04 17:00:34.189532+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f88d0dc00ece'
down_revision: Union[str, None] = ('20260831_0006', '20260822_pluralize_supplier_table_names', '2026_09_04_0001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
