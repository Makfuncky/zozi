from sqlalchemy import create_engine, text
from infrastructure.utils.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text("SELECT tgname, tgrelid::regclass FROM pg_trigger WHERE tgrelid = 'accounts.users'::regclass"))
    rows = result.fetchall()
    print('Triggers on accounts.users:', rows)
