import sqlite3
import os
db_path = 'zozi.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print('Tables:', cursor.fetchall())
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    print('Indexes:', cursor.fetchall())
    conn.close()
else:
    print('Database file does not exist')
