import urllib.request, json, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

data = json.dumps({'username': 'customer@zozi.com', 'password': 'E2eCustomer#2026'}).encode()
req = urllib.request.Request('http://127.0.0.1:3100/api/auth/login', data=data, headers={'Content-Type': 'application/json'}, method='POST')
r = opener.open(req)

print('All cookies after login:')
for c in cj:
    print(f'  {c.name}: domain={c.domain}, path={c.path}, value={c.value[:40]}...')
