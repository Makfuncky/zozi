import os, sys
sys.path.insert(0, os.path.abspath("backend")); sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("APP_ENV","test"); os.environ.setdefault("SECRET_KEY","t")
os.environ.setdefault("SEED_ADMIN_PASSWORD","a"); os.environ.setdefault("CSRF_DISABLED","true")
from fastapi import FastAPI
from fastapi.testclient import TestClient
import routers.public_products_access as rp
app = FastAPI()
app.include_router(rp.router, prefix="/p")
# does FastAPI accept dict response_model with an ORM object?
from data.models import Product
print("router built OK; routes:", len(rp.router.routes))
