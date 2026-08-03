import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

client.post('/auth/register', json={
    'email': 'coupon_admin@zozi.test',
    'username': 'coupon_admin',
    'password': 'CouponAdmin123!',
    'role': 'admin',
})
resp = client.post('/auth/login', data={'username': 'coupon_admin@zozi.test', 'password': 'CouponAdmin123!'})
print('login status', resp.status_code, resp.json())
headers = {'Authorization': f"Bearer {resp.json().get('access_token', '')}"}

resp2 = client.post('/coupons', json={'code': 'TESTDEAL20', 'discount_type': 'percent', 'discount_value': 20, 'min_order_amount': 50, 'is_active': True}, headers=headers)
print('/coupons create', resp2.status_code, resp2.json())

client.post('/auth/register', json={'email': 'coupon_cust@zozi.test', 'username': 'coupon_cust', 'password': 'CouponPass123!', 'role': 'customer'})
resp3 = client.post('/auth/login', data={'username': 'coupon_cust@zozi.test', 'password': 'CouponPass123!'})
print('cust login', resp3.status_code, resp3.json())
cust_headers = {'Authorization': f"Bearer {resp3.json().get('access_token', '')}"}

val1 = client.post('/coupons/validate', json={'code': 'TESTDEAL20', 'order_total': 10}, headers=cust_headers)
print('/coupons/validate low', val1.status_code, val1.json())
val2 = client.post('/coupons/validate', json={'code': 'TESTDEAL20', 'order_total': 100}, headers=cust_headers)
print('/coupons/validate ok', val2.status_code, val2.json())
