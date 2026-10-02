from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from infrastructure.utils.config import settings
from domains.accounts.models.user import User

engine = create_engine(settings.database_url)
with Session(engine) as db:
    user = db.query(User).filter(func.lower(User.email) == 'customer@zozi.com').first()
    if user:
        print(f'Found user: id={user.id}, email={user.email}, role={user.role}')
    else:
        print('User not found')
