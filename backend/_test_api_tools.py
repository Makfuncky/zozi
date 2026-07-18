import httpx

r = httpx.post('http://127.0.0.1:8000/auth/login', json={
    'email': 'admin@test.com', 'password': 'admin123'
})
token = r.json()['access_token']
print(f'Admin token: {token[:50]}...')

with open('test_product_image.jpg', 'rb') as f:
    file_data = f.read()

files = {'image': ('test.jpg', file_data, 'image/jpeg')}
data = {
    'name': 'Test API White Balance',
    'description': 'Testing white_balance param through API',
    'price': 29.99,
    'stock_quantity': 15,
    'category': 'Electronics',
    'process_white_balance': 'true',
    'process_denoise': 'true',
}

headers = {'Authorization': f'Bearer {token}'}
r = httpx.post('http://127.0.0.1:8000/supplier/products', headers=headers, data=data, files=files)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    body = r.json()
    print(f'OK - product created with ID: {body.get("id", "?")}')
elif r.status_code == 422:
    errors = r.json().get('detail', [])
    for e in errors:
        print(f'  Validation error: {e}')
else:
    print(f'Response: {r.text[:300]}')

