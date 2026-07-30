"""
Seed ALL dev database data — users, products, orders, communications, commissions.

This is the single entry point to populate the entire dev database with
realistic data across all domains. All seed data is inline for simplicity.

Usage:
    cd backend && python seed_all.py

Or with verbose output:
    cd backend && python seed_all.py --verbose
"""

import sys
import os
import time
import logging
import argparse
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

sys.path.insert(0, os.path.dirname(__file__))

from db.database import SessionLocal
from db.base import Base
from models.user import User
from models.products import Category, Product, ProductVariant, Review
from models.orders import Order, OrderItem
from models.core import (
    EntityChatThread, EntityChatMessage,
    DirectChatRoom, DirectChatMessage,
    GroupChatRoom, GroupChatMember, GroupChatMessage,
)
from models.employee_models import InternalEmail, EmailFolder, Employee
from models import CommissionCategoryRate, CommissionBadgeTier
from services.commission_engine import seed_defaults, get_global_config
from utils.auth import get_password_hash
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("seed_all")

# ── Configuration ──────────────────────────────────────────────────────────────

USERS = [
    {"email": "admin@zozi.com", "username": "admin", "full_name": "ZOZI Administrator",
     "role": "admin", "is_active": True, "email_verified": True, "is_verified": True,
     "preferred_country": "AE", "preferred_currency": "AED"},
    {"email": "supplier@zozi.com", "username": "supplier", "full_name": "TechGadgets Store",
     "role": "supplier", "is_active": True, "email_verified": True, "is_verified": True,
     "preferred_country": "AE", "preferred_currency": "AED"},
    {"email": "fashion.supplier@zozi.com", "username": "fashion_house",
     "full_name": "Fashion House International", "role": "supplier", "is_active": True,
     "email_verified": True, "is_verified": True, "preferred_country": "AE",
     "preferred_currency": "AED"},
    {"email": "home.supplier@zozi.com", "username": "home_living",
     "full_name": "Home & Living Co.", "role": "supplier", "is_active": True,
     "email_verified": True, "is_verified": True, "preferred_country": "SA",
     "preferred_currency": "SAR"},
    {"email": "beauty.supplier@zozi.com", "username": "beauty_parlour",
     "full_name": "Beauty Essentials", "role": "supplier", "is_active": True,
     "email_verified": True, "is_verified": True, "preferred_country": "OM",
     "preferred_currency": "OMR"},
    {"email": "customer@zozi.com", "username": "customer", "full_name": "Ahmed Al-Rashid",
     "role": "customer", "is_active": True, "email_verified": True, "is_verified": True,
     "preferred_country": "AE", "preferred_currency": "AED"},
    {"email": "sara@customer.com", "username": "sara_omani", "full_name": "Sara Al-Balushi",
     "role": "customer", "is_active": True, "email_verified": True, "is_verified": True,
     "preferred_country": "OM", "preferred_currency": "OMR"},
    {"email": "mohammed@customer.com", "username": "mohammed_ksa",
     "full_name": "Mohammed Al-Saud", "role": "customer", "is_active": True,
     "email_verified": True, "is_verified": True, "preferred_country": "SA",
     "preferred_currency": "SAR"},
    {"email": "fatima@customer.com", "username": "fatima_uae", "full_name": "Fatima Al-Maktoum",
     "role": "customer", "is_active": True, "email_verified": True, "is_verified": True,
     "preferred_country": "AE", "preferred_currency": "AED"},
    {"email": "khalid@customer.com", "username": "khalid_bahrain",
     "full_name": "Khalid Al-Khalifa", "role": "customer", "is_active": True,
     "email_verified": True, "is_verified": True, "preferred_country": "BH",
     "preferred_currency": "BHD"},
    {"email": "logistics@zozi.com", "username": "logistics",
     "full_name": "ZOZI Express Logistics", "role": "logistics_partner", "is_active": True,
     "email_verified": True, "is_verified": True, "preferred_country": "AE",
     "preferred_currency": "AED"},
    {"email": "fast.delivery@zozi.com", "username": "fast_delivery",
     "full_name": "Fast Delivery Services", "role": "logistics_partner", "is_active": True,
     "email_verified": True, "is_verified": True, "preferred_country": "SA",
     "preferred_currency": "SAR"},
    {"email": "gulf.shipping@zozi.com", "username": "gulf_shipping",
     "full_name": "Gulf Shipping Solutions", "role": "logistics_partner", "is_active": True,
     "email_verified": True, "is_verified": True, "preferred_country": "OM",
     "preferred_currency": "OMR"},
]

