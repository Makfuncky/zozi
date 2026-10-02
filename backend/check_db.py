import os
os.environ["APP_ENV"] = "development"
from infrastructure.database.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT table_schema || '.' || table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema') ORDER BY 1"))
    print("Tables:", [r[0] for r in result])
    try:
        res = conn.execute(text("SELECT * FROM alembic_version"))
        print("alembic_version:", [dict(r) for r in res])
    except Exception as e:
        print("alembic_version table:", str(e))
