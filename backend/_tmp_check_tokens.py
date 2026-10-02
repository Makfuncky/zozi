import urllib.request, json, base64, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

data = json.dumps({'username': 'customer@zozi.com', 'password': 'E2eCustomer#2026'}).encode()
req = urllib.request.Request('http://127.0.0.1:3100/api/auth/login', data=data, headers={'Content-Type': 'application/json'}, method='POST')
r = opener.open(req)

# Get cookies
for c in cj:
    if c.name == 'access_token':
        payload = c.value.split('.')[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload).decode()
        token_data = json.loads(decoded)
        print('Access token sub:', token_data.get('sub'))
        print('Access token role:', token_data.get('role'))
    if c.name == 'refresh_token':
        payload = c.value.split('.')[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload).decode()
        token_data = json.loads(decoded)
        print('Refresh token sub:', token_data.get('sub'))
        print('Refresh token role:', token_data.get('role'))
