import requests

# Test login
resp = requests.post("http://localhost:8000/auth/login", data={
    "username": "admin@test.com",
    "password": "admin123"
})
print(f"Login status: {resp.status_code}")
token = resp.json().get('access_token', '')

headers = {"Authorization": f"Bearer {token}"}

# Test search
resp2 = requests.get("http://localhost:8000/search/advanced", params={"q": "handbag"})
print(f"Search status: {resp2.status_code}")
print(f"Products: {len(resp2.json().get('products', []))}")

# Test fuzzy search
resp3 = requests.get("http://localhost:8000/search/fuzzy", params={"q": "iphnoe"})
print(f"Fuzzy search status: {resp3.status_code}")
print(f"Fuzzy products: {len(resp3.json().get('products', []))}")

# Test word prediction
resp4 = requests.get("http://localhost:8000/search/predict", params={"q": "iph"})
print(f"Prediction status: {resp4.status_code}")
print(f"Predictions: {resp4.json().get('predictions', [])}")

# Test filtered products
resp5 = requests.post("http://localhost:8000/search/filtered", json={"min_price": 50, "max_price": 200})
print(f"Filtered status: {resp5.status_code}")
print(f"Filtered products: {len(resp5.json().get('products', []))}")
