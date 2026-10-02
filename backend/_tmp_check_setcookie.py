import urllib.request, json, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

data = json.dumps({'username': 'customer@zozi.com', 'password': 'E2eCustomer#2026'}).encode()
req = urllib.request.Request('http://127.0.0.1:3100/api/auth/login', data=data, headers={'Content-Type': 'application/json'}, method='POST')
r = opener.open(req)

print('Status:', r.status)
print('Set-Cookie headers:')
for header, value in r.headers.items():
    if header.lower() == 'set-cookie':
        print(f'  {value}')
