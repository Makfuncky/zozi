import main  # replicate server import order (avoids circular import)
from infrastructure.database.database import SessionLocal
from infrastructure.utils.auth import verify_password
from domains.accounts.models.user import User

db = SessionLocal()
u = db.query(User).filter_by(email="admin@zozi.com").first()
print("user found:", bool(u))
if u:
    print("hashed[:30]:", (u.hashed_password or "")[:30])
    print("verify admin123:", verify_password("admin123", u.hashed_password or ""))
    print("verify admin123 (fresh hash):", verify_password("admin123", "x"))
    print("email_verified:", getattr(u, "email_verified", "MISSING"))
    print("is_active:", getattr(u, "is_active", "MISSING"))
db.close()
