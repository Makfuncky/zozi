"""Quick diagnostic: test all 4 demo logins and check products/categories."""
import json
import sqlite3
import urllib.request
import urllib.error

URL = "http://127.0.0.1:8000/auth/login/json"

ACCOUNTS = [
    ("admin@zozi.com", "admin123"),
    ("customer@zozi.com", "customer123"),
    ("supplier@zozi.com", "supplier123"),
    ("logistics@zozi.com", "logistics123"),
]

print("=" * 60)
print("LOGIN TESTS")
print("=" * 60)
for email, pw in ACCOUNTS:
    body = json.dumps({"email": email, "password": pw}).encode()
    req = urllib.request.Request(
        URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            role = data["user"]["role"]
            tok = data["access_token"][:20]
            print(f"  OK   {email:<32}  role={role}  token={tok}...")
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"  FAIL {email:<32}  HTTP {e.code}  {body_err[:120]}")
    except Exception as e:
        print(f"  FAIL {email:<32}  {e}")

# ── DB inspection ────────────────────────────────────────────
print()
print("=" * 60)
print("DATABASE INSPECTION")
print("=" * 60)
con = sqlite3.connect("zozi.db")
con.row_factory = sqlite3.Row

# Products
print("\n--- Products ---")
products = con.execute(
    "SELECT id, name, price, category_id, supplier_id, stock, is_active FROM products"
).fetchall()
for p in products:
    print(f"  id={p['id']} name={p['name']!r} price={p['price']} cat_id={p['category_id']} stock={p['stock']} active={p['is_active']}")

# Product count by is_active
active_products = con.execute("SELECT COUNT(*) FROM products WHERE is_active=1").fetchone()[0]
inactive_products = con.execute("SELECT COUNT(*) FROM products WHERE is_active=0").fetchone()[0]
print(f"\n  Active products: {active_products}  |  Inactive: {inactive_products}")

# Categories
print("\n--- Categories ---")
cats = con.execute("SELECT id, name, slug, is_active FROM categories").fetchall()
if cats:
    for c in cats:
        print(f"  id={c['id']} name={c['name']!r} slug={c['slug']} active={c['is_active']}")
else:
    print("  !!! CATEGORIES TABLE IS EMPTY !!!")

# Rate limit / failed logins check (audit_logs)
print("\n--- Recent Audit Logs (last 10) ---")
logs = con.execute(
    "SELECT action, user_id, details, created_at FROM audit_logs ORDER BY id DESC LIMIT 10"
).fetchall()
for l in logs:
    print(f"  [{l['created_at']}] {l['action']} user_id={l['user_id']} details={str(l['details'])[:80]}")

# Check account_locked / failed_login_count fields
print("\n--- User Account Lock Status ---")
try:
    lock_rows = con.execute(
        "SELECT email, role, is_active, email_verified, failed_login_count, locked_until FROM users WHERE email IN ('admin@zozi.com','customer@zozi.com','supplier@zozi.com','logistics@zozi.com') ORDER BY email"
    ).fetchall()
    for r in lock_rows:
        print(f"  {r['email']:<32} role={r['role']} active={r['is_active']} verified={r['email_verified']} fails={r['failed_login_count']} locked_until={r['locked_until']}")
except Exception as e:
    print(f"  Column check error: {e}")

con.close()
print()
print("Done.")

