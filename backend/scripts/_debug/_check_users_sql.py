from infrastructure.database.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # All schemas with users
    print("Schemas with users table:")
    res = conn.execute(text("""
        SELECT table_schema FROM information_schema.tables 
        WHERE table_name='users' AND table_schema NOT IN ('pg_catalog','information_schema')
    """))
    for r in res.fetchall():
        print(" ", r.table_schema)
    # All rows in accounts.users
    res = conn.execute(text("SELECT count(*) FROM accounts.users"))
    print("accounts.users count:", res.scalar())
    # Check ALL tables count
    res = conn.execute(text("""
        SELECT table_schema, table_name FROM information_schema.tables 
        WHERE table_type='BASE TABLE' AND table_schema NOT IN ('pg_catalog','information_schema')
        ORDER BY table_schema, table_name
    """))
    print("All base tables:")
    for r in res.fetchall():
        print(f"  {r.table_schema}.{r.table_name}")