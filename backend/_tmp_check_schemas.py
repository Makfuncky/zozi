from sqlalchemy import create_engine, text
from infrastructure.utils.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"))
    rows = result.fetchall()
    print('Schemas:', [r[0] for r in rows])
