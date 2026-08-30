import sqlite3
from infrastructure.utils.auth import verify_password

files = [
    r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\database\zozi.db",
    r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\infrastructure\database\zozi.db",
]
pws = {"admin@zozi.com": "admin123", "supplier@zozi.com": "supplier123", "customer@zozi.com": "customer123"}
for f in files:
    print("===", f, "===")
    try:
        c = sqlite3.connect(f)
        for email, pw in pws.items():
            row = c.execute("SELECT hashed_password FROM users WHERE email=?", (email,)).fetchone()
            if not row:
                print(" ", email, "MISSING")
            else:
                print(" ", email, "verify", pw, "=", verify_password(pw, row[0]))
    except Exception as e:
        print("  ERR", e)
