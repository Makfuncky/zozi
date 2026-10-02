import os
os.environ["APP_ENV"] = "development"
from infrastructure.database.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    q = text("""
        SELECT pid, state, query, now() - query_start AS duration, backend_type
        FROM pg_stat_activity
        WHERE state IS NOT NULL
        ORDER BY duration DESC NULLS LAST
        LIMIT 20
    """)
    for pid, state, query, dur, btype in conn.execute(q):
        print(f"{pid} state={state} dur={dur} type={btype}")
        print(f"   {query[:200]}")