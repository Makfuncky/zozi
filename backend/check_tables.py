import sqlite3
conn = sqlite3.connect('zozi.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(tables)

# Also check alembic version
cur.execute("SELECT version_num FROM alembic_version")
print("Alembic version:", cur.fetchall())
conn.close()