CATEGORIES = [
    {"name": "Electronics", "slug": "electronics", "description": "Phones, laptops, gadgets",
     "is_featured": True},
    {"name": "Fashion", "slug": "fashion", "description": "Clothing, shoes, accessories",
     "is_featured": True},
    {"name": "Home & Living", "slug": "home-living", "description": "Furniture, decor, kitchen",
     "is_featured": True},
    {"name": "Beauty", "slug": "beauty", "description": "Skincare, makeup, fragrances",
     "is_featured": True},
    {"name": "Sports", "slug": "sports", "description": "Fitness, outdoor, sports gear",
     "is_featured": False},
    {"name": "Baby & Kids", "slug": "baby-kids", "description": "Toys, clothing, nursery",
     "is_featured": False},
    {"name": "Automotive", "slug": "automotive", "description": "Car parts, accessories",
     "is_featured": False},
    {"name": "Books", "slug": "books", "description": "Fiction, non-fiction, academic",
     "is_featured": False},
    {"name": "Grocery", "slug": "grocery", "description": "Food, beverages, household",
     "is_featured": False},
    {"name": "Accessories", "slug": "accessories", "description": "Bags, watches, jewelry",
     "is_featured": True},
]

PRODUCTS = [
    {"name": "iPhone 15 Pro Max", "description": "Latest Apple iPhone with A17 Pro chip, titanium design, 48MP camera system",
     "price": 1199.99, "compare_price": 1299.99, "category": "Electronics", "brand": "Apple",
     "color": "Titanium Blue", "stock": 50, "sales_count": 342, "rating": 4.8},
    {"name": "Samsung Galaxy S24 Ultra", "description": "Galaxy AI-powered smartphone with S Pen, 200MP camera",
     "price": 1099.99, "compare_price": 1199.99, "category": "Electronics", "brand": "Samsung",
     "color": "Titanium Gray", "stock": 45, "sales_count": 289, "rating": 4.7},
    {"name": "MacBook Pro 14-inch M3", "description": "Apple M3 Pro chip, 18GB RAM, 512GB SSD, Liquid Retina XDR display",
     "price": 1999.99, "category": "Electronics", "brand": "Apple", "color": "Space Black",
     "stock": 25, "sales_count": 156, "rating": 4.9},
    {"name": "Sony WH-1000XM5 Headphones", "description": "Industry-leading noise cancellation, 30-hour battery, multipoint connection",
     "price": 349.99, "compare_price": 399.99, "category": "Electronics", "brand": "Sony",
     "color": "Black", "stock": 80, "sales_count": 445, "rating": 4.6},
    {"name": "iPad Air M2", "description": "11-inch Liquid Retina display, M2 chip, Touch ID",
     "price": 599.99, "category": "Electronics", "brand": "Apple", "color": "Purple",
     "stock": 35, "sales_count": 198, "rating": 4.7},
    {"name": "Nike Air Max 270", "description": "Max Air unit for unrivaled comfort, lightweight mesh upper",
     "price": 149.99, "category": "Fashion", "brand": "Nike", "color": "Black/White",
     "stock": 100, "sales_count": 823, "rating": 4.5},
    {"name": "Adidas Ultraboost 23", "description": "Responsive BOOST midsole, Primeknit+ upper",
     "price": 189.99, "compare_price": 219.99, "category": "Fashion", "brand": "Adidas",
     "color": "Core Black", "stock": 75, "sales_count": 456, "rating": 4.6},
    {"name": "Gucci GG Marmont Bag", "description": "Quilted leather, antique gold-toned hardware, chain strap",
     "price": 2450.00, "category": "Fashion", "brand": "Gucci", "color": "Black",
     "stock": 10, "sales_count": 23, "rating": 4.9},
    {"name": "IKEA KALLAX Shelf Unit", "description": "4x4 cube organizer, versatile storage, white finish",
     "price": 179.99, "category": "Home & Living", "brand": "IKEA", "color": "White",
     "stock": 30, "sales_count": 345, "rating": 4.3},
    {"name": "Dyson V15 Detect Vacuum", "description": "Laser dust detection, 60min runtime, HEPA filtration",
     "price": 749.99, "compare_price": 849.99, "category": "Home & Living", "brand": "Dyson",
     "color": "Yellow/Nickel", "stock": 20, "sales_count": 123, "rating": 4.8},
    {"name": "Chanel No. 5 Eau de Parfum", "description": "Iconic floral aldehyde fragrance, 100ml",
     "price": 145.00, "category": "Beauty", "brand": "Chanel", "color": "Clear",
     "stock": 25, "sales_count": 189, "rating": 4.8},
    {"name": "La Mer Moisturizing Cream", "description": "Miracle Broth, ultra-rich, 60ml",
     "price": 380.00, "category": "Beauty", "brand": "La Mer", "color": "White",
     "stock": 12, "sales_count": 67, "rating": 4.9},
    {"name": "Peloton Bike+", "description": "23.8\" rotating HD touchscreen, auto-follow resistance",
     "price": 2495.00, "compare_price": 2795.00, "category": "Sports", "brand": "Peloton",
     "color": "Black", "stock": 5, "sales_count": 34, "rating": 4.6},
    {"name": "Apple Watch Series 9", "description": "Always-on Retina display, S9 chip, double tap gesture",
     "price": 399.99, "category": "Accessories", "brand": "Apple", "color": "Midnight",
     "stock": 60, "sales_count": 456, "rating": 4.7},
]

