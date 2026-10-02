import sqlite3
db = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\zozi.db"
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%user%'")
print("tables:", cur.fetchall())
try:
    cur.execute("SELECT id, email, role, username FROM accounts")
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print("accounts err:", e)
con.close()
