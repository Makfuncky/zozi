from sqlalchemy import create_engine, text
from infrastructure.utils.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    # Check all tables named 'users' in any schema
    result = conn.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'users'"))
    rows = result.fetchall()
    print('All users tables:', rows)
    
    # Check views
    result2 = conn.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name LIKE '%user%' AND table_type = 'VIEW'"))
    rows2 = result2.fetchall()
    print('User views:', rows2)
