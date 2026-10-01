import sqlite3
from infrastructure.utils.auth import verify_password

c = sqlite3.connect("database/zozi.db")
for email in ("admin@zozi.com", "supplier@zozi.com", "customer@zozi.com"):
    row = c.execute("SELECT email, hashed_password, role FROM users WHERE email=?", (email,)).fetchone()
    if not row:
        print(email, "MISSING")
        continue
    pw = "admin123" if email == "admin@zozi.com" else ("supplier123" if email == "supplier@zozi.com" else "customer123")
    print(email, "role=", row[2], "verify", pw, "=", verify_password(pw, row[1]))
