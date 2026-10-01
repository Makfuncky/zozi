import urllib.request, urllib.error, http.cookiejar, json, traceback, sys

BASE = "http://127.0.0.1:8000"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

try:
    op.open(urllib.request.Request(BASE + "/health"), timeout=10)
except Exception as e:
    print("warmup err", e)

csrf = None
for c in jar:
    if c.name == "csrf_token":
        csrf = c.value
print("csrf token present:", bool(csrf))

def login(email, pw):
    data = json.dumps({"email": email, "password": pw}).encode()
    req = urllib.request.Request(
        BASE + "/api/v1/auth/login", data=data, method="POST",
        headers={"Content-Type": "application/json", "X-CSRF-Token": csrf or ""},
    )
    try:
        r = op.open(req, timeout=60)
        print(f"LOGIN {email} -> {r.status}: {r.read().decode()[:300]}")
    except urllib.error.HTTPError as e:
        print(f"LOGIN {email} -> HTTP {e.code}: {e.read().decode()[:300]}")
    except Exception as e:
        print(f"LOGIN {email} -> ERR {type(e).__name__}: {e}")

login("admin@zozi.com", "admin123")
login("supplier@zozi.com", "supplier123")
login("customer@zozi.com", "customer123")
