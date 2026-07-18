"""
Recovery script Phase 3: Rebuild main.py and requirements.txt
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(BASE)

def write_file(rel_path, content):
    fp = os.path.join(PROJECT, rel_path)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  RESTORED: {rel_path}")


# ============================================================
# backend/main.py
# ============================================================
write_file("backend/main.py", '''\
"""ZOZI Marketplace - FastAPI application entry point."""
from contextlib import asynccontextmanager
import logging, os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db.database import Base, engine
from utils.config import settings

logger = logging.getLogger("zozi")


# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")
    yield


# ─── App factory ──────────────────────────────────────────────
app = FastAPI(
    title="ZOZI Marketplace API",
    version="1.0.0",
    description="Multi-vendor e-commerce platform API",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static files ─────────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# ─── Router registration ─────────────────────────────────────
PREFIX = "/api/v1"

from routers import (
    auth, users, addresses, cart, orders, payments,
    shipments, reviews, wishlist, notifications,
    coupons, banners, flash_sales, tickets, returns,
    search, upload, referrals, chatbot, ai_image,
    admin_users, admin_products, admin_orders, admin_commission,
    admin_email, admin_logistics, admin_settings, admin_cash,
    admin_analytics, admin_payouts,
    supplier_profile, supplier_products, supplier_orders,
    supplier_payouts, supplier_documents, supplier_analytics,
    logistics_orders, logistics_partner,
)

# Also import product/category routers if they exist
try:
    from routers import products
    app.include_router(products.router, prefix=f"{PREFIX}/products", tags=["Products"])
except (ImportError, AttributeError):
    pass

try:
    from routers import categories
    app.include_router(categories.router, prefix=f"{PREFIX}/categories", tags=["Categories"])
except (ImportError, AttributeError):
    pass

# Public routers
app.include_router(auth.router, prefix=f"{PREFIX}/auth", tags=["Auth"])
app.include_router(users.router, prefix=f"{PREFIX}/users", tags=["Users"])
app.include_router(addresses.router, prefix=f"{PREFIX}/addresses", tags=["Addresses"])
app.include_router(cart.router, prefix=f"{PREFIX}/cart", tags=["Cart"])
app.include_router(orders.router, prefix=f"{PREFIX}/orders", tags=["Orders"])
app.include_router(payments.router, prefix=f"{PREFIX}/payments", tags=["Payments"])
app.include_router(shipments.router, prefix=f"{PREFIX}/shipments", tags=["Shipments"])
app.include_router(reviews.router, prefix=f"{PREFIX}/reviews", tags=["Reviews"])
app.include_router(wishlist.router, prefix=f"{PREFIX}/wishlist", tags=["Wishlist"])
app.include_router(notifications.router, prefix=f"{PREFIX}/notifications", tags=["Notifications"])
app.include_router(coupons.router, prefix=f"{PREFIX}/coupons", tags=["Coupons"])
app.include_router(banners.router, prefix=f"{PREFIX}/banners", tags=["Banners"])
app.include_router(flash_sales.router, prefix=f"{PREFIX}/flash-sales", tags=["Flash Sales"])
app.include_router(tickets.router, prefix=f"{PREFIX}/tickets", tags=["Support"])
app.include_router(returns.router, prefix=f"{PREFIX}/returns", tags=["Returns"])
app.include_router(search.router, prefix=f"{PREFIX}/search", tags=["Search"])
app.include_router(upload.router, prefix=f"{PREFIX}/upload", tags=["Upload"])
app.include_router(referrals.router, prefix=f"{PREFIX}/referrals", tags=["Referrals"])
app.include_router(chatbot.router, prefix=f"{PREFIX}/chatbot", tags=["Chatbot"])
app.include_router(ai_image.router, prefix=f"{PREFIX}/ai-image", tags=["AI Image"])

# Admin routers
app.include_router(admin_users.router, prefix=f"{PREFIX}/admin/users", tags=["Admin"])
app.include_router(admin_products.router, prefix=f"{PREFIX}/admin/products", tags=["Admin"])
app.include_router(admin_orders.router, prefix=f"{PREFIX}/admin/orders", tags=["Admin"])
app.include_router(admin_commission.router, prefix=f"{PREFIX}/admin/commission", tags=["Admin"])
app.include_router(admin_email.router, prefix=f"{PREFIX}/admin/email", tags=["Admin"])
app.include_router(admin_logistics.router, prefix=f"{PREFIX}/admin/logistics", tags=["Admin"])
app.include_router(admin_settings.router, prefix=f"{PREFIX}/admin/settings", tags=["Admin"])
app.include_router(admin_cash.router, prefix=f"{PREFIX}/admin/cash", tags=["Admin"])
app.include_router(admin_analytics.router, prefix=f"{PREFIX}/admin/analytics", tags=["Admin"])
app.include_router(admin_payouts.router, prefix=f"{PREFIX}/admin/payouts", tags=["Admin"])

# Supplier routers
app.include_router(supplier_profile.router, prefix=f"{PREFIX}/supplier/profile", tags=["Supplier"])
app.include_router(supplier_products.router, prefix=f"{PREFIX}/supplier/products", tags=["Supplier"])
app.include_router(supplier_orders.router, prefix=f"{PREFIX}/supplier/orders", tags=["Supplier"])
app.include_router(supplier_payouts.router, prefix=f"{PREFIX}/supplier/payouts", tags=["Supplier"])
app.include_router(supplier_documents.router, prefix=f"{PREFIX}/supplier/documents", tags=["Supplier"])
app.include_router(supplier_analytics.router, prefix=f"{PREFIX}/supplier/analytics", tags=["Supplier"])

# Logistics routers
app.include_router(logistics_orders.router, prefix=f"{PREFIX}/logistics/orders", tags=["Logistics"])
app.include_router(logistics_partner.router, prefix=f"{PREFIX}/logistics/partner", tags=["Logistics"])


# ─── Health check ─────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to ZOZI Marketplace API", "docs": "/docs"}
''')


# ============================================================
# backend/requirements.txt
# ============================================================
write_file("backend/requirements.txt", '''\
# ZOZI Marketplace - Python Dependencies
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
pydantic[email]>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9
python-dotenv>=1.0.0
stripe>=7.0.0
openai>=1.0.0
httpx>=0.27.0
aiofiles>=24.0.0
Pillow>=10.0.0
jinja2>=3.1.0
itsdangerous>=2.1.0
email-validator>=2.1.0
requests>=2.31.0
python-dateutil>=2.9.0
slowapi>=0.1.9
''')


# ============================================================
# backend/.env (template - won't overwrite if exists)
# ============================================================
env_path = os.path.join(PROJECT, "backend", ".env")
if not os.path.exists(env_path) or os.path.getsize(env_path) == 0:
    write_file("backend/.env", '''\
# ZOZI Marketplace Environment Variables
SECRET_KEY=change-me-in-production-use-a-long-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=sqlite:///./zozi.db

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Stripe
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder

# SMTP Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
FROM_EMAIL=noreply@zozi.com

# OpenAI
OPENAI_API_KEY=

# Uploads
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=10485760

# App
APP_NAME=ZOZI Marketplace
APP_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
''')
else:
    print(f"  SKIPPED: backend/.env (already exists)")


# ============================================================
# backend/db/__init__.py
# ============================================================
write_file("backend/db/__init__.py", '"""Database package."""\n')


# ============================================================
# backend/utils/__init__.py
# ============================================================
write_file("backend/utils/__init__.py", '"""Utilities package."""\n')


# ============================================================
# backend/controllers/__init__.py
# ============================================================
write_file("backend/controllers/__init__.py", '"""Controllers package."""\n')


# ============================================================
# backend/services/__init__.py
# ============================================================
write_file("backend/services/__init__.py", '"""Services package."""\n')


print("\n=== Phase 3: main.py, requirements.txt, .env restored ===")
