import sqlite3
import os

for root, dirs, files in os.walk(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend'):
    for f in files:
        if f == 'zozi.db':
            path = os.path.join(root, f)
            print(f'Found: {path}')
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            print(f'  User count: {count}')
            cursor.execute("SELECT email, hashed_password FROM users WHERE email LIKE '%logistics%'")
            for r in cursor.fetchall():
                print(f'  User: {r[0]}, hash: {r[1][:40]}...')
            conn.close()
