from sqlalchemy import create_engine, text
from infrastructure.utils.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    # Check all users
    result = conn.execute(text("SELECT id, email, role FROM accounts.users ORDER BY id"))
    rows = result.fetchall()
    print('All users:')
    for row in rows:
        print(f'  id={row[0]}, email={row[1]}, role={row[2]}')
