import os, sqlite3
import main  # triggers router/model imports
from infrastructure.database.base import Base
from sqlalchemy import create_engine

e = create_engine("sqlite:///C:/tmp/_createtest.db")
# mirror dev engine: strip schemas
for t in Base.metadata.tables.values():
    t.schema = None
Base.metadata.create_all(bind=e)
cols = [r[1] for r in sqlite3.connect("C:/tmp/_createtest.db").execute("PRAGMA table_info(users)")]
print("CREATED users cols:", cols)
print("email_verified present:", "email_verified" in cols)
