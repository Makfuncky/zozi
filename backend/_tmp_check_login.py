import urllib.request, json

data = json.dumps({'username': 'customer@zozi.com', 'password': 'E2eCustomer#2026'}).encode()
req = urllib.request.Request('http://127.0.0.1:3100/api/auth/login', data=data, headers={'Content-Type': 'application/json'}, method='POST')
r = urllib.request.urlopen(req)
result = json.loads(r.read().decode())
print('Login user:', result.get('user'))
print('Access token sub:', json.loads(result['access_token'].split('.')[1] + '==').get('sub') if len(result['access_token'].split('.')) > 1 else 'N/A')
