import sys, time, os
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///test_zozi.db"
os.environ["DEBUG"] = "false"
t0 = time.time()
from fastapi.testclient import TestClient
from main import app
print("imports OK", round(time.time()-t0,2), flush=True)
t1 = time.time()
c = TestClient(app, raise_server_exceptions=False)
print("TestClient OK", round(time.time()-t1,2), flush=True)
r = c.get("/health")
print("health", r.status_code, round(time.time()-t1,2), flush=True)

