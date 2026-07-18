"""Test all 4 logins using form-encoded POST (same as browser/frontend)."""
import json
import urllib.error
import urllib.parse
import urllib.request

URL_FORM   = "http://127.0.0.1:8000/auth/login"
URL_JSON   = "http://127.0.0.1:8000/auth/login/json"
URL_CATS   = "http://127.0.0.1:8000/categories/"
URL_PRODS  = "http://127.0.0.1:8000/products/"

ACCOUNTS = [
    ("admin@zozi.com",     "admin123"),
    ("customer@zozi.com",  "customer123"),
    ("supplier@zozi.com",  "supplier123"),
    ("logistics@zozi.com", "logistics123"),
]

print("=" * 65)
print("FORM-ENCODED LOGIN TESTS (as browser sends)")
print("=" * 65)
for email, pw in ACCOUNTS:
    form_data = urllib.parse.urlencode({"username": email, "password": pw}).encode()
    req = urllib.request.Request(
        URL_FORM,
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            d = json.loads(resp.read())
            role = d["user"]["role"]
            tok = d["access_token"][:25]
            print(f"  OK   {email:<35} role={role}  token[0:25]={tok}...")
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"  FAIL {email:<35} HTTP {e.code}  body={body_err[:140]}")
    except Exception as e:
        print(f"  ERR  {email:<35} {e}")

print()
print("=" * 65)
print("PRODUCTS API")
print("=" * 65)
try:
    req = urllib.request.Request(URL_PRODS, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as r:
        prods = json.loads(r.read())
        items = prods.get("items") or prods if isinstance(prods, list) else []
        if isinstance(prods, dict):
            items = prods.get("items", prods.get("products", []))
        print(f"  Total products returned: {len(items)}")
        for p in items[:5]:
            print(f"    id={p.get('id')} name={p.get('name')!r} active={p.get('is_active')} approved={p.get('is_approved')}")
except Exception as e:
    print(f"  ERR: {e}")

print()
print("=" * 65)
print("CATEGORIES API")
print("=" * 65)
try:
    req = urllib.request.Request(URL_CATS, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as r:
        cats = json.loads(r.read())
        if isinstance(cats, list):
            print(f"  Total categories: {len(cats)}")
            for c in cats[:10]:
                print(f"    id={c.get('id')} name={c.get('name')!r} slug={c.get('slug')} active={c.get('is_active')}")
        else:
            print(f"  Response: {str(cats)[:200]}")
except Exception as e:
    print(f"  ERR: {e}")

