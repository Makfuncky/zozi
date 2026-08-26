import json
import logging
import os
import re
import warnings
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from infrastructure.database.database import engine
from domains.governance.models.user import User
from domains.catalog.models.products import Category
from domains.catalog.models.products import Product
from domains.comms.models.marketing import EmailTemplate
from domains.comms.models.suppliers import SupplierProfile
from domains.country.models.countries import CountryConfig
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPartnerServiceArea
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.models.logistics import LogisticsVehicleRule
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import ShipmentEvent
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from domains.orders.models.orders import OrderLogisticsAllocation
from domains.hr.models.employee_models import (
def seed_data(session_factory: Callable[[], Session] | Session | None = None) -> None:
    _prepare_database_for_seed()
    if isinstance(session_factory, Session):
        db = session_factory
    else:
        db = (session_factory or SessionLocal)()
    try:
        _seed_countries(db)
        admin_user = _ensure_demo_user(
            db,
            email="admin@zozi.com",
            username="admin",
            password=_seed_password("SEED_ADMIN_PASSWORD"),
            role="admin",
            log_label="admin",
        )
        supplier_user = _ensure_demo_user(
            db,
            email="supplier@zozi.com",
            username="supplier",
            password=_seed_password("SEED_SUPPLIER_PASSWORD"),
            role="supplier",
            log_label="supplier",
        )
        customer_user = _ensure_demo_user(
            db,
            email="customer@zozi.com",
            username="customer",
            password=_seed_password("SEED_CUSTOMER_PASSWORD"),
            role="customer",
            log_label="customer",
        )
        logistics_user = _ensure_demo_user(
            db,
            email="logistics@zozi.com",
            username="logistics",
            password=_seed_password("SEED_LOGISTICS_PASSWORD"),
            role="logistics",
            log_label="logistics partner",
        )

        _ensure_demo_user(
            db,
            email="admin@test.com",
            username="admin_test",
            password=_seed_password("SEED_ADMIN_PASSWORD"),
            role="admin",
            log_label="test admin",
        )
        _ensure_demo_user(
            db,
            email="supplier@test.com",
            username="supplier_test",
            password=_seed_password("SEED_SUPPLIER_PASSWORD"),
            role="supplier",
            log_label="test supplier",
        )
        _ensure_demo_user(
            db,
            email="customer@test.com",
            username="customer_test",
            password=_seed_password("SEED_CUSTOMER_PASSWORD"),
            role="customer",
            log_label="test customer",
        )

        db.flush()
        supplier_id = supplier_user.id
        admin_id = admin_user.id
        logistics_user_id = logistics_user.id

        supplier_profile = _ensure_demo_supplier_profile(
            db,
            supplier_user=supplier_user,
        )

        logistics_partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == logistics_user_id).first()
        if not logistics_partner:
            logistics_partner = db.query(LogisticsPartner).filter(LogisticsPartner.code == "ZOZI-DEMO-LP").first()

        if not logistics_partner:
            logistics_partner = LogisticsPartner(
                name="ZOZI Logistics Demo",
                code="ZOZI-DEMO-LP",
                user_id=logistics_user_id,
            )
            db.add(logistics_partner)
            logger.info("Seeded default logistics partner profile")

        logistics_partner.name = "ZOZI Logistics Demo"
        logistics_partner.code = "ZOZI-DEMO-LP"
        logistics_partner.contact_name = "ZOZI Logistics Team"
        logistics_partner.contact_email = "logistics@zozi.com"
        logistics_partner.contact_phone = "+971500000111"
        logistics_partner.website = "https://logistics.zozi.local"
        logistics_partner.coverage_regions = json.dumps(["United Arab Emirates", "Saudi Arabia"])
        logistics_partner.service_types = json.dumps(["ground", "same_day"])
        logistics_partner.status = "active"
        logistics_partner.verification_status = "approved"
        logistics_partner.verification_note = "Seeded demo logistics partner approved for browser QA"
        logistics_partner.verified_by = admin_id
        logistics_partner.verified_at = _utcnow()
        logistics_partner.user_id = logistics_user_id

        db.flush()

        # Sample products
        products = [
            {
                "name": "Luxury Handbag",
                "description": "Premium leather handbag with gold accents",
                "price": 299.99,
                "category": "Fashion",
                "brand": "Gucci",
                "rating": 4.5,
                "image_url": "https://via.placeholder.com/300x200?text=Luxury+Handbag",
                "stock": 10,
                "color": "Black",
                "supplier_id": supplier_id,
                "is_approved": True
            },
            {
                "name": "Designer Watch",
                "description": "Elegant timepiece with diamond bezel",
                "price": 499.99,
                "category": "Accessories",
                "brand": "Rolex",
                "rating": 4.8,
                "image_url": "https://via.placeholder.com/300x200?text=Designer+Watch",
                "stock": 5,
                "color": "Gold",
                "supplier_id": supplier_id,
                "is_approved": True
            },
            {
                "name": "Silk Scarf",
                "description": "Soft silk scarf in vibrant colors",
                "price": 89.99,
                "category": "Fashion",
                "brand": "Hermes",
                "rating": 4.2,
                "image_url": "https://via.placeholder.com/300x200?text=Silk+Scarf",
                "stock": 20,
                "color": "Red",
                "supplier_id": supplier_id,
                "is_approved": True
            }
        ]

        # ── Categories ─────────────────────────────────────────────────────────────
        # Seed root categories that match the product categories above.
        # Picsum-sourced cover images are stable and look real in the UI.
        categories_data = [
            {"name": "Fashion",      "slug": "fashion",      "icon": "👗", "sort_order": 1,
             "image_url": "https://picsum.photos/seed/fashion/600/400"},
            {"name": "Accessories",  "slug": "accessories",  "icon": "💍", "sort_order": 2,
             "image_url": "https://picsum.photos/seed/accessories/600/400"},
            {"name": "Electronics",  "slug": "electronics",  "icon": "📱", "sort_order": 3,
             "image_url": "https://picsum.photos/seed/electronics/600/400"},
            {"name": "Beauty",       "slug": "beauty",       "icon": "💄", "sort_order": 4,
             "image_url": "https://picsum.photos/seed/beauty/600/400"},
            {"name": "Home & Living","slug": "home-living",  "icon": "🏠", "sort_order": 5,
             "image_url": "https://picsum.photos/seed/home/600/400"},
            {"name": "Sports",       "slug": "sports",       "icon": "⚽", "sort_order": 6,
             "image_url": "https://picsum.photos/seed/sports/600/400"},
            {"name": "Footwear",     "slug": "footwear",     "icon": "👟", "sort_order": 7,
             "image_url": "https://picsum.photos/seed/shoes/600/400"},
            {"name": "Watches",      "slug": "watches",      "icon": "⌚", "sort_order": 8,
             "image_url": "https://picsum.photos/seed/watches/600/400"},
              {"name": "General",      "slug": "general",      "icon": "📦", "sort_order": 9,
               "image_url": "https://picsum.photos/seed/general/600/400"},
              {"name": "Furniture",    "slug": "furniture",    "icon": "🛋️", "sort_order": 10,
               "image_url": "https://picsum.photos/seed/furniture/600/400"},
        ]
        for cat_data in categories_data:
            existing_cat = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing_cat:
                db.add(Category(is_active=True, **cat_data))
                logger.info("Seeded category: %s", cat_data["name"])
            else:
                for field, value in cat_data.items():
                    setattr(existing_cat, field, value)

        # ── Idempotent: only add products that don't already exist by name ─────
        # Also update any stale placeholder images with Picsum alternatives.
        # Products use `category` (VARCHAR) matching the category names above.
        extended_products = [
            {
                "name": "Luxury Handbag",
                "description": "Premium leather handbag with gold accents, perfect for any occasion.",
                "price": 299.99, "compare_price": 399.99,
                "category": "Fashion", "brand": "Luxury Edition",
                "rating": 4.5, "stock": 15, "color": "Black",
                "image_url": "https://picsum.photos/seed/handbag1/600/600",
                "supplier_id": supplier_id, "is_approved": True,
                "is_featured": True, "is_active": True,
            },
            {
                "name": "Designer Watch",
                "description": "Elegant Swiss-movement timepiece with sapphire crystal glass.",
                "price": 499.99, "compare_price": 699.99,
                "category": "Watches", "brand": "Chrono Elite",
                "rating": 4.8, "stock": 8, "color": "Gold",
                "image_url": "https://picsum.photos/seed/watch1/600/600",
                "supplier_id": supplier_id, "is_approved": True,
                "is_featured": True, "is_active": True, "is_hot": True,
            },
            {
                "name": "Silk Scarf",
                "description": "100% pure silk scarf with vibrant hand-painted pattern.",
                "price": 89.99, "compare_price": 129.99,
                "category": "Fashion", "brand": "Silk House",
                "rating": 4.2, "stock": 25, "color": "Red",
                "image_url": "https://picsum.photos/seed/scarf1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True,
            },
            {
                "name": "Wireless Noise-Cancelling Headphones",
                "description": "Premium over-ear headphones with 40-hour battery life and active noise cancellation.",
                "price": 349.99, "compare_price": 449.99,
                "category": "Electronics", "brand": "SoundMax",
                "rating": 4.7, "stock": 20, "color": "Midnight Black",
                "image_url": "https://picsum.photos/seed/headphones1/600/600",
                "supplier_id": supplier_id, "is_approved": True,
                "is_featured": True, "is_active": True, "is_new": True,
            },
            {
                "name": "Diamond Stud Earrings",
                "description": "0.5ct genuine diamond stud earrings in 18K white gold setting.",
                "price": 899.99, "compare_price": 1199.99,
                "category": "Accessories", "brand": "Diamond & Co",
                "rating": 4.9, "stock": 5, "color": "White Gold",
                "image_url": "https://picsum.photos/seed/earrings1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_hot": True,
            },
            {
                "name": "Premium Moisturizing Serum",
                "description": "Hyaluronic acid and vitamin C serum for radiant, youthful skin.",
                "price": 79.99, "compare_price": 109.99,
                "category": "Beauty", "brand": "GlowLab",
                "rating": 4.4, "stock": 40, "color": None,
                "image_url": "https://picsum.photos/seed/serum1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True,
            },
            {
                "name": "Ergonomic Office Chair",
                "description": "Height-adjustable mesh office chair with lumbar support and 5-year warranty.",
                "price": 599.99, "compare_price": 799.99,
                "category": "Home & Living", "brand": "ErgoSeat",
                "rating": 4.6, "stock": 10, "color": "Charcoal",
                "image_url": "https://picsum.photos/seed/chair1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True,
            },
            {
                "name": "Athletic Running Shoes",
                "description": "Lightweight, responsive foam midsole running shoes for marathon training.",
                "price": 149.99, "compare_price": 199.99,
                "category": "Footwear", "brand": "RunFast",
                "rating": 4.5, "stock": 30, "color": "Electric Blue",
                "image_url": "https://picsum.photos/seed/shoes1/600/600",
                "supplier_id": supplier_id, "is_approved": True,
                "is_active": True, "is_featured": True,
            },
            {
                "name": "Leather Bifold Wallet",
                "description": "Full-grain Italian leather wallet with RFID blocking, 8 card slots.",
                "price": 59.99, "compare_price": 89.99,
                "category": "Accessories", "brand": "Leather & Co",
                "rating": 4.3, "stock": 50, "color": "Brown",
                "image_url": "https://picsum.photos/seed/wallet1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True,
            },
            {
                "name": "Smart Fitness Tracker",
                "description": "24/7 heart rate monitoring, sleep tracking, GPS, and 7-day battery life.",
                "price": 199.99, "compare_price": 249.99,
                "category": "Electronics", "brand": "FitPulse",
                "rating": 4.4, "stock": 22, "color": "Graphite",
                "image_url": "https://picsum.photos/seed/tracker1/600/600",
                "supplier_id": supplier_id, "is_approved": True,
                "is_active": True, "is_new": True,
            },
            {
                "name": "Cashmere Pullover Sweater",
                "description": "100% pure cashmere v-neck sweater, ultra-soft and warm.",
                "price": 189.99, "compare_price": 259.99,
                "category": "Fashion", "brand": "Cashmere & Co",
                "rating": 4.6, "stock": 18, "color": "Camel",
                "image_url": "https://picsum.photos/seed/sweater1/600/600",
                "supplier_id": supplier_id, "is_approved": True,
                "is_active": True, "is_featured": True,
            },
            {
                "name": "Rose Gold Bangle Bracelet",
                "description": "18K rose gold plated bangle with cubic zirconia accent stones.",
                "price": 119.99, "compare_price": 169.99,
                "category": "Accessories", "brand": "Golden Touch",
                "rating": 4.5, "stock": 12, "color": "Rose Gold",
                "image_url": "https://picsum.photos/seed/bracelet1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True,
            },
            {
                "name": "Matte Liquid Lipstick Set",
                "description": "Long-lasting 12-hour formula, set of 6 classic shades, cruelty-free.",
                "price": 44.99, "compare_price": 69.99,
                "category": "Beauty", "brand": "ColorPop",
                "rating": 4.3, "stock": 60, "color": "Multi",
                "image_url": "https://picsum.photos/seed/lipstick1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True,
            },
            {
                "name": "Stainless Steel Water Bottle",
                "description": "1L triple-insulated bottle, keeps drinks cold 36h / hot 18h.",
                "price": 34.99, "compare_price": 49.99,
                "category": "Sports", "brand": "HydroMax",
                "rating": 4.7, "stock": 80, "color": "Midnight Blue",
                "image_url": "https://picsum.photos/seed/bottle1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True,
            },
            {
                "name": "Scented Soy Candle Set",
                "description": "Set of 3 hand-poured soy wax candles with essential oil fragrances.",
                "price": 49.99, "compare_price": 74.99,
                "category": "Home & Living", "brand": "ZenScents",
                "rating": 4.5, "stock": 35, "color": "Ivory",
                "image_url": "https://picsum.photos/seed/candle1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True,
            },
            {
                "name": "Leather Belt",
                "description": "Full-grain cowhide leather belt with antique brass buckle, sizes 30-44.",
                "price": 69.99, "compare_price": 99.99,
                "category": "Fashion", "brand": "BeltCraft",
                "rating": 4.4, "stock": 28, "color": "Dark Brown",
                "image_url": "https://picsum.photos/seed/belt1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True,
            },
            {
                "name": "Yoga Mat Premium",
                "description": "6mm thick non-slip TPE yoga mat with body alignment lines, eco-friendly.",
                "price": 59.99, "compare_price": 89.99,
                "category": "Sports", "brand": "ZenFlow",
                "rating": 4.6, "stock": 45, "color": "Purple",
                "image_url": "https://picsum.photos/seed/yogamat1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True,
            },
            {
                "name": "Ceramic Coffee Mug Set",
                "description": "Set of 4 handcrafted ceramic mugs, 350ml each, dishwasher-safe.",
                "price": 39.99, "compare_price": 59.99,
                "category": "Home & Living", "brand": "CeramicKind",
                "rating": 4.4, "stock": 55, "color": "Earth Tones",
                "image_url": "https://picsum.photos/seed/mug1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True,
            },
            {
                "name": "Snap-Back Baseball Cap",
                "description": "100% cotton twill 6-panel cap with adjustable snap closure.",
                "price": 29.99, "compare_price": 44.99,
                "category": "Fashion", "brand": "CapKing",
                "rating": 4.2, "stock": 70, "color": "Black / White",
                "image_url": "https://picsum.photos/seed/cap1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True,
            },
            {
                "name": "Portable Bluetooth Speaker",
                "description": "360° surround sound, waterproof IPX7, 12-hour battery, USB-C charging.",
                "price": 129.99, "compare_price": 179.99,
                "category": "Electronics", "brand": "SoundWave",
                "rating": 4.5, "stock": 18, "color": "Gunmetal",
                "image_url": "https://picsum.photos/seed/speaker1/600/600",
                "supplier_id": supplier_id, "is_approved": True,
                "is_active": True, "is_hot": True,
            },
            {
                "name": "Perfume Eau de Parfum",
                "description": "Floral-oriental fragrance with top notes of rose and jasmine, 100ml.",
                "price": 159.99, "compare_price": 219.99,
                "category": "Beauty", "brand": "Essence Royale",
                "rating": 4.7, "stock": 20, "color": None,
                "image_url": "https://picsum.photos/seed/perfume1/600/600",
                "supplier_id": supplier_id, "is_approved": True,
                "is_active": True, "is_featured": True,
            },
            {
                "name": "Slim Leather Backpack",
                "description": "15in laptop compartment, water-resistant coated canvas with leather trim.",
                "price": 179.99, "compare_price": 249.99,
                "category": "Fashion", "brand": "Urban Carry",
                "rating": 4.5, "stock": 14, "color": "Tan",
                "image_url": "https://picsum.photos/seed/backpack1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True,
            },
            {
                "name": "Stainless Steel Sunglasses",
                "description": "UV400 polarised lenses with lightweight stainless steel frame.",
                "price": 99.99, "compare_price": 139.99,
                "category": "Accessories", "brand": "OptiView",
                "rating": 4.3, "stock": 22, "color": "Gunmetal / Grey",
                "image_url": "https://picsum.photos/seed/glasses1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True,
            },
            {
                "name": "Resistance Band Set",
                "description": "Set of 5 loop bands (10–50 lbs) with mesh carry bag, latex-free.",
                "price": 24.99, "compare_price": 39.99,
                "category": "Sports", "brand": "FlexBand",
                "rating": 4.6, "stock": 100, "color": "Multi",
                "image_url": "https://picsum.photos/seed/bands1/600/600",
                "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True,
            },
            {
                "name": "Chef's Knife 8-inch",
                "description": "High-carbon German steel blade with full tang handle, razor-sharp edge.",
                "price": 89.99, "compare_price": 129.99,
                "category": "Home & Living", "brand": "BladeChef",
                "rating": 4.8, "stock": 25, "color": "Silver",
                "image_url": "https://picsum.photos/seed/knife1/600/600",
                "supplier_id": supplier_id, "is_approved": True,
                "is_active": True, "is_hot": True,
            },
        ]
        all_products = extended_products
        for product_data in all_products:
            _upsert_demo_product(db, product_data)

        demo_service_area = _ensure_demo_service_area(
            db,
            partner=logistics_partner,
            admin_id=admin_id,
        )
        db.flush()
        _ensure_demo_pricing_profile(
            db,
            partner=logistics_partner,
            service_area=demo_service_area,
            admin_id=admin_id,
        )
        _ensure_demo_vehicle_rule(
            db,
            partner=logistics_partner,
            service_area=demo_service_area,
            admin_id=admin_id,
            vehicle_type="car",
            max_weight_kg="10.00",
            cost_multiplier="1.0000",
            priority_rank=10,
        )
        _ensure_demo_vehicle_rule(
            db,
            partner=logistics_partner,
            service_area=demo_service_area,
            admin_id=admin_id,
            vehicle_type="van",
            max_weight_kg="25.00",
            cost_multiplier="1.2000",
            priority_rank=20,
        )
        db.flush()
        _ensure_demo_pickup_ready_shipment(
            db,
            admin_user=admin_user,
            customer_user=customer_user,
            supplier_user=supplier_user,
            logistics_partner=logistics_partner,
            service_area=demo_service_area,
        )

        # Email templates for promotional campaigns
        email_templates = [
            {
                "name": "Welcome Series - New Customer",
                "subject": "Welcome to ZOZI - Your Fashion Journey Begins!",
                "html_content": """
<p>We're thrilled to have you join the ZOZI community! As a token of our appreciation, here's <strong>10% off</strong> your first purchase.</p>

<p>Use code: <strong>WELCOME10</strong> at checkout.</p>

<p>Discover our curated collection of premium fashion and lifestyle products from trusted suppliers across the UAE and beyond.</p>

<div style="text-align: center; margin: 20px 0;">
    <a href="{{unsubscribe_url}}" style="color: #666; font-size: 12px;">Unsubscribe</a>
</div>
""",
                "template_type": "promotional",
                "variables": '["{{first_name}}", "{{unsubscribe_url}}"]',
                "created_by": admin_id
            },
            {
                "name": "Flash Sale Announcement",
                "subject": "⚡ FLASH SALE: Up to 50% Off - Limited Time!",
                "html_content": """
<h3>🚨 FLASH SALE ALERT! 🚨</h3>

<p>Don't miss out on our biggest sale of the season! Up to <strong>50% off</strong> on selected items.</p>

<p><strong>Sale ends in 24 hours!</strong></p>

<p>Featured deals:</p>
<ul>
    <li>Luxury handbags from $199</li>
    <li>Designer watches up to 40% off</li>
    <li>Silk accessories starting at $49</li>
</ul>

<p>Shop now before it's too late!</p>

<div style="text-align: center; margin: 20px 0;">
    <a href="{{unsubscribe_url}}" style="color: #666; font-size: 12px;">Unsubscribe</a>
</div>
""",
                "template_type": "promotional",
                "variables": '["{{first_name}}", "{{unsubscribe_url}}"]',
                "created_by": admin_id
            },
            {
                "name": "New Arrivals Newsletter",
                "subject": "New Arrivals: Fresh Fashion Just Landed!",
                "html_content": """
<p>Hello {{first_name}},</p>

<p>We've just added some amazing new pieces to our collection! Check out the latest arrivals from our featured suppliers.</p>

<p><strong>This week's highlights:</strong></p>
<ul>
    <li>Premium leather goods</li>
    <li>Contemporary jewelry</li>
    <li>Limited edition accessories</li>
</ul>

<p>Be the first to shop these exclusive items before they're gone!</p>

<div style="text-align: center; margin: 20px 0;">
    <a href="{{unsubscribe_url}}" style="color: #666; font-size: 12px;">Unsubscribe</a>
</div>
""",
                "template_type": "marketing",
                "variables": '["{{first_name}}", "{{unsubscribe_url}}"]',
                "created_by": admin_id
            },
            {
                "name": "Abandoned Cart Recovery",
                "subject": "Your Cart is Waiting - Complete Your Purchase!",
                "html_content": """
<p>Hi {{first_name}},</p>

<p>We noticed you were interested in some items but didn't complete your purchase. Your cart is saved and ready for you!</p>

<p>Complete your order now and enjoy:</p>
<ul>
    <li>Free shipping on orders over AED 200</li>
    <li>30-day return policy</li>
    <li>Secure checkout</li>
</ul>

<p>Your items are reserved for 24 hours.</p>

<div style="text-align: center; margin: 20px 0;">
    <a href="{{unsubscribe_url}}" style="color: #666; font-size: 12px;">Unsubscribe</a>
</div>
""",
                "template_type": "transactional",
                "variables": '["{{first_name}}", "{{unsubscribe_url}}"]',
                "created_by": admin_id
            }
        ]

        # Idempotent: only add templates that don't already exist by name
        for template_data in email_templates:
            _upsert_email_template(db, template_data)

        db.commit()
        logger.info("Sample data seeded successfully")
        
        _seed_employee_data(db)
    except Exception:
        db.rollback()
        logger.exception("Seed failed")
        raise
    finally:
        db.close()


