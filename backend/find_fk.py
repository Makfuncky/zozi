import sys
sys.path.insert(0, '.')
from db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
uid = 13

all_tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
print(f"Checking user_id={uid} across all tables with FK to users...")
found = False
for (t,) in all_tables:
    fk_rows = db.execute(text(f'PRAGMA foreign_key_list("{t}")')).fetchall()
    fk_cols = [r[3] for r in fk_rows if r[2] == 'users']
    for col in fk_cols:
        try:
            r = db.execute(text(f'SELECT COUNT(*) FROM "{t}" WHERE "{col}" = :uid'), {'uid': uid}).scalar()
            if r:
                print(f'  HIT: {t}.{col} = {r} rows')
                found = True
        except Exception as e:
            print(f'  ERR: {t}.{col}: {e}')
if not found:
    print("  (none)")
print("Done.")
db.close()

