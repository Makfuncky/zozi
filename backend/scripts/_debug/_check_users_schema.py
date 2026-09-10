from infrastructure.database.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='accounts' AND table_name='users' ORDER BY ordinal_position"))
    for r in res.fetchall():
        print(r)