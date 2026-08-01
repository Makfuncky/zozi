"""add_supplier_public_profile_fields

Revision ID: n1o2p3q4r5s6
Revises: m3n4o5p6q7r8
Create Date: 2026-03-28 12:00:00.000000

Adds customer-facing fields to supplier_profiles:
  about_us, logo_url, banner_url, video_url,
  certifications, social_links, established_year
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "n1o2p3q4r5s6"
down_revision: Union[str, Sequence[str], None] = "m3n4o5p6q7r8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_COLS = [
    ("about_us",         sa.Text(),        True),
    ("logo_url",         sa.String(500),   True),
    ("banner_url",       sa.String(500),   True),
    ("video_url",        sa.String(500),   True),
    ("certifications",   sa.Text(),        True),
    ("social_links",     sa.Text(),        True),
    ("established_year", sa.Integer(),     True),
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "supplier_profiles" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("supplier_profiles")}

    with op.batch_alter_table("supplier_profiles", schema=None) as batch_op:
        for col_name, col_type, nullable in _NEW_COLS:
            if col_name not in existing:
                batch_op.add_column(sa.Column(col_name, col_type, nullable=nullable))


def downgrade() -> None:
    with op.batch_alter_table("supplier_profiles", schema=None) as batch_op:
        for col_name, _, _ in reversed(_NEW_COLS):
            batch_op.drop_column(col_name)

