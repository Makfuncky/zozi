import urllib.request, urllib.error, http.cookiejar, json

BASE = "http://127.0.0.1:8123"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(BASE + "/health"), timeout=10)
csrf = next((c.value for c in jar if c.name == "csrf_token"), None)

def post(path, payload, token=None):
    h = {"Content-Type": "application/json", "X-CSRF-Token": csrf or ""}
    if token: h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(), method="POST", headers=h)
    try:
        r = op.open(req, timeout=60); return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def get(path, token):
    h = {"Authorization": "Bearer " + token}
    req = urllib.request.Request(BASE + path, headers=h)
    try:
        r = op.open(req, timeout=60); return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# login admin
st, body = post("/api/v1/auth/login", {"email": "admin@zozi.com", "password": "admin123"})
print("login:", st, body[:300])
tok = json.loads(body)["access_token"] if st == 200 else None
print("me:", (lambda s,b: f"{s} {b[:300]}") (*(get("/api/v1/auth/me", tok) if tok else ("no","token"))))
print("catalog:", (lambda s,b: f"{s} {b[:300]}") (*(get("/api/v1/rbac/catalog", tok) if tok else ("no","token"))))