ORDER_STATUSES = ["pending", "processing", "confirmed", "shipped", "in_transit", "delivered", "cancelled"]
PAYMENT_STATUSES = ["pending", "completed", "failed", "refunded"]
PAYMENT_METHODS = ["credit_card", "debit_card", "apple_pay", "cod", "bank_transfer"]
CURRENCIES = ["AED", "SAR", "OMR", "USD", "BHD"]
SHIPPING_ADDRESSES = [
    "Al Majaz, Sharjah, UAE", "Dubai Marina, Dubai, UAE",
    "Al Khuwair, Muscat, Oman", "King Fahd Road, Riyadh, Saudi Arabia",
    "Manama, Bahrain", "Abu Dhabi, UAE", "Jeddah, Saudi Arabia", "Salalah, Oman",
]

ENTITY_THREADS = [
    {
        "title": "Q4 Budget Review — Finance Team",
        "entity_type": "admin", "entity_id": 1,
        "messages": [
            (1, "Team, please review the attached Q4 budget draft before Friday.", 72),
            (2, "I've reviewed the marketing line items — they look reasonable but we might need to adjust the ad spend.", 70),
            (1, "Good catch. Can you prepare a revised breakdown by region?", 68),
            (2, "Sure, I'll have it ready by tomorrow EOD.", 67),
            (3, "Customer support headcount request is included, right?", 65),
            (1, "Yes, it's in the ops section. We're approving 3 new hires.", 64),
            (2, "Here's the revised breakdown: Eastern region needs +15%, Western stays flat.", 48),
            (1, "Looks good. Let's finalize in tomorrow's standup.", 46),
        ],
    },
    {
        "title": "Product Launch — ZoziPay Integration",
        "entity_type": "admin", "entity_id": 2,
        "messages": [
            (1, "Heads up: ZoziPay integration is targeting Nov 15 launch. We need to align comms.", 96),
            (3, "Marketing collateral is ready — landing page, explainer video, email sequence.", 94),
            (2, "Engineering confirmed the API is stable. We're in final QA.", 92),
            (1, "Let's schedule a dry run with 10 beta users next week.", 90),
            (3, "I'll set up the beta cohort. Mostly power users from the UAE region.", 89),
            (1, "Perfect. Loop in the support team for the beta.", 87),
            (2, "QA passed 98%. One minor bug in the notification service — being patched today.", 48),
            (1, "Excellent. Go status for Nov 15 confirmed. Great work everyone.", 46),
        ],
    },
]

DIRECT_CONVERSATIONS = [
    {"p1": 1, "p2": 2,
     "messages": [
         (1, "Hey, the new product listings are live. Can you review?", 48),
         (2, "Looking now. The electronics category looks good. Fashion needs better images.", 47),
         (2, "Agreed. I'll ask the vendor to resubmit those.", 46),
         (1, "Also, the pricing on item #4401 seems off — double-check?", 44),
         (2, "You're right. Fixed it. Was a currency conversion error.", 43),
         (1, "Great. Everything else is approved. Pushing live.", 42),
     ]},
    {"p1": 1, "p2": 3,
     "messages": [
         (3, "Hi! I'm having trouble with my recent order — it hasn't shipped yet.", 24),
         (1, "Let me check. Order #ZO-48123, right?", 23),
         (3, "Yes, that's the one. It's been 4 days.", 22),
         (1, "I see the issue — the payment gateway flagged it for review. Let me clear it manually.", 21),
         (3, "Thank you! I really appreciate the quick help.", 20),
         (1, "Done. It's released now. You'll get the tracking number within the hour.", 19),
     ]},
]

