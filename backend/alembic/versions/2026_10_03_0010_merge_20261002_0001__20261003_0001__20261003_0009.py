"""merge_20261002_0001__20261003_0001__20261003_0009

Three resolver blocks each added an expand-only, additive migration on top of
``20261001_0001`` (the previously single head):

  - ``20261002_0001`` - hr.employee_biometrics / hr.geo_fence_logs audit columns
  - ``20261003_0001`` - logistics entities created_at server_default
  - ``20261003_0009`` - suppliers.supplier_disputes audit columns (FILE 104)

This merge revision reunites the branches into the single head that Law 6
(Alembic is the only schema source of truth) and the migration gate require.
It performs no DDL of its own: every parent is expand-only and they touch
disjoint tables (``hr``, ``logistics``, ``suppliers``), so the merge exists
purely so ``alembic heads`` reports exactly one head.
"""
from __future__ import annotations

from typing import Sequence, Union

revision: str = "20261003_0010"
down_revision: Union[str, Sequence[str], None] = (
    "20261002_0001",
    "20261003_0001",
    "20261003_0009",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: both parents are pure additive migrations on disjoint tables."""


def downgrade() -> None:
    """No-op: nothing is owned by this merge revision."""
