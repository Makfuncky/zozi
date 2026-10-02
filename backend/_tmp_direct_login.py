import urllib.request, json

# Direct call to backend (not through Next.js proxy)
data = json.dumps({'username': 'customer@zozi.com', 'password': 'E2eCustomer#2026'}).encode()
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', data=data, headers={'Content-Type': 'application/json'}, method='POST')
try:
    r = urllib.request.urlopen(req)
    result = json.loads(r.read().decode())
    print('Direct login user:', result.get('user'))
    print('Direct access_token sub:', result.get('access_token', '').split('.')[1][:40] if result.get('access_token') else 'N/A')
except urllib.error.HTTPError as e:
    print('Direct login error:', e.code, e.read().decode()[:300])
