"""Phase 6B seed — create 5 demo users with the canonical DevSeed123! password."""
import os
os.environ["APP_ENV"] = "test"

# Use raw SQL via engine to avoid ORM mapper issues
from infrastructure.database.database import engine
from infrastructure.utils.auth import get_password_hash
from sqlalchemy import text

DEMO_USERS = [
    ("admin@zozi.com", "admin", "DevSeed123!"),
    ("supplier@zozi.com", "supplier", "DevSeed123!"),
    ("customer@zozi.com", "customer", "DevSeed123!"),
    ("employee@zozi.com", "employee", "DevSeed123!"),
    ("logistics@zozi.com", "logistics", "DevSeed123!"),
]

with engine.begin() as conn:
    for email, role, password in DEMO_USERS:
        hashed = get_password_hash(password)
        # Check if exists
        existing = conn.execute(text("SELECT id, hashed_password FROM accounts.users WHERE email = :email"), {"email": email}).first()
        if existing:
            print(f"UPDATE {email}: id={existing.id}")
            conn.execute(
                text("""UPDATE accounts.users
                       SET hashed_password=:hp, role=:role, country_code='AE', is_active=true, email_verified=true
                       WHERE email=:email"""),
                {"hp": hashed, "role": role, "email": email},
            )
        else:
            print(f"INSERT {email}")
            conn.execute(
                text("""INSERT INTO accounts.users
                       (email, hashed_password, full_name, role, country_code, is_active, email_verified, is_deleted, created_at, updated_at)
                       VALUES (:email, :hp, :full_name, :role, 'AE', true, true, false, NOW(), NOW())"""),
                {"email": email, "hp": hashed, "full_name": role.capitalize(), "role": role},
            )

# Verify
with engine.connect() as conn:
    res = conn.execute(text("SELECT email, role, country_code, is_active, email_verified, substring(coalesce(hashed_password,'') from 1 for 12) FROM accounts.users ORDER BY id"))
    print("\nFINAL accounts.users:")
    for r in res.fetchall():
        print(f"  {r}")