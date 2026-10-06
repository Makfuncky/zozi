"""widen promotions.banners colour columns to String(32)

The ORM declares ``bg_color``/``text_color``/``subtitle_color``/
``btn_bg_color``/``btn_text_color``/``badge_color`` as ``String(10)`` while the
seeded default banners store CSS values such as ``rgba(255,255,255,0.86)``
(23 chars). PostgreSQL then rejected the insert with
``StringDataRightTruncation`` and the banners endpoint answered 500.

This revision widens the six columns to ``String(32)`` (enough for any
``rgba(r,g,b,a)`` value) and is idempotent: it only alters columns that are
still narrower.

Revision ID: 20261006_0022_widen_banner_color_columns
Revises: 20261004_0021_fix_products_fk_and_defaults
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261006_0022_widen_banner_color_columns"
down_revision: Union[str, None] = "20261004_0021_fix_products_fk_and_defaults"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None

_TARGET_LEN = 32
_COLOR_COLUMNS = (
    "bg_color",
    "text_color",
    "subtitle_color",
    "btn_bg_color",
    "btn_text_color",
    "badge_color",
)


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


def _widen(bind) -> None:
    inspector = sa.inspect(bind)
    existing = {c["name"]: c for c in inspector.get_columns("banners", schema="promotions")}
    for name in _COLOR_COLUMNS:
        col = existing.get(name)
        if col is None:
            continue
        current_len = col["type"].length if hasattr(col["type"], "length") else None
        if current_len is None or current_len >= _TARGET_LEN:
            continue
        op.alter_column(
            "banners",
            name,
            type_=sa.String(length=_TARGET_LEN),
            existing_type=sa.String(length=current_len),
            schema="promotions",
        )


def upgrade() -> None:
    bind = op.get_bind()
    if _is_offline(bind):
        return
    if bind.dialect.name == "sqlite":
        return
    _widen(bind)


def downgrade() -> None:
    bind = op.get_bind()
    if _is_offline(bind):
        return
    if bind.dialect.name == "sqlite":
        return
    inspector = sa.inspect(bind)
    existing = {c["name"]: c for c in inspector.get_columns("banners", schema="promotions")}
    for name in _COLOR_COLUMNS:
        if name not in existing:
            continue
        op.alter_column(
            "banners",
            name,
            type_=sa.String(length=10),
            existing_type=sa.String(length=_TARGET_LEN),
            schema="promotions",
        )
