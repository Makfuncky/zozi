import sys
sys.path.insert(0, r'D:\Projects\10- E-COMMERCE WEBSITE\zozi')
import os
os.environ['APP_ENV'] = 'test'
os.environ['SECRET_KEY'] = ''
os.environ['FIELD_ENCRYPTION_KEY'] = ''
os.environ['AUDIT_CHAIN_KEY'] = ''
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app)
with patch('infrastructure.valkey.client.get_valkey', return_value=None):
    resp = client.get('/health/ready')
    assert resp.status_code == 503, resp.text
    data = resp.json()
    assert data['ready'] is False
    assert 'valkey' in data['blocking_dependencies']