GROUP_CONVERSATIONS = [
    {"name": "Operations — All Hands", "created_by": 1, "members": [1, 2, 3, 4],
     "messages": [
         (1, "Team, great news — we hit our monthly target 3 days early!", 48),
         (2, "Amazing! Everyone's been working really hard on this.", 47),
         (3, "The new onboarding flow definitely helped conversion.", 46),
         (4, "Logistics was a bottleneck but we cleared it this week.", 45),
         (1, "Let's keep this momentum. Q4 targets are ambitious but achievable.", 44),
         (2, "Would it help if we brought the marketing push forward by a week?", 43),
         (1, "Yes — coordinate with the design team and go ahead.", 42),
     ]},
]

INTERNAL_EMAIL_DATA = [
    (1, 1, "Q4 OKR Review — Please Submit by Friday",
     "Hi team,\n\nPlease submit your Q4 OKRs by end of day Friday.\n\nWe'll review them in Monday's all-hands.\n\nBest,\nAdmin", 96),
    (1, 1, "New Compliance Training — Mandatory",
     "All staff are required to complete the new data privacy compliance training.\n\nThe training takes approximately 45 minutes.\n\nRegards,\nCompliance Team", 72),
    (1, 1, "Updated Vendor Agreement — Signature Required",
     "The new vendor agreement terms have been updated.\n\nKey changes:\n- Payment terms: Net 30 to Net 15\n- SLA response time: 4 hours to 2 hours\n- Added data processing addendum\n\nPlease review and sign by end of week.", 24),
    (1, 2, "New Product Listing Guidelines — Q4 Update",
     "Dear Supplier,\n\nPlease review the updated product listing guidelines for Q4.\n\nKey changes:\n- Image resolution minimum: 1200x1200\n- Mandatory variant data for electronics\n- New prohibited items list attached\n\nPlease ensure all listings comply by Nov 1st.\n\nRegards,\nZozi Marketplace Team", 120),
    (1, 2, "Invoice #INV-2024-08921 — Payment Processed",
     "Your invoice INV-2024-08921 for $12,450.00 has been processed.\n\nExpected settlement: 3-5 business days.\n\nView details in your Supplier Dashboard.\n\nThanks,\nAccounts Payable", 36),
    (1, 3, "Your Order ZO-48123 Has Shipped!",
     "Great news! Your order ZO-48123 has shipped and is on its way.\n\nTracking number: ZO-TRK-7739201\nEstimated delivery: 3-5 business days\n\nTrack your package: http://zozi.com/track/ZO-TRK-7739201\n\nThank you for shopping with Zozi!", 48),
    (1, 4, "Weekly Route Optimization Report",
     "Here's the weekly route optimization summary:\n\n- Total deliveries: 1,842\n- On-time rate: 94.2%\n- Average transit time: 2.3 hours\n- Optimized routes saved 128 driving hours\n\nTop improvement area: Muscat morning routes (-12% efficiency).\n\nKeep up the great work!\n\nZozi Operations", 48),
]

_ROLE_PASSWORD_ENV = {
    "admin": "SEED_ADMIN_PASSWORD",
    "supplier": "SEED_SUPPLIER_PASSWORD",
    "customer": "SEED_CUSTOMER_PASSWORD",
    "logistics_partner": "SEED_LOGISTICS_PASSWORD",
    "employee": "SEED_EMPLOYEE_PASSWORD",
}

VALID_ROLES = {"customer", "supplier", "admin", "employee", "logistics_partner"}


def _get_seed_password(env_key: str) -> str:
    value = os.getenv(env_key)
    if not value:
        raise ValueError(
            f"Seed password environment variable {env_key} is not set. "
            "Set it before running seed in any environment."
        )
    return value


def _wipe_data():
    """Wipe existing seed data for a fresh start."""
    db = SessionLocal()
    try:
        tables = [
            "internal_emails", "email_folders", "employees",
            "group_chat_messages", "group_chat_members", "group_chat_rooms",
            "direct_chat_messages", "direct_chat_rooms",
            "entity_chat_messages", "entity_chat_threads",
            "order_items", "orders",
            "reviews", "products", "categories",
        ]
        for table in tables:
            try:
                db.execute(text(f"DELETE FROM {table}"))
            except Exception:
                pass
        db.commit()
        log.info("  ✅ Existing data wiped")
    except Exception as e:
        log.error(f"  ❌ Wipe failed: {e}")
        db.rollback()
    finally:
        db.close()


