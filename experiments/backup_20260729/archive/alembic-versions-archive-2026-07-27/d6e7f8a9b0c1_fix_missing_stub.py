"""fix_missing_stub (recovered no-op stub for deleted migration)

Revision ID: d6e7f8a9b0c1
Revises: 5ca199ab0c03
Create Date: 2026-04-05 00:00:00.000000

"""

from typing import Sequence, Union

revision: str = "d6e7f8a9b0c1"
down_revision: Union[str, Sequence[str], None] = "5ca199ab0c03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

