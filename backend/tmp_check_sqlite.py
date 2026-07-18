import sqlite3

conn = sqlite3.connect('zozi.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('tables', [r[0] for r in cur.fetchall()])
conn.close()

