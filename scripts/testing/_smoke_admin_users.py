"""Smoke test: get_all_users enrichment with last_login + verification."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DATABASE_URL", "sqlite:///D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/zozi.db")
os.environ.setdefault("SECRET_KEY", "smoke-test-key-not-for-prod")
os.environ.setdefault("ALGORITHM", "HS256")

from db.database import SessionLocal
from controllers.admin_controller import get_all_users

db = SessionLocal()
try:
    users = get_all_users(db, limit=5, offset=0)
    print(f"get_all_users returned {len(users)} rows")
    for u in users[:3]:
        uname = getattr(u, "username", "?")
        ll = getattr(u, "last_login", "ATTR_MISSING")
        vs = getattr(u, "verification_status", "ATTR_MISSING")
        va = getattr(u, "verified_at", "ATTR_MISSING")
        print(f"  user={uname!r} last_login={ll} vs={vs} va={va}")
    print("ADMIN USERS SMOKE TEST PASSED")
finally:
    db.close()