def seed_users():
    """Seed users (admin, suppliers, customers, logistics partners)."""
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
                    created_at=datetime.utcnow() - timedelta(days=30),
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


def seed_products():
    """Seed categories, products, and reviews."""
    db = SessionLocal()
    try:
        log.info("Seeding categories...")
        category_map = {}
        for cat_data in CATEGORIES:
            existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if existing:
                category_map[cat_data["name"]] = existing.id
                log.info(f"  ✓ Category exists: {cat_data['name']}")
                continue
            cat = Category(
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data.get("description"),
                is_featured=cat_data.get("is_featured", False),
                is_active=True,
            )
            db.add(cat)
            db.flush()
            category_map[cat_data["name"]] = cat.id
            log.info(f"  + Created category: {cat_data['name']}")

        db.commit()

        suppliers = db.query(User).filter(User.role == "supplier").all()
        if not suppliers:
            log.warning("No suppliers found! Run seed_users first.")
            return
        supplier_ids = [s.id for s in suppliers]

        log.info(f"\nSeeding products...")
        created_count = 0
        for product_data in PRODUCTS:
            existing = db.query(Product).filter(Product.name == product_data["name"]).first()
            if existing:
                log.info(f"  ✓ Product exists: {product_data['name']}")
                continue

            category_id = category_map.get(product_data["category"])
            supplier_id = random.choice(supplier_ids)

            product = Product(
                name=product_data["name"],
                description=product_data["description"],
                price=Decimal(str(product_data["price"])),
                compare_price=Decimal(str(product_data["compare_price"])) if product_data.get("compare_price") else None,
                category=product_data["category"],
                category_id=category_id,
                brand=product_data.get("brand"),
                color=product_data.get("color"),
                stock=product_data.get("stock", 50),
                rating=Decimal(str(product_data.get("rating", 4.0))),
                sales_count=product_data.get("sales_count", 0),
                supplier_id=supplier_id,
                is_active=True,
                is_approved=True,
                is_deleted=False,
                image_url=f"https://via.placeholder.com/400x400?text={product_data['name'].replace(' ', '+')}",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            )
            db.add(product)
            created_count += 1
            log.info(f"  + Created product: {product_data['name']}")

        db.commit()

        log.info(f"\nSeeding reviews...")
        customers = db.query(User).filter(User.role == "customer").all()
        products = db.query(Product).all()

        review_count = 0
        if not customers:
            log.warning("  No customers found — skipping reviews")
        else:
            for product in products[:15]:
                existing_reviews = db.query(Review).filter(Review.product_id == product.id).count()
                if existing_reviews > 0:
                    continue

                num_reviews = random.randint(2, 5)
                for _ in range(num_reviews):
                    customer = random.choice(customers)
                    review = Review(
                        product_id=product.id,
                        user_id=customer.id,
                        rating=random.randint(3, 5),
                        title=random.choice(["Great product!", "Love it!", "Good value", "Excellent quality", "Highly recommended"]),
                        comment=random.choice([
                            "Amazing quality and fast delivery!",
                            "Very satisfied with my purchase.",
                            "Exactly as described. Would buy again.",
                            "Great value for the price.",
                            "Exceeded my expectations!",
                        ]),
                        is_approved=True,
                        is_verified_purchase=random.choice([True, True, False]),
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    )
                    db.add(review)
                    review_count += 1

            db.commit()

        log.info(f"\n{'='*55}")
        log.info(f"Product seeding complete!")
        log.info(f"  Categories: {len(category_map)}")
        log.info(f"  Products: {created_count} new")
        log.info(f"  Reviews: {review_count} new")
        log.info(f"{'='*55}")

    except Exception:
        log.exception("Seed failed")
        db.rollback()
        raise
    finally:
        db.close()


