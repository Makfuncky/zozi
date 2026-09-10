import sqlite3
con = sqlite3.connect('var/zozi.db')
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
print('users table:', cur.fetchall())
try:
    cur.execute("SELECT count(*) FROM users")
    print('users count:', cur.fetchone())
except Exception as e:
    print('no users:', e)
cur.execute("SELECT email FROM users LIMIT 5")
for r in cur.fetchall(): print(r)
