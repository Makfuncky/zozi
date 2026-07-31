"""Alembic migration helper."""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def upgrade_database_to_head() -> None:
    """Run alembic upgrade head programmatically."""
    alembic_ini = str(Path(__file__).resolve().parent.parent / "alembic.ini")
    cfg = Config(alembic_ini)
    command.upgrade(cfg, "head")
