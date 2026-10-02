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
import infrastructure.database.database as db_mod
client = TestClient(app)
patches = [
    patch.object(db_mod, 'check_connection_health', return_value=False),
    patch('infrastructure.valkey.client.get_valkey_health_status', return_value={'available': False}),
]
for p in patches:
    p.start()
try:
    resp = client.get('/health')
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data['status'] == 'degraded'
    assert data['dependencies']['database']['status'] == 'failed'
    assert data['dependencies']['valkey']['status'] == 'unavailable'
finally:
    for p in patches:
        p.stop()
