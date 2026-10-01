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
        return r.status, r.read().decode()[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return None, repr(e)

# Just admin / DevSeed123!
status, body = login("admin@zozi.com", "DevSeed123!")
print(f"admin/DevSeed123!: status={status} body={body}")