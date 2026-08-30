import sqlite3, os
db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "zozi.db")
con = sqlite3.connect(db)
rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print("TABLE_COUNT", len(rows))
print([r[0] for r in rows][:80])
# sample a few expected tables
for t in ["users", "country_staff_assignments", "alembic_version"]:
    try:
        n = con.execute(f"SELECT COUNT(*) FROM \"{t}\"").fetchone()[0]
        print(f"  {t}: {n} rows")
    except Exception as e:
        print(f"  {t}: ERR {e}")
con.close()
