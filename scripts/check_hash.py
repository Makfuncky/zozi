import sqlite3

conn = sqlite3.connect(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\zozi.db')
cursor = conn.cursor()
cursor.execute("SELECT email, hashed_password FROM users WHERE email = 'logistics@zozi.com'")
for r in cursor.fetchall():
    print(f'User: {r[0]}')
    print(f'Hash: {r[1]}')
conn.close()
