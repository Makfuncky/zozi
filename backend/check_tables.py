import sqlite3
con = sqlite3.connect("zozi.db")
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("all tables:", cur.fetchall())
con.close()
