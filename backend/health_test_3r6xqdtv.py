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
resp = client.get('/health/deps')
assert resp.status_code == 200, resp.text
data = resp.json()
deps = data.get('dependencies', {})
assert 'circuit_breakers' in deps
assert isinstance(deps['circuit_breakers'], dict)
