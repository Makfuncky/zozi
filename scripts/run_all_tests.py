import sqlite3
import bcrypt
import urllib.request
import json

# Step 1: Reset password
password = b'logistics123'
hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode()

conn = sqlite3.connect(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\zozi.db')
cursor = conn.cursor()
cursor.execute("UPDATE users SET hashed_password = ? WHERE email = 'logistics@zozi.com'", (hashed,))
conn.commit()
conn.close()

# Step 2: Login
url = 'http://127.0.0.1:8000/api/v1/auth/login'
data = json.dumps({'email': 'logistics@zozi.com', 'password': 'logistics123'}).encode()
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
login_json = json.loads(resp.read().decode())
token = login_json.get('access_token') or login_json.get('token')
print(f'Login: OK (token {token[:20]}...)')

# Step 3: Test endpoints - try both path formats
print('\n=== ENDPOINT TESTS ===')
endpoints = [
    # User-specified paths
    ('/logistics-partner/dashboard', 'dashboard (user path)'),
    ('/api/v1/logistics/shipments', 'shipments (user path)'),
    ('/api/v1/logistics/accounts/profile', 'profile (user path)'),
    ('/api/v1/logistics/analytics', 'analytics (user path)'),
    # Correct paths based on router
    ('/logistics-partner/shipments', 'shipments (router path)'),
    ('/logistics-partner/profile', 'profile (router path)'),
    ('/logistics-partner/analytics', 'analytics (router path)'),
]

results = []
for path, name in endpoints:
    url = f'http://127.0.0.1:8000{path}'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        status = resp.status
        body = resp.read().decode()
        try:
            json_body = json.loads(body)
            has_data = bool(json_body) if isinstance(json_body, dict) else len(json_body) > 0 if isinstance(json_body, list) else True
            preview = json.dumps(json_body, indent=2)[:300]
        except:
            has_data = len(body) > 10
            preview = body[:300]
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode()
        has_data = False
        preview = body[:200]
    
    result = 'PASS' if status == 200 and has_data else 'FAIL'
    results.append((name, status, has_data, result))
    print(f'\n--- {name}: GET {path} ---')
    print(f'  Status: {status} | Has data: {has_data} | Result: {result}')
    print(f'  Preview: {preview}')

print('\n=== SUMMARY ===')
for name, status, has_data, result in results:
    print(f'  {name}: HTTP {status} | data={has_data} | {result}')
