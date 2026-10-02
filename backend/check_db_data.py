import os
os.environ["APP_ENV"] = "development"
from infrastructure.database.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT schemaname || '.' || tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY 1"))
    tables = [r[0] for r in result]
    total = 0
    for schema, table in (t.split(".") for t in tables):
        r = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{table}"))
        n = r.fetchone()[0]
        total += n
        if n > 0:
            print(f"DATA: {schema}.{table} has {n} rows")
print(f"Total tables: {len(tables)}, total rows: {total}")