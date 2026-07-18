from sqlalchemy import text
from db.database import SessionLocal
db = SessionLocal()
# Get all column names from country_configs
cols = db.execute(text("PRAGMA table_info(country_configs)")).fetchall()
print("=== country_configs columns ===")
for c in cols:
    print(f"  {c[1]}: {c[2]}")
# Check alembic version
ver = db.execute(text("SELECT version_num FROM alembic_version")).fetchone()
print(f"\nAlembic version: {ver[0]}")
db.close()

