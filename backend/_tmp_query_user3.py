from sqlalchemy import create_engine, text
from infrastructure.utils.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    # Direct query using the same logic as _find_user_for_login
    result = conn.execute(text("SELECT id, email, role FROM accounts.users WHERE LOWER(email) = LOWER(:email)"), {"email": "customer@zozi.com"})
    row = result.fetchone()
    if row:
        print(f'Found user: id={row[0]}, email={row[1]}, role={row[2]}')
    else:
        print('User not found')
    
    # Also check id=3
    result2 = conn.execute(text("SELECT id, email, role FROM accounts.users WHERE id = :id"), {"id": 3})
    row2 = result2.fetchone()
    if row2:
        print(f'User 3: id={row2[0]}, email={row2[1]}, role={row2[2]}')
    else:
        print('User 3 not found')
