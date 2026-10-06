from logging.config import fileConfig
import asyncio
import os
import sys

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
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

    def do_run_migrations(connection):
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

    async def async_run():
        connectable = create_async_engine(
            db_url,
            poolclass=pool.NullPool,
            connect_args=connect_args,
        )
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    asyncio.run(async_run())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

