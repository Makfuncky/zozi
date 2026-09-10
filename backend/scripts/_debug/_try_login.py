import urllib.request, urllib.error, json
req = urllib.request.Request(
    "http://127.0.0.1:8001/api/v1/auth/login",
    data=b'{"email":"admin@zozi.com","password":"admin123"}',
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    r = urllib.request.urlopen(req, timeout=10)
    print("STATUS", r.status)
    print(r.read().decode())
except urllib.error.HTTPError as e:
    print("STATUS", e.code)
    print(e.read().decode())
except Exception as e:
    print("ERR", repr(e))