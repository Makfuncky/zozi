"""Alembic migration helper."""
from __future__ import annotations

from pathlib import Path

from alembic.config import Config

from alembic import command


def get_alembic_config() -> Config:
    """Get Alembic configuration."""
    alembic_ini = str(Path(__file__).resolve().parent.parent / "alembic.ini")
    return Config(alembic_ini)


def upgrade_database_to_head() -> None:
    """Run alembic upgrade head programmatically."""
    alembic_ini = str(Path(__file__).resolve().parent.parent / "alembic.ini")
    cfg = Config(alembic_ini)
    command.upgrade(cfg, "head")


def check_schema_drift() -> bool:
    """Check if ORM models differ from migration head. Returns True if drift detected."""
    alembic_ini = str(Path(__file__).resolve().parent.parent / "alembic.ini")
    cfg = Config(alembic_ini)
    from alembic.script import ScriptDirectory
    
    script = ScriptDirectory.from_config(cfg)
    
    from sqlalchemy import inspect

    from data.base import Base
    from data.db import engine
    
    inspector = inspect(engine)
    metadata_tables = set(Base.metadata.tables.keys())
    db_tables = set(inspector.get_table_names())
    
    return metadata_tables != db_tables