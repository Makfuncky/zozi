import urllib.request, urllib.error, json, urllib.parse, http.cookiejar, sys

BASE = "http://127.0.0.1:8123"

def login(email, pw):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.open(urllib.request.Request(BASE + "/health"), timeout=10)
    csrf = next((c.value for c in jar if c.name == "csrf_token"), None)
    data = json.dumps({"email": email, "password": pw}).encode()
    req = urllib.request.Request(BASE + "/api/v1/auth/login", data=data, method="POST",
        headers={"Content-Type": "application/json", "X-CSRF-Token": csrf or ""})
    try:
        r = op.open(req, timeout=60)
        return json.loads(r.read().decode())["access_token"]
    except urllib.error.HTTPError as e:
        print("LOGIN FAILED", e.code, e.read().decode()[:160]); raise

def get_paths():
    import main
    out = []
    for r in main.app.routes:
        p = getattr(r, "path", "")
        methods = getattr(r, "methods", None)
        if methods and "GET" in methods and "{" not in p:
            out.append(p)
    # Focus on core e-commerce read endpoints; skip heavy analytics dashboards.
    want = ("catalog", "product", "category", "country", "customer", "supplier",
            "order", "brand", "review", "coupon", "banner", "wallet", "currency",
            "rbac", "auth", "profile", "address", "cart")
    core = [p for p in out if any(w in p for w in want) and "analytics" not in p]
    if not core:
        core = out
    return core[:30]

def main_test():
    tok = login("admin@zozi.com", "admin123")
    paths = get_paths()
    print(f"GET param-less routes: {len(paths)}", flush=True)
    ok, bycode = [], {}
    LIMIT = 35
    for p in sorted(paths)[:LIMIT]:
        req = urllib.request.Request(BASE + p, headers={"Authorization": "Bearer " + tok})
        try:
            r = urllib.request.urlopen(req, timeout=10)
            code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as e:
            code = "ERR:" + type(e).__name__
        if code == 200:
            ok.append(p)
        else:
            bycode.setdefault(str(code), []).append(p)
        print(f"  {code} {p}", flush=True)
    print(f"200 OK: {len(ok)} / {min(LIMIT,len(paths))} tested", flush=True)
    for c in sorted(bycode):
        print(f"  {c}: {bycode[c][:5]}")

main_test()
