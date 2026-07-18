import sqlite3

con = sqlite3.connect('zozi.db')

# Smoke/test users and their order counts
users = con.execute(
    "SELECT id, username, email, role FROM users WHERE username LIKE 'smoke%' OR username LIKE 'test%' OR username LIKE '%_1%' LIMIT 20"
).fetchall()
print("=== Smoke/Test users ===")
for uid, uname, email, role in users:
    orders = con.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (uid,)).fetchone()[0]
    print(f"  id={uid} username={uname} email={email} role={role} orders={orders}")

print()
roles = con.execute("SELECT role, COUNT(*) FROM users GROUP BY role").fetchall()
print("=== User role breakdown ===")
for r in roles:
    print(f"  {r[0]}: {r[1]}")

# Check if there are any FK constraints blocking deletion
print()
print("=== FK references to a sample smoke user ===")
if users:
    uid = users[0][0]
    print(f"Checking user id={uid}")
    for tbl, col in [
        ("orders", "user_id"),
        ("reviews", "user_id"),
        ("wishlists", "user_id"),
        ("addresses", "user_id"),
        ("notifications", "user_id"),
        ("support_tickets", "user_id"),
        ("audit_logs", "user_id"),
        ("payouts", "supplier_id"),
    ]:
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {tbl} WHERE {col}=?", (uid,)).fetchone()[0]
            print(f"  {tbl}.{col}: {count}")
        except Exception as e:
            print(f"  {tbl}.{col}: ERROR - {e}")

con.close()

