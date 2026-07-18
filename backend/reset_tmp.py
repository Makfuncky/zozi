import sys, time, os
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///test_zozi.db"
os.environ["DEBUG"] = "false"
t0 = time.time()
from db.database import reset_tables, SessionLocal
print("imports OK", round(time.time()-t0,2), flush=True)
t1 = time.time()
reset_tables()
print("reset_tables OK", round(time.time()-t1,2), flush=True)
# try seeding role settings like lifespan
from controllers.admin_controller import load_role_permission_settings
db = SessionLocal()
load_role_permission_settings(db)
db.close()
print("role settings OK", round(time.time()-t1,2), flush=True)
# now run a fastapi testclient request that hits a DB route
from fastapi.testclient import TestClient
from main import app
c = TestClient(app, raise_server_exceptions=False)
r = c.get("/payments/methods")
print("methods", r.status_code, r.text[:200], flush=True)
print("TOTAL", round(time.time()-t0,2), flush=True)

