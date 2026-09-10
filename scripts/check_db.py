import sqlite3

conn = sqlite3.connect(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\zozi.db')
cursor = conn.cursor()

# Find user tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%user%'")
tables = cursor.fetchall()
print('User tables:', tables)

for t in tables:
    tname = t[0]
    cursor.execute(f'PRAGMA table_info({tname})')
    cols = [c[1] for c in cursor.fetchall()]
    print(f'\nTable {tname} columns: {cols}')
    try:
        cursor.execute(f'SELECT * FROM {tname} WHERE email LIKE "%logistics%" LIMIT 5')
        rows = cursor.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print(f'Error: {e}')

conn.close()
