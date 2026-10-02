from sqlalchemy import create_engine, text
from infrastructure.utils.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'accounts' ORDER BY table_name"))
    rows = result.fetchall()
    print('Tables in accounts:', [r[0] for r in rows])
