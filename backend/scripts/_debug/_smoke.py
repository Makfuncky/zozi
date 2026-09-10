import requests, json
BASE = "http://127.0.0.1:8000"
s = requests.Session()
# GET to obtain CSRF cookie
r = s.get(f"{BASE}/health")
print("health", r.status_code)
csrf = s.cookies.get("csrf_token") or s.cookies.get("csrftoken") or s.cookies.get("csrf")
print("cookies:", list(s.cookies.keys()))
# Try the /rbac/catalog after login using csrf header
headers = {}
if csrf:
    headers["X-CSRF-Token"] = csrf
r2 = s.post(f"{BASE}/api/v1/auth/login",
            json={"email": "admin@zozi.com", "password": "admin123"},
            headers=headers)
print("login", r2.status_code, r2.text[:300])
if r2.status_code == 200:
    tok = r2.json().get("access_token") or r2.json().get("token")
    h2 = {"Authorization": f"Bearer {tok}"}
    if csrf:
        h2["X-CSRF-Token"] = csrf
    r3 = s.get(f"{BASE}/api/v1/rbac/catalog", headers=h2)
    print("catalog", r3.status_code, "keys:", list(r3.json().keys())[:8] if r3.status_code==200 else r3.text[:200])