def seed_orders():
    """Seed orders and order items."""
    db = SessionLocal()
    try:
        log.info("Seeding orders...")

        customers = db.query(User).filter(User.role == "customer").all()
        suppliers = db.query(User).filter(User.role == "supplier").all()
        products = db.query(Product).filter(Product.is_active == True, Product.is_deleted == False).all()

        if not customers:
            log.warning("No customers found! Run seed_users first.")
            return
        if not products:
            log.warning("No products found! Run seed_products first.")
            return

        existing_count = db.query(Order).count()
        if existing_count > 0:
            log.info(f"  ✓ {existing_count} orders already exist. Skipping.")
            return

        created_count = 0
        item_count = 0

        for i in range(50):
            customer = random.choice(customers)
            num_items = random.randint(1, 5)
            order_items = random.sample(products, min(num_items, len(products)))

            subtotal = Decimal("0.00")
            items_data = []

            for product in order_items:
                qty = random.randint(1, 3)
                unit_price = Decimal(str(product.price))
                item_total = unit_price * qty
                subtotal += item_total
                items_data.append({
                    "product": product,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total_price": item_total,
                })

            shipping_fee = Decimal(str(random.choice([0, 5, 10, 15, 20])))
            tax_amount = subtotal * Decimal("0.05")
            total = subtotal + shipping_fee + tax_amount

            status = random.choice(ORDER_STATUSES)
            payment_status = "completed" if status in ["shipped", "in_transit", "delivered"] else random.choice(PAYMENT_STATUSES)

            order = Order(
                order_number=f"ZO-{random.randint(40000, 99999)}",
                user_id=customer.id,
                customer_id=customer.id,
                status=status,
                payment_status=payment_status,
                payment_method=random.choice(PAYMENT_METHODS),
                subtotal=subtotal,
                subtotal_amount=subtotal,
                shipping_fee=shipping_fee,
                shipping_amount=shipping_fee,
                tax_amount=tax_amount,
                vat_amount=tax_amount,
                total=total,
                total_amount=total,
                currency=random.choice(CURRENCIES),
                shipping_address=random.choice(SHIPPING_ADDRESSES),
                shipping_city=random.choice(["Dubai", "Sharjah", "Muscat", "Riyadh", "Manama"]),
                shipping_country=random.choice(["AE", "OM", "SA", "BH"]),
                tracking_number=f"ZO-TRK-{random.randint(100000, 999999)}" if status in ["shipped", "in_transit", "delivered"] else None,
                fraud_score=Decimal(str(round(random.uniform(0, 0.3), 2))),
                fraud_action="allow",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
            )
            db.add(order)
            db.flush()
            created_count += 1

            for item_data in items_data:
                product = item_data["product"]
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    supplier_id=product.supplier_id,
                    quantity=item_data["quantity"],
                    unit_price=item_data["unit_price"],
                    price=item_data["unit_price"],
                    total_price=item_data["total_price"],
                    product_name=product.name,
                    product_image=product.image_url,
                    selected_size=random.choice(["S", "M", "L", "XL", None]),
                    selected_color=product.color,
                )
                db.add(order_item)
                item_count += 1

        db.commit()

        log.info(f"\n{'='*55}")
        log.info(f"Order seeding complete!")
        log.info(f"  Orders: {created_count} new")
        log.info(f"  Order Items: {item_count} new")
        log.info(f"{'='*55}")

    except Exception:
        log.exception("Seed failed")
        db.rollback()
        raise
    finally:
        db.close()


