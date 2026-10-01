from infrastructure.database.database import engine
from infrastructure.utils.auth import verify_password
from sqlalchemy import text

with engine.connect() as c:
    rows = c.execute(text("SELECT email, hashed_password FROM users")).fetchall()
for email, h in rows:
    hp = h or ""
    print(email, "| hash[:24]:", hp[:24],
          "| admin123:", verify_password("admin123", hp),
          "| customer123:", verify_password("customer123", hp))
