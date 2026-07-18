import sys, time, os
sys.path.insert(0, os.path.dirname(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"))
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///test_zozi.db"
t0 = time.time()
print("importing main...", flush=True)
from main import app
print("MAIN OK", round(time.time()-t0,2), flush=True)

