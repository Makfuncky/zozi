import sqlite3
import bcrypt

# Generate a known hash for logistics123
password = b'logistics123'
hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=10)).decode()
print(f'New hash: {hashed}')

conn = sqlite3.connect(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\zozi.db')
cursor = conn.cursor()
cursor.execute("UPDATE users SET hashed_password = ? WHERE email = 'logistics@zozi.com'", (hashed,))
conn.commit()
print(f'Updated {cursor.rowcount} rows')
conn.close()
