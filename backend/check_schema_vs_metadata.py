import os
os.environ["APP_ENV"] = "development"
from infrastructure.database.base import Base as ModelsBase
from infrastructure.database.database import engine
from sqlalchemy import text

missing = []
extra_tables = []
with engine.connect() as conn:
    db_tables = conn.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")).fetchall()
    db_set = {(s, t) for s, t in db_tables}

    for table in ModelsBase.metadata.tables.values():
        schema = table.schema or "public"
        if (schema, table.name) not in db_set:
            missing.append((schema, table.name))
            continue
        # column check
        q = text("SELECT column_name FROM information_schema.columns WHERE table_schema = :s AND table_name = :t ORDER BY ordinal_position")
        cols = {r[0] for r in conn.execute(q, {"s": schema, "t": table.name})}
        for col in table.columns:
            if col.name not in cols:
                missing.append((f"{schema}.{table.name}.{col.name}"))

print("Missing (schema is OLDER than metadata/HEAD):")
for m in missing:
    print("  -", m)
if not missing:
    print("  (none)")
