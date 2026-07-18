from sqlalchemy.orm import sessionmaker
from db.database import engine, Base
from db.models import User
from utils.auth import get_password_hash

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_data():
    # Create tables (safe — skips already-existing tables)
    Base.metadata.create_all(bind=engine)
    print("Tables:", list(Base.metadata.tables.keys()))

    db = SessionLocal()
    try:
        # Create admin user
        admin_user = db.query(User).filter(User.email == "admin@zozi.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@zozi.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin_user)
            print("Admin user created")

        # Create supplier user
        supplier_user = db.query(User).filter(User.email == "supplier@zozi.com").first()
        if not supplier_user:
            supplier_user = User(
                email="supplier@zozi.com",
                username="supplier",
                hashed_password=get_password_hash("supplier123"),
                role="supplier"
            )
            db.add(supplier_user)
            db.commit()
            db.refresh(supplier_user)
            supplier_id = supplier_user.id
            print("Supplier user created")
        else:
            supplier_id = supplier_user.id

        # Create customer user
        customer_user = db.query(User).filter(User.email == "customer@zozi.com").first()
        if not customer_user:
            customer_user = User(
                email="customer@zozi.com",
                username="customer",
                hashed_password=get_password_hash("customer123"),
                role="customer"
            )
            db.add(customer_user)
            print("Customer user created")

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
                "supplier_id": supplier_id
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
                "supplier_id": 1
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
                "supplier_id": 1
            }
        ]

        # Idempotent: only add products that don't already exist by name
        for product_data in products:
            existing = db.query(Product).filter(Product.name == product_data["name"]).first()
            if not existing:
                db.add(Product(**product_data))

        db.commit()
        print("Sample data seeded successfully!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
