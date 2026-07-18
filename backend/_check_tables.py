from sqlalchemy import text
from db.database import SessionLocal
db = SessionLocal()
rows = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
db.close()
for r in rows:
    print(r[0])

