"""
Seed realistic product data — categories, products, variants, reviews.

Usage:
    cd backend && python seed_products.py
"""

import sys
import os
import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(__file__))

from db.database import SessionLocal
from models.user import User
from models.products import Category, Product, ProductVariant, Review

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("seed_products")


# ── Seed data ──────────────────────────────────────────────────────────────

CATEGORIES = [
    {"name": "Electronics", "slug": "electronics", "description": "Phones, laptops, gadgets", "is_featured": True},
    {"name": "Fashion", "slug": "fashion", "description": "Clothing, shoes, accessories", "is_featured": True},
    {"name": "Home & Living", "slug": "home-living", "description": "Furniture, decor, kitchen", "is_featured": True},
    {"name": "Beauty", "slug": "beauty", "description": "Skincare, makeup, fragrances", "is_featured": True},
    {"name": "Sports", "slug": "sports", "description": "Fitness, outdoor, sports gear", "is_featured": False},
    {"name": "Baby & Kids", "slug": "baby-kids", "description": "Toys, clothing, nursery", "is_featured": False},
    {"name": "Automotive", "slug": "automotive", "description": "Car parts, accessories", "is_featured": False},
    {"name": "Books", "slug": "books", "description": "Fiction, non-fiction, academic", "is_featured": False},
    {"name": "Grocery", "slug": "grocery", "description": "Food, beverages, household", "is_featured": False},
    {"name": "Accessories", "slug": "accessories", "description": "Bags, watches, jewelry", "is_featured": True},
]