def seed_comms():
    """Seed communication data (DMs, groups, emails)."""
    db = SessionLocal()
    try:
        log.info("Clearing existing communication seed data...")
        db.execute(text("DELETE FROM entity_chat_messages"))
        db.execute(text("DELETE FROM entity_chat_threads"))
        db.execute(text("DELETE FROM direct_chat_messages"))
        db.execute(text("DELETE FROM direct_chat_rooms"))
        db.execute(text("DELETE FROM group_chat_messages"))
        db.execute(text("DELETE FROM group_chat_members"))
        db.execute(text("DELETE FROM group_chat_rooms"))
        db.execute(text("DELETE FROM internal_emails"))
        db.commit()
        log.info("Cleared.\n")

        LOGIN_EMPLOYEES = [
            (1, "ADM-001", "Administration", "System Administrator"),
            (2, "SUP-001", "Supplier Management", "Vendor Relations"),
            (3, "CUS-001", "Customer Service", "Premium Support Agent"),
            (4, "LOG-001", "Logistics", "Fleet Operations Manager"),
        ]
        log.info("Ensuring Employee + EmailFolder for all users...")
        inbox_folders = {}
        for user_id, emp_code, dept, pos in LOGIN_EMPLOYEES:
            emp = db.query(Employee).filter(Employee.user_id == user_id).first()
            if not emp:
                emp = Employee(
                    user_id=user_id,
                    employee_code=emp_code,
                    department=dept,
                    position=pos,
                    employment_status="active",
                    hire_date=datetime.utcnow().date() - timedelta(days=365),
                )
                db.add(emp)
                db.flush()
                log.info(f"  Created Employee #{emp.id} for user_id={user_id} ({pos})")
            else:
                log.info(f"  Found Employee #{emp.id} for user_id={user_id}")

            folder = db.query(EmailFolder).filter(
                EmailFolder.employee_id == emp.id,
                EmailFolder.name == "inbox",
            ).first()
            if not folder:
                folder = EmailFolder(
                    employee_id=emp.id,
                    name="inbox",
                    folder_type="inbox",
                    is_system=True,
                    sort_order=0,
                )
                db.add(folder)
                db.flush()
                log.info(f"  Created 'inbox' folder #{folder.id} for user_id={user_id}")
            else:
                log.info(f"  Found 'inbox' folder #{folder.id} for user_id={user_id}")

            inbox_folders[user_id] = folder
        log.info("")

        log.info("Seeding entity chat threads...")
        for tdata in ENTITY_THREADS:
            thread = EntityChatThread(
                entity_type=tdata["entity_type"],
                entity_id=tdata["entity_id"],
                title=tdata["title"],
                is_active=True,
                created_at=datetime.utcnow() - timedelta(hours=tdata["messages"][0][2]),
            )
            db.add(thread)
            db.flush()

            for sender_id, msg, hours_ago in tdata["messages"]:
                db.add(EntityChatMessage(
                    thread_id=thread.id,
                    sender_id=sender_id,
                    message=msg,
                    message_type="text",
                    created_at=datetime.utcnow() - timedelta(hours=hours_ago),
                ))
            log.info(f"  Thread #{thread.id}: {tdata['title'][:55]}")

        log.info("\nSeeding direct messages...")
        for conv in DIRECT_CONVERSATIONS:
            p1, p2 = sorted([conv["p1"], conv["p2"]])
            room = DirectChatRoom(
                chat_id=f"dm_seed_{p1}_{p2}",
                participant_one=p1,
                participant_two=p2,
                country_code="AE",
                is_active=True,
                created_at=datetime.utcnow() - timedelta(hours=conv["messages"][0][2]),
            )
            db.add(room)
            db.flush()

            for sender_id, msg, hours_ago in conv["messages"]:
                db.add(DirectChatMessage(
                    room_id=room.id,
                    sender_id=sender_id,
                    message=msg,
                    message_type="text",
                    created_at=datetime.utcnow() - timedelta(hours=hours_ago),
                ))
            log.info(f"  DM between users {p1} <-> {p2}")

        log.info("\nSeeding group conversations...")
        for gdata in GROUP_CONVERSATIONS:
            slug = gdata["name"].lower().replace(" ", "_")[:20]
            room = GroupChatRoom(
                chat_id=f"grp_seed_{slug}",
                name=gdata["name"],
                is_active=True,
                created_by=gdata["created_by"],
                created_at=datetime.utcnow() - timedelta(hours=gdata["messages"][0][2]),
            )
            db.add(room)
            db.flush()

            for uid in gdata["members"]:
                db.add(GroupChatMember(
                    room_id=room.id,
                    user_id=uid,
                    role="admin" if uid == gdata["created_by"] else "member",
                ))

            for sender_id, msg, hours_ago in gdata["messages"]:
                db.add(GroupChatMessage(
                    room_id=room.id,
                    sender_id=sender_id,
                    message=msg,
                    message_type="text",
                    created_at=datetime.utcnow() - timedelta(hours=hours_ago),
                ))
            log.info(f"  Group: {gdata['name']}")

        log.info("\nSeeding internal emails...")
        email_count = 0
        email_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for sender_id, recipient_id, subject, body_text, hours_ago in INTERNAL_EMAIL_DATA:
            folder = inbox_folders.get(recipient_id)
            if not folder:
                log.warning(f"  Skipping email to user_id={recipient_id} — no inbox folder")
                continue

            email = InternalEmail(
                subject=subject,
                body_text=body_text,
                sender_id=sender_id,
                recipients=[{"user_id": recipient_id, "email": f"user{recipient_id}@zozi.com"}],
                folder_id=folder.id,
                is_read=False,
                thread_id=f"seed_thread_{hours_ago}_{recipient_id}",
                created_at=datetime.utcnow() - timedelta(hours=hours_ago),
            )
            db.add(email)
            email_count += 1
            email_counts[recipient_id] = email_counts.get(recipient_id, 0) + 1
            log.info(f"  Email to user_id={recipient_id}: {subject[:50]}")

        db.commit()
        msg_count = sum(len(t["messages"]) for t in ENTITY_THREADS)
        dm_count = sum(len(c["messages"]) for c in DIRECT_CONVERSATIONS)
        grp_count = sum(len(g["messages"]) for g in GROUP_CONVERSATIONS)
        total = msg_count + dm_count + grp_count + email_count
        log.info(f"\n{'='*55}")
        log.info(f"Communication data seeded successfully!")
        log.info(f"  {len(ENTITY_THREADS)} entity threads ({msg_count} messages)")
        log.info(f"  {len(DIRECT_CONVERSATIONS)} DM rooms ({dm_count} messages)")
        log.info(f"  {len(GROUP_CONVERSATIONS)} group chats ({grp_count} messages)")
        log.info(f"  {email_count} internal emails:")
        for uid in sorted(email_counts):
            if email_counts[uid] > 0:
                log.info(f"    - user_id={uid}: {email_counts[uid]} email(s)")
        log.info(f"  Total: {total} messages across all channels")
        log.info(f"{'='*55}")

    except Exception:
        log.exception("Seed failed")
        db.rollback()
        raise
    finally:
        db.close()


