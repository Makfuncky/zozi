import sqlite3
conn = sqlite3.connect('zozi.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print(f'Total tables: {len(tables)}')
for t in tables[:40]:
    print(f'  - {t[0]}')
if len(tables) > 40:
    print(f'  ... and {len(tables) - 40} more')
conn.close()
