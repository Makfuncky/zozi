from domains.catalog.services.products.products_service import get_products
from infrastructure.database.database import get_db

db = next(get_db())
try:
    products, total = get_products(db, None, limit=5, offset=0)
    print(f'Products returned: {len(products)}, Total: {total}')
    for p in products[:3]:
        print(f'  - {p.name}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