PRODUCTS = [
    # ── Electronics ───────────────────────────────────────────────────────
    {"name": "iPhone 15 Pro Max", "description": "Latest Apple iPhone with A17 Pro chip, titanium design, 48MP camera system", "price": 1199.99, "compare_price": 1299.99, "category": "Electronics", "brand": "Apple", "color": "Titanium Blue", "stock": 50, "sales_count": 342, "rating": 4.8},
    {"name": "Samsung Galaxy S24 Ultra", "description": "Galaxy AI-powered smartphone with S Pen, 200MP camera", "price": 1099.99, "compare_price": 1199.99, "category": "Electronics", "brand": "Samsung", "color": "Titanium Gray", "stock": 45, "sales_count": 289, "rating": 4.7},
    {"name": "MacBook Pro 14-inch M3", "description": "Apple M3 Pro chip, 18GB RAM, 512GB SSD, Liquid Retina XDR display", "price": 1999.99, "category": "Electronics", "brand": "Apple", "color": "Space Black", "stock": 25, "sales_count": 156, "rating": 4.9},
    {"name": "Sony WH-1000XM5 Headphones", "description": "Industry-leading noise cancellation, 30-hour battery, multipoint connection", "price": 349.99, "compare_price": 399.99, "category": "Electronics", "brand": "Sony", "color": "Black", "stock": 80, "sales_count": 445, "rating": 4.6},
    {"name": "iPad Air M2", "description": "11-inch Liquid Retina display, M2 chip, Touch ID", "price": 599.99, "category": "Electronics", "brand": "Apple", "color": "Purple", "stock": 35, "sales_count": 198, "rating": 4.7},
    {"name": "Dell XPS 15 Laptop", "description": "15.6-inch OLED display, Intel Core i9, 32GB RAM, 1TB SSD", "price": 1799.99, "compare_price": 1999.99, "category": "Electronics", "brand": "Dell", "color": "Platinum Silver", "stock": 20, "sales_count": 87, "rating": 4.5},
    {"name": "AirPods Pro 2nd Gen", "description": "Active noise cancellation, adaptive transparency, USB-C", "price": 249.99, "category": "Electronics", "brand": "Apple", "color": "White", "stock": 120, "sales_count": 567, "rating": 4.8},
    {"name": "LG OLED C3 65-inch TV", "description": "4K OLED, AI-powered processor, Dolby Vision, 120Hz", "price": 1599.99, "compare_price": 1899.99, "category": "Electronics", "brand": "LG", "color": "Black", "stock": 15, "sales_count": 65, "rating": 4.7},
    # ── Fashion ───────────────────────────────────────────────────────────
    {"name": "Nike Air Max 270", "description": "Max Air unit for unrivaled comfort, lightweight mesh upper", "price": 149.99, "category": "Fashion", "brand": "Nike", "color": "Black/White", "stock": 100, "sales_count": 823, "rating": 4.5},
    {"name": "Adidas Ultraboost 23", "description": "Responsive BOOST midsole, Primeknit+ upper", "price": 189.99, "compare_price": 219.99, "category": "Fashion", "brand": "Adidas", "color": "Core Black", "stock": 75, "sales_count": 456, "rating": 4.6},
    {"name": "Gucci GG Marmont Bag", "description": "Quilted leather, antique gold-toned hardware, chain strap", "price": 2450.00, "category": "Fashion", "brand": "Gucci", "color": "Black", "stock": 10, "sales_count": 23, "rating": 4.9},
    {"name": "Levi's 501 Original Jeans", "description": "Iconic straight leg, button fly, 100% cotton denim", "price": 89.99, "category": "Fashion", "brand": "Levi's", "color": "Medium Wash", "stock": 150, "sales_count": 1234, "rating": 4.4},
    {"name": "Zara Blazer Collection", "description": "Tailored fit, single-breasted, peak lapel", "price": 129.99, "category": "Fashion", "brand": "Zara", "color": "Navy", "stock": 40, "sales_count": 189, "rating": 4.3},
    {"name": "Hermes Silk Scarf", "description": "100% mulberry silk, hand-rolled edges, iconic patterns", "price": 445.00, "category": "Fashion", "brand": "Hermes", "color": "Red/Blue", "stock": 8, "sales_count": 34, "rating": 4.9},
    {"name": "Ray-Ban Aviator Classic", "description": "Gold frame, green classic G-15 lenses, 100% UV protection", "price": 163.00, "compare_price": 185.00, "category": "Fashion", "brand": "Ray-Ban", "color": "Gold/Green", "stock": 60, "sales_count": 567, "rating": 4.7},
    # ── Home & Living ─────────────────────────────────────────────────────
    {"name": "IKEA KALLAX Shelf Unit", "description": "4x4 cube organizer, versatile storage, white finish", "price": 179.99, "category": "Home & Living", "brand": "IKEA", "color": "White", "stock": 30, "sales_count": 345, "rating": 4.3},
    {"name": "Dyson V15 Detect Vacuum", "description": "Laser dust detection, 60min runtime, HEPA filtration", "price": 749.99, "compare_price": 849.99, "category": "Home & Living", "brand": "Dyson", "color": "Yellow/Nickel", "stock": 20, "sales_count": 123, "rating": 4.8},
    {"name": "Nespresso Vertuo Plus", "description": "Centrifusion brewing, 5 cup sizes, 30-sec heat up", "price": 199.99, "category": "Home & Living", "brand": "Nespresso", "color": "Black", "stock": 45, "sales_count": 234, "rating": 4.5},
    {"name": "Samsung 65\" Crystal UHD TV", "description": "4K UHD, Crystal Processor 4K, HDR10+", "price": 599.99, "compare_price": 799.99, "category": "Home & Living", "brand": "Samsung", "color": "Black", "stock": 18, "sales_count": 89, "rating": 4.4},
    {"name": "Philips Hue Starter Kit", "description": "3 smart bulbs + bridge, 16M colors, voice control", "price": 199.99, "category": "Home & Living", "brand": "Philips", "color": "White/Color Ambiance", "stock": 50, "sales_count": 312, "rating": 4.6},
    # ── Beauty ────────────────────────────────────────────────────────────
    {"name": "Chanel No. 5 Eau de Parfum", "description": "Iconic floral aldehyde fragrance, 100ml", "price": 145.00, "category": "Beauty", "brand": "Chanel", "color": "Clear", "stock": 25, "sales_count": 189, "rating": 4.8},
    {"name": "Dyson Airwrap Complete", "description": "Multi-styler with Coanda airflow, 6 attachments", "price": 599.99, "compare_price": 649.99, "category": "Beauty", "brand": "Dyson", "color": "Nickel/Copper", "stock": 15, "sales_count": 234, "rating": 4.7},
    {"name": "La Mer Moisturizing Cream", "description": "Miracle Broth, ultra-rich, 60ml", "price": 380.00, "category": "Beauty", "brand": "La Mer", "color": "White", "stock": 12, "sales_count": 67, "rating": 4.9},
    {"name": "MAC Matte Lipstick", "description": "Long-wearing, color-intense, 30+ shades", "price": 23.00, "category": "Beauty", "brand": "MAC", "color": "Ruby Woo", "stock": 200, "sales_count": 1567, "rating": 4.5},
    {"name": "Olay Regenerist Micro-Sculpting Cream", "description": "Anti-aging, niacinamide + peptides, 50g", "price": 28.99, "compare_price": 34.99, "category": "Beauty", "brand": "Olay", "color": "White", "stock": 80, "sales_count": 456, "rating": 4.4},
    # ── Sports ────────────────────────────────────────────────────────────
    {"name": "Peloton Bike+", "description": "23.8\" rotating HD touchscreen, auto-follow resistance", "price": 2495.00, "compare_price": 2795.00, "category": "Sports", "brand": "Peloton", "color": "Black", "stock": 5, "sales_count": 34, "rating": 4.6},
    {"name": "Garmin Forerunner 265", "description": "GPS running watch, AMOLED display, 13-day battery", "price": 449.99, "category": "Sports", "brand": "Garmin", "color": "Black", "stock": 30, "sales_count": 156, "rating": 4.7},
    {"name": "Yoga Mat Premium", "description": "Non-slip, 6mm thick, eco-friendly TPE material", "price": 45.99, "category": "Sports", "brand": "Manduka", "color": "Purple", "stock": 100, "sales_count": 678, "rating": 4.5},
    {"name": "Adjustable Dumbbells Set", "description": "5-52.5 lbs each, 15 weight settings, compact design", "price": 349.99, "compare_price": 399.99, "category": "Sports", "brand": "Bowflex", "color": "Black/Red", "stock": 20, "sales_count": 234, "rating": 4.6},
    # ── Accessories ───────────────────────────────────────────────────────
    {"name": "Apple Watch Series 9", "description": "Always-on Retina display, S9 chip, double tap gesture", "price": 399.99, "category": "Accessories", "brand": "Apple", "color": "Midnight", "stock": 60, "sales_count": 456, "rating": 4.7},
    {"name": "Rolex Submariner", "description": "Oystersteel, black Cerachrom bezel, 300m waterproof", "price": 10500.00, "category": "Accessories", "brand": "Rolex", "color": "Silver/Black", "stock": 3, "sales_count": 12, "rating": 5.0},
    {"name": "Samsonite Lite-Box ALU", "description": "Aluminum hardside, TSA locks, 4-wheel spinner", "price": 599.99, "compare_price": 699.99, "category": "Accessories", "brand": "Samsonite", "color": "Silver", "stock": 25, "sales_count": 89, "rating": 4.5},
    {"name": "Raymond Weil Freelancer", "description": "Swiss automatic, stainless steel, date display", "price": 1295.00, "category": "Accessories", "brand": "Raymond Weil", "color": "Silver/Blue", "stock": 8, "sales_count": 23, "rating": 4.8},
]


def seed():
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

        # Get supplier IDs
        suppliers = db.query(User).filter(User.role == "supplier").all()
        if not suppliers:
            log.warning("No suppliers found! Run seed_users.py first.")
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

        # Seed reviews for some products
        log.info(f"\nSeeding reviews...")
        customers = db.query(User).filter(User.role == "customer").all()
        products = db.query(Product).all()

        review_count = 0
        if not customers:
            log.warning("  No customers found — skipping reviews")
        else:
            for product in products[:15]:  # Reviews for first 15 products
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


if __name__ == "__main__":
    seed()
