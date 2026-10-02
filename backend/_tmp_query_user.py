from sqlalchemy import create_engine, func
from infrastructure.utils.config import settings
from domains.accounts.models.user import User

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    # Use the same query as _find_user_for_login
    user = conn.execute(
        # Need to use session for ORM query
    ).fetchone()
    print('Need to use session for ORM')

# Try with session
from sqlalchemy.orm import Session
with Session(engine) as db:
    user = db.query(User).filter(func.lower(User.email) == 'customer@zozi.com').first()
    if user:
        print(f'Found user: id={user.id}, email={user.email}, role={user.role}')
    else:
        print('User not found')
