import os
os.environ["APP_ENV"] = "development"
from infrastructure.database.database import engine
from sqlalchemy import text

checks = [
    ("public", "internal_messages", "is_deleted"),
    ("public", "org_units", "path"),
    ("public", "org_units", "depth"),
    ("public", "org_units", "parent_id"),
    ("public", "sales_order_lines", "so_id"),
    ("public", "sales_order_lines", "id"),
    ("accounts", "users", "email"),
    ("accounts", "users", "username"),
    ("accounts", "users", "hashed_password"),
    ("accounts", "users", "role"),
    ("comms", "internal_messages", "is_deleted"),
    ("hr", "org_units", "path"),
    ("hr", "org_units", "depth"),
]
with engine.connect() as conn:
    for schema, table, col in checks:
        q = text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = :s AND table_name = :t AND column_name = :col)")
        r = conn.execute(q, {"s": schema, "t": table, "col": col})
        print(f"{schema}.{table}.{col} ->", bool(r.fetchone()[0]))
