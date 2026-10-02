import sys
sys.path.insert(0, r'D:\Projects\10- E-COMMERCE WEBSITE\zozi')
import os
os.environ['APP_ENV'] = 'test'
os.environ['SECRET_KEY'] = ''
os.environ['FIELD_ENCRYPTION_KEY'] = ''
os.environ['AUDIT_CHAIN_KEY'] = ''
from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app)
resp = client.get('/health')
assert resp.status_code == 200, resp.text
data = resp.json()
assert 'dependencies' in data
deps = data['dependencies']
assert 'database' in deps
assert 'valkey' in deps
assert deps['database']['status'] in ('ok', 'failed')
assert deps['valkey']['status'] in ('ok', 'unavailable')
