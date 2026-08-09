"""
Seed realistic order data — orders, order items, payments.

Usage:
    cd backend && python seed_orders.py
"""

import sys
import os
import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

sys.path.insert(0, os.path.dirname(__file__))

from db.database import SessionLocal
from models.user import User
from models.products import Product
from models.orders import Order, OrderItem

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("seed_orders")


ORDER_STATUSES = ["pending", "processing", "confirmed", "shipped", "in_transit", "delivered", "cancelled"]
PAYMENT_STATUSES = ["pending", "completed", "failed", "refunded"]
PAYMENT_METHODS = ["credit_card", "debit_card", "apple_pay", "cod", "bank_transfer"]
CURRENCIES = ["AED", "SAR", "OMR", "USD", "BHD"]
SHIPPING_ADDRESSES = [
    "Al Majaz, Sharjah, UAE",
    "Dubai Marina, Dubai, UAE",
    "Al Khuwair, Muscat, Oman",
    "King Fahd Road, Riyadh, Saudi Arabia",
    "Manama, Bahrain",
    "Abu Dhabi, UAE",
    "Jeddah, Saudi Arabia",
    "Salalah, Oman",
]


def seed():
    db = SessionLocal()
    try:
        log.info("Seeding orders...")

        # Get users and products
        customers = db.query(User).filter(User.role == "customer").all()
        suppliers = db.query(User).filter(User.role == "supplier").all()
        products = db.query(Product).filter(Product.is_active == True, Product.is_deleted == False).all()

        if not customers:
            log.warning("No customers found! Run seed_users.py first.")
            return
        if not products:
            log.warning("No products found! Run seed_products.py first.")
            return



        existing_count = db.query(Order).count()
        if existing_count > 0:
            log.info(f"  ✓ {existing_count} orders already exist. Skipping.")
            return

        created_count = 0
        item_count = 0

        for i in range(50):  # Create 50 orders
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
            tax_amount = subtotal * Decimal("0.05")  # 5% VAT
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

            # Create order items
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


if __name__ == "__main__":
    seed()
