import traceback
from infrastructure.database.database import get_db
from domains.accounts.services.auth.auth_service import json_login_user, LoginRequest
from fastapi import Response

db = next(get_db())
try:
    req = LoginRequest(email="admin@zozi.com", password="admin123")
    resp = Response()
    out = json_login_user(response=resp, login_data=req, db=db, request=None)
    print("OK", list(out.keys()))
except Exception as e:
    print("EXCEPTION:", type(e).__name__, e)
    traceback.print_exc()
finally:
    db.close()
