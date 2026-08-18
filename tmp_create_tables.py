import os, sys, traceback
os.chdir(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
sys.path.insert(0, os.getcwd())
# Ensure dev SQLite is targeted (canonical path: backend/infrastructure/database/zozi.db)
os.environ.setdefault("DATABASE_URL", "sqlite:///database/zozi.db")

print("== importing models ==")
try:
    from infrastructure.database import models
    n_tables = len(models.Base.metadata.tables)
    print("OK: models imported. tables in metadata =", n_tables)
    if n_tables == 0:
        print("WARN: metadata empty - nothing to create")
        sys.exit(0)
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("== creating tables via infrastructure.database.database.create_tables() ==")
try:
    from infrastructure.database import database as dbmod
    print("engine url:", dbmod.DATABASE_URL)
    dbmod.create_tables()
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("== verifying zozi.db ==")
import sqlite3
db_path = dbmod.DATABASE_URL.replace("sqlite:///", "")
if not os.path.isabs(db_path):
    db_path = os.path.join(os.getcwd(), db_path)
con = sqlite3.connect(db_path)
rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
con.close()
names = [r[0] for r in rows]
print("tables in zozi.db =", len(names))
print(names[:50])
