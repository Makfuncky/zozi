import sqlite3
conn = sqlite3.connect('zozi.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
for t in tables:
    print(t[0])
print(f'Total tables: {len(tables)}')
