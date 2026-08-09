"""
Seed realistic user data — admin, suppliers, customers, and logistics partners.

Usage:
    cd backend && python seed_users.py

Required environment variables:
    SEED_ADMIN_PASSWORD - Password for admin user
    SEED_SUPPLIER_PASSWORD - Password for supplier users
    SEED_CUSTOMER_PASSWORD - Password for customer users
    SEED_LOGISTICS_PASSWORD - Password for logistics partner users
"""

import sys
import os
import logging
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from db.database import SessionLocal
from models.user import User
from utils.auth import get_password_hash

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("seed_users")


def _get_seed_password(env_key: str) -> str:
    value = os.getenv(env_key)
    if not value:
        raise ValueError(
            f"Seed password environment variable {env_key} is not set. "
            "Set it before running seed in any environment."
        )
    return value


# ── Seed data ──────────────────────────────────────────────────────────────

USERS = [
    # ── Admin ─────────────────────────────────────────────────────────────
    {
        "email": "admin@zozi.com",
        "username": "admin",
        "full_name": "ZOZI Administrator",
        "role": "admin",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "AE",
        "preferred_currency": "AED",
    },
    # ── Suppliers ─────────────────────────────────────────────────────────
    {
        "email": "supplier@zozi.com",
        "username": "supplier",
        "full_name": "TechGadgets Store",
        "role": "supplier",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "AE",
        "preferred_currency": "AED",
    },
    {
        "email": "fashion.supplier@zozi.com",
        "username": "fashion_house",
        "full_name": "Fashion House International",
        "role": "supplier",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "AE",
        "preferred_currency": "AED",
    },
    {
        "email": "home.supplier@zozi.com",
        "username": "home_living",
        "full_name": "Home & Living Co.",
        "role": "supplier",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "SA",
        "preferred_currency": "SAR",
    },
    {
        "email": "beauty.supplier@zozi.com",
        "username": "beauty_parlour",
        "full_name": "Beauty Essentials",
        "role": "supplier",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "OM",
        "preferred_currency": "OMR",
    },
    # ── Customers ─────────────────────────────────────────────────────────
    {
        "email": "customer@zozi.com",
        "username": "customer",
        "full_name": "Ahmed Al-Rashid",
        "role": "customer",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "AE",
        "preferred_currency": "AED",
    },
    {
        "email": "sara@customer.com",
        "username": "sara_omani",
        "full_name": "Sara Al-Balushi",
        "role": "customer",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "OM",
        "preferred_currency": "OMR",
    },
    {
        "email": "mohammed@customer.com",
        "username": "mohammed_ksa",
        "full_name": "Mohammed Al-Saud",
        "role": "customer",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "SA",
        "preferred_currency": "SAR",
    },
    {
        "email": "fatima@customer.com",
        "username": "fatima_uae",
        "full_name": "Fatima Al-Maktoum",
        "role": "customer",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "AE",
        "preferred_currency": "AED",
    },
    {
        "email": "khalid@customer.com",
        "username": "khalid_bahrain",
        "full_name": "Khalid Al-Khalifa",
        "role": "customer",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "BH",
        "preferred_currency": "BHD",
    },
    # ── Logistics Partners ─────────────────────────────────────────────────
    {
        "email": "logistics@zozi.com",
        "username": "logistics",
        "full_name": "ZOZI Express Logistics",
        "role": "logistics_partner",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "AE",
        "preferred_currency": "AED",
    },
    {
        "email": "fast.delivery@zozi.com",
        "username": "fast_delivery",
        "full_name": "Fast Delivery Services",
        "role": "logistics_partner",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "SA",
        "preferred_currency": "SAR",
    },
    {
        "email": "gulf.shipping@zozi.com",
        "username": "gulf_shipping",
        "full_name": "Gulf Shipping Solutions",
        "role": "logistics_partner",
        "is_active": True,
        "email_verified": True,
        "is_verified": True,
        "preferred_country": "OM",
        "preferred_currency": "OMR",
    },
]


# Valid roles per the DB CHECK constraint
VALID_ROLES = {"customer", "supplier", "admin", "employee", "logistics_partner"}

_ROLE_PASSWORD_ENV = {
    "admin": "SEED_ADMIN_PASSWORD",
    "supplier": "SEED_SUPPLIER_PASSWORD",
    "customer": "SEED_CUSTOMER_PASSWORD",
    "logistics_partner": "SEED_LOGISTICS_PASSWORD",
    "employee": "SEED_EMPLOYEE_PASSWORD",
}


def seed():
    log.info("Seeding users...")
    created_count = 0
    skipped_count = 0
    db = SessionLocal()
    try:
        for user_data in USERS:
            try:
                existing = db.query(User).filter(User.email == user_data["email"]).first()
                if existing:
                    log.info(f"  ✓ User already exists: {user_data['email']}")
                    skipped_count += 1
                    continue

                role = user_data["role"]
                if role not in VALID_ROLES:
                    log.warning(f"  ⚠ Role '{role}' not in DB constraint — mapping to 'employee'")
                    role = "employee"

                password_env = _ROLE_PASSWORD_ENV.get(role)
                if not password_env:
                    log.warning(f"  ⚠ No password env var for role '{role}', skipping")
                    skipped_count += 1
                    continue

                password = _get_seed_password(password_env)

                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    full_name=user_data.get("full_name"),
                    hashed_password=get_password_hash(password),
                    role=role,
                    is_active=user_data.get("is_active", True),
                    email_verified=user_data.get("email_verified", False),
                    is_verified=user_data.get("is_verified", False),
                    preferred_country=user_data.get("preferred_country"),
                    preferred_currency=user_data.get("preferred_currency"),
                    created_at=datetime.now(timezone.utc) - timedelta(days=30),
                )
                db.add(user)
                db.commit()
                created_count += 1
                log.info(f"  + Created user: {user_data['email']} ({role})")

            except Exception as e:
                db.rollback()
                log.warning(f"  ⚠ Failed to create {user_data['email']}: {e}")
                skipped_count += 1
    finally:
        db.close()

    log.info(f"\n{'='*55}")
    log.info("User seeding complete!")
    log.info(f"  Created: {created_count} new users")
    log.info(f"  Existing/Skipped: {skipped_count} users")
    log.info(f"  Total: {len(USERS)} users")
    log.info(f"{'='*55}")


if __name__ == "__main__":
    seed()
