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
    ROOT = os.path.dirname(os.path.dirname(__file__))
    load_dotenv(os.path.join(ROOT, ".env"), override=False)
except ImportError:
    pass

from infrastructure.database.base import Base as ModelsBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = ModelsBase.metadata

db_url = os.getenv("DATABASE_URL_DIRECT", os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url")))
print(f"DEBUG: DATABASE_URL_DIRECT env = {os.getenv('DATABASE_URL_DIRECT', 'NOT SET')}")
print(f"DEBUG: DATABASE_URL env = {os.getenv('DATABASE_URL', 'NOT SET')}")
print(f"DEBUG: db_url before convert = {db_url!r}")
# Alembic runs synchronous DDL; convert asyncpg DSNs to sync for migrations.
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
print(f"DEBUG: db_url after convert = {db_url!r}")
config.set_main_option("sqlalchemy.url", db_url)
