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
