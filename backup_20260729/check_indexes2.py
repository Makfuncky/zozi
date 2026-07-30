import sqlite3
conn = sqlite3.connect('zozi.db')
cursor = conn.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' ORDER BY name")
rows = cursor.fetchall()
print(f"Total indexes: {len(rows)}")
for row in rows[:20]:
    print(row[0])
if len(rows) > 20:
    print("...")
conn.close()
