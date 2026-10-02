from sqlalchemy import create_engine, text
from infrastructure.utils.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, email, role FROM accounts.users WHERE id = 3"))
    row = result.fetchone()
    print('User 3:', row)
    
    result2 = conn.execute(text("SELECT id, email, role FROM accounts.users WHERE email = 'customer@zozi.com'"))
    row2 = result2.fetchone()
    print('Customer user:', row2)