def seed_commission():
    """Seed commission defaults and badge tiers."""
    db = SessionLocal()
    try:
        seed_defaults(db)
        cfg = get_global_config(db)
        log.info(f"Commission config default_rate: {cfg.default_rate}")
        cats = db.query(CommissionCategoryRate).count()
        badges = db.query(CommissionBadgeTier).count()
        log.info(f"Category rates: {cats}, Badge tiers: {badges}")
    finally:
        db.close()
    log.info("Commission seeding complete!")


def main():
    parser = argparse.ArgumentParser(description="Seed the entire ZOZI dev database")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full tracebacks on failure")
    parser.add_argument("--skip", nargs="*", default=[], help="Modules to skip")
    parser.add_argument("--force", action="store_true", help="Wipe existing data before seeding")
    args = parser.parse_args()

    log.info(f"🚀 ZOZI Database Seeder — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    log.info(f"   Seeding all data in dependency order...\n")

    if args.force:
        log.info("⚠️  FORCE MODE: Wiping existing data before seeding...")
        _wipe_data()
        log.info("")

    results = []

    seeders = [
        ("users", "Users (admin, suppliers, customers, logistics)"),
        ("products", "Categories, Products, Variants, Reviews"),
        ("orders", "Orders, Order Items"),
        ("comms", "Communication data (DMs, groups, emails)"),
        ("commission", "Commission defaults"),
    ]

    for module_name, description in seeders:
        if module_name in args.skip:
            log.info(f"\n⏭  Skipping: {description}")
            results.append((module_name, description, True, 0.0))
            continue

        start = time.time()
        try:
            if module_name == "users":
                seed_users()
            elif module_name == "products":
                seed_products()
            elif module_name == "orders":
                seed_orders()
            elif module_name == "comms":
                seed_comms()
            elif module_name == "commission":
                seed_commission()

            elapsed = time.time() - start
            log.info(f"  ✅ {description} — completed in {elapsed:.1f}s")
            results.append((module_name, description, True, elapsed))

        except Exception as e:
            elapsed = time.time() - start
            log.error(f"  ❌ {description} — FAILED after {elapsed:.1f}s")
            log.error(f"     Error: {e}")
            if args.verbose:
                log.exception("     Full traceback:")
            results.append((module_name, description, False, elapsed))

            if module_name in ("users", "products"):
                log.error(f"\n⛔ Critical seeder '{module_name}' failed. Aborting remaining seeders.")
                break

    success_count = sum(1 for _, _, ok, _ in results if ok)
    fail_count = len(results) - success_count
    total_time = sum(t for _, _, _, t in results)

    log.info(f"\n{'═'*60}")
    log.info("📊 SEEDING SUMMARY")
    log.info(f"{'═'*60}")
    for module, desc, ok, elapsed in results:
        status = "✅" if ok else "❌"
        log.info(f"  {status} {desc:<45} {elapsed:>6.1f}s")
    log.info(f"{'─'*60}")
    log.info(f"  Total: {success_count}/{len(results)} succeeded  |  {total_time:.1f}s total")
    if fail_count > 0:
        log.info(f"  ⚠ {fail_count} seeder(s) failed — check logs above")
    else:
        log.info("  🎉 All seeders completed successfully!")
    log.info(f"{'═'*60}\n")

    if any(not ok for _, _, ok, _ in results):
        sys.exit(1)


if __name__ == "__main__":
    main()