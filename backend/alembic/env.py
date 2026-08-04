from logging.config import fileConfig
import os
import sys

os.environ.setdefault('ALEMBIC_MODE', 'true')

from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import Base as ModelsBase
from utils.schema_compat import SCHEMA_TRANSLATE_MAP, patch_fk_schemas

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = ModelsBase.metadata

# Rewrite bare foreign-key targets to schema-qualified form so metadata can be
# created/reflected on SQLite (which has no real schemas) the same way the app
# engine does via schema_translate_map. Idempotent; safe on Postgres too.
patch_fk_schemas(target_metadata)

db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
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
    execution_options = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        execution_options["schema_translate_map"] = SCHEMA_TRANSLATE_MAP

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
        execution_options=execution_options or None,
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
