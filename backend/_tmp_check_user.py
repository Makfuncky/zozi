from sqlalchemy import create_engine, text
from infrastructure.utils.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%user%'"))
    rows = result.fetchall()
    print('User tables:', [r[0] for r in rows])
