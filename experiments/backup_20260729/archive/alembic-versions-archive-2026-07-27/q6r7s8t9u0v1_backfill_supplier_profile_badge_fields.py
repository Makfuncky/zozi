"""backfill_supplier_profile_badge_fields

Revision ID: q6r7s8t9u0v1
Revises: p4q5r6s7t8u9
Create Date: 2026-03-28 22:10:00.000000

The supplier_profiles table was created on a sibling branch before the phase10
credibility/badge columns existed, so clean SQLite rebuilds reached head with a
table that still missed those fields. Add them here idempotently.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "q6r7s8t9u0v1"
down_revision: Union[str, Sequence[str], None] = "p4q5r6s7t8u9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SUPPLIER_PROFILE_COLUMNS: list[tuple[str, sa.Column]] = [
    ("credibility_score", sa.Column("credibility_score", sa.Integer(), nullable=True)),
    ("badge_level", sa.Column("badge_level", sa.String(length=20), nullable=True)),
    ("badge_granted_at", sa.Column("badge_granted_at", sa.DateTime(), nullable=True)),
    ("verified_documents", sa.Column("verified_documents", sa.Text(), nullable=True)),
    ("document_expires_at", sa.Column("document_expires_at", sa.DateTime(), nullable=True)),
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "supplier_profiles" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("supplier_profiles")}
    pending_columns = [(name, column) for name, column in SUPPLIER_PROFILE_COLUMNS if name not in existing_columns]
    if not pending_columns:
        return

    with op.batch_alter_table("supplier_profiles", schema=None) as batch_op:
        for _, column in pending_columns:
            batch_op.add_column(column)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "supplier_profiles" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("supplier_profiles")}
    removable_columns = [name for name, _ in SUPPLIER_PROFILE_COLUMNS if name in existing_columns]
    if not removable_columns:
        return

    with op.batch_alter_table("supplier_profiles", schema=None) as batch_op:
        for name in reversed(removable_columns):
            batch_op.drop_column(name)

