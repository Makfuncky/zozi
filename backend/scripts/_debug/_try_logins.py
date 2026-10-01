import urllib.request, urllib.error, json

def login(email, password):
    req = urllib.request.Request(
        "http://127.0.0.1:8001/api/v1/auth/login",
        data=json.dumps({"email": email, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        r = urllib.request.urlopen(req, timeout=10)
        body = r.read().decode()
        return r.status, body[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]
    except Exception as e:
        return None, repr(e)

for role, email in [
    ("admin", "admin@zozi.com"),
    ("supplier", "supplier@zozi.com"),
    ("customer", "customer@zozi.com"),
    ("employee", "employee@zozi.com"),
    ("logistics", "logistics@zozi.com"),
]:
    status, body = login(email, "DevSeed123!")
    print(f"{role:10s} {email:30s} pw=DevSeed123! status={status}")
    print(f"  body: {body[:150]}")