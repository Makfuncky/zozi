"""Legacy alias: dependencies.db -> db.database."""
from data.db import *  # noqa: F401,F403
from data.db import get_db, SessionLocal  # noqa: F401

