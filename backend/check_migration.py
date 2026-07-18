from sqlalchemy import create_engine, text
from utils.config import settings

engine = create_engine(settings.database_url)
print("DB URL:", settings.database_url)
with engine.connect() as c:
    try:
        r = c.execute(text("select version_num from alembic_version")).fetchone()
        print("Alembic current revision:", r[0] if r else None)
    except Exception as e:
        print("Failed to read alembic_version:", e)

