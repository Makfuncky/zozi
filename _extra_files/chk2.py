import os, sys
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("APP_ENV","test"); os.environ.setdefault("SECRET_KEY","t")
os.environ.setdefault("SEED_ADMIN_PASSWORD","a"); os.environ.setdefault("CSRF_DISABLED","true")
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

class Dummy:
    def __init__(self): self.id=1; self.name="x"

app = FastAPI()
@app.get("/orm", response_model=dict)
def orm(): return Dummy()

c = TestClient(app, raise_server_exceptions=False)
r = c.get("/orm")
print("STATUS:", r.status_code)
print("BODY:", r.text[:300])
