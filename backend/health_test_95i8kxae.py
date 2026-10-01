import sys
sys.path.insert(0, r'D:\Projects\10- E-COMMERCE WEBSITE\zozi')
import os
os.environ.setdefault('APP_ENV', 'test')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-health-tests-only')
from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app)
resp = client.get('/health')
assert resp.status_code == 200, resp.text
data = resp.json()
assert 'dependencies' in data
deps = data['dependencies']
assert 'database' in deps
assert 'redis' in deps
assert deps['database']['status'] in ('ok', 'failed')
assert deps['redis']['status'] in ('ok', 'unavailable')
