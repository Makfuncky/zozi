from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))
import migration_helpers

try:
    from dotenv import load_dotenv
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    load_dotenv(os.path.join(ROOT, ".env"), override=False)
except ImportError:
    pass

from infrastructure.database.base import Base as ModelsBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = ModelsBase.metadata

db_url = os.getenv("DATABASE_URL_DIRECT", os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url")))
# Alembic runs synchronous DDL; convert asyncpg DSNs to sync for migrations.
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
config.set_main_option("sqlalchemy.url", db_url)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

