"""Add rollout_percentage to country_feature_flags (additive gradual rollout)

Revision ID: 20260929_0745
Revises: f88d0dc00ece
Create Date: 2026-09-29

Adds country_feature_flags.rollout_percentage (Integer, NOT NULL, server
default 0) so a country feature flag can gate access by percentage rollout.
Additive only: existing rows receive the default 0 (binary membership gating
and rollout_audience are unchanged), so this migration is safe on live data.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


def _is_offline(conn) -> bool:
    if conn is None:
        return True
    try:
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy.exc import NoInspectionAvailable
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


revision: str = "20260929_0745"
down_revision: Union[str, None] = "f88d0dc00ece"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "country_feature_flags"
# The table was created under the ``configuration`` schema (baseline) and later
# moved to ``country`` (2026_08_22_0001); SQLite keeps it schema-less. Probe in
# that order so the column lands wherever the table actually lives.
_SCHEMAS = (None, "country", "configuration")


def _target_schema(bind) -> Union[str, None]:
    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)
    for schema in _SCHEMAS:
        if _TABLE in inspector.get_table_names(schema=schema):
            return schema
    return None


def upgrade() -> None:
    bind = op.get_bind()
    schema = _target_schema(bind)
    if schema is None:
        # Table not present in this database - nothing to alter (additive no-op).
        return
    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)
    existing = {c["name"] for c in inspector.get_columns(_TABLE, schema=schema)}
    if "rollout_percentage" not in existing:
        op.add_column(
            _TABLE,
            sa.Column("rollout_percentage", sa.Integer(), nullable=False, server_default="0"),
            schema=schema,
        )


def downgrade() -> None:
    bind = op.get_bind()
    schema = _target_schema(bind)
    if schema is None:
        return
    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)
    existing = {c["name"] for c in inspector.get_columns(_TABLE, schema=schema)}
    if "rollout_percentage" in existing:
        op.drop_column(_TABLE, "rollout_percentage", schema=schema)
