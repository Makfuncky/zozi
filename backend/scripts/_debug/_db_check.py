from infrastructure.database.database import engine
print("URL:", str(engine.url))
# Test query through accounts.users
from sqlalchemy import text
with engine.connect() as conn:
    print("users count:", conn.execute(text("SELECT count(*) FROM accounts.users")).scalar())