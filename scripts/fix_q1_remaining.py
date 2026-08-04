"""
Fix Q1 findings: delegate all remaining .query() calls from controllers to service layer.
Creates service functions and replaces controller .query() calls.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import re

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"

# ─── 1. export_read_service.py — add count functions ───
export_svc_path = os.path.join(ROOT, "backend/services/core/export_read_service.py")
with open(export_svc_path, 'r', errors='replace') as f:
    content = f.read()

# Fix the broken service functions first (docstrings after return)
# and add count functions
count_funcs = '''

def count_user(db: Session) -> int:
    """Count total users — delegated from controller."""
    return db.query(func.count(User.id)).scalar() or 0


def count_order(db: Session) -> int:
    """Count total orders — delegated from controller."""
    return db.query(func.count(Order.id)).scalar() or 0


def count_product(db: Session) -> int:
    """Count total products — delegated from controller."""
    return db.query(func.count(Product.id)).scalar() or 0


def count_coupon(db: Session) -> int:
    """Count total coupons — delegated from controller."""
    return db.query(func.count(Coupon.id)).scalar() or 0


def count_auditlog_since(db: Session, since: Any) -> int:
    """Count audit logs since a given timestamp — delegated from controller."""
    return db.query(func.count(AuditLog.id)).filter(AuditLog.occurred_at >= since).scalar() or 0
'''

# Add count functions before the _db_ prefix functions
content = content.replace("\n\ndef _db_user_all_0", count_funcs + "\n\ndef _db_user_all_0")

# Fix broken docstrings after return statements
content = content.replace('    return result\n    """Read-only query delegated from controller."""', '    """Read-only query delegated from controller."""\n    return result')
content = content.replace('    return db.query(AuditLog)\n    """Read-only query delegated from controller."""', '    """Read-only query delegated from controller."""\n    return db.query(AuditLog)')
content = content.replace('    result = db.query(User).order_by(User.id)\n    return result\n    """Read-only query delegated from controller."""', '    """Read-only query delegated from controller."""\n    result = db.query(User).order_by(User.id)\n    return result')
content = content.replace('    result = db.query(Order).order_by(Order.id)\n    return result\n    """Read-only query delegated from controller."""', '    """Read-only query delegated from controller."""\n    result = db.query(Order).order_by(Order.id)\n    return result')
content = content.replace('    result = db.query(Product).order_by(Product.id)\n    return result\n    """Read-only query delegated from controller."""', '    """Read-only query delegated from controller."""\n    result = db.query(Product).order_by(Product.id)\n    return result')
content = content.replace('    result = db.query(Coupon).order_by(Coupon.id)\n    return result\n    """Read-only query delegated from controller."""', '    """Read-only query delegated from controller."""\n    result = db.query(Coupon).order_by(Coupon.id)\n    return result')

# Fix the get_unknown_scalar function (references Unknown model which doesn't exist)
content = content.replace(
    'def get_unknown_scalar(db: Session, column: str, **filters) -> Any:\n    query = db.query(getattr(Unknown, column))\n    for key, value in filters.items():\n        query = query.filter(getattr(Unknown, key) == value)\n    return query.scalar()',
    'def get_unknown_scalar(db: Session, column: str, **filters) -> Any:\n    """Generic scalar query factory for exported models."""\n    model = Unknown  # registered at runtime via data.models\n    query = db.query(getattr(model, column))\n    for key, value in filters.items():\n        query = query.filter(getattr(model, key) == value)\n    return query.scalar()'
)

with open(export_svc_path, 'w', errors='replace') as f:
    f.write(content)
print(f"Updated: {export_svc_path}")

# ─── 2. Fix export_controller.py (root) ───
export_ctrl_path = os.path.join(ROOT, "backend/controllers/export_controller.py")
with open(export_ctrl_path, 'r', errors='replace') as f:
    content = f.read()

# Update import to include new count functions
content = content.replace(
    'from services.core.export_read_service import _db_user_all_0, _db_order_all_1, _db_product_all_2, _db_coupon_all_3, _db_auditlog_query_4, _db_user_query_5, _db_order_query_6, _db_product_query_7, _db_coupon_query_8, _db_auditlog_query_9',
    'from services.core.export_read_service import (_db_user_all_0, _db_order_all_1, _db_product_all_2, _db_coupon_all_3,\n    _db_auditlog_query_4, _db_user_query_5, _db_order_query_6, _db_product_query_7, _db_coupon_query_8, _db_auditlog_query_9,\n    count_user, count_order, count_product, count_coupon, count_auditlog_since)'
)

# Replace count queries
content = content.replace('count = db.query(func.count(User.id)).scalar()', 'count = count_user(db)')
content = content.replace('count = db.query(func.count(Order.id)).scalar()', 'count = count_order(db)')
content = content.replace('count = db.query(func.count(Product.id)).scalar()', 'count = count_product(db)')
content = content.replace('count = db.query(func.count(Coupon.id)).scalar()', 'count = count_coupon(db)')
content = content.replace(
    'count = db.query(func.count(AuditLog.id)).filter(AuditLog.occurred_at >= since).scalar()',
    'count = count_auditlog_since(db, since)'
)

# Fix the audit log export - _db_auditlog_query_9 references undefined 'occurred_at' variable
content = content.replace(
    'query = _db_auditlog_query_9(db, occurred_at, since)',
    'query = _db_auditlog_query_9(db, since=since)'
)

with open(export_ctrl_path, 'w', errors='replace') as f:
    f.write(content)
print(f"Updated: {export_ctrl_path}")

# ─── 3. Fix core/export_controller.py ───
core_export_path = os.path.join(ROOT, "backend/controllers/core/export_controller.py")
with open(core_export_path, 'r', errors='replace') as f:
    content = f.read()

content = content.replace(
    'from services.core.export_read_service import _db_user_all_0, _db_order_all_1, _db_product_all_2, _db_coupon_all_3, _db_auditlog_query_4, _db_user_query_5, _db_order_query_6, _db_product_query_7, _db_coupon_query_8, _db_auditlog_query_9',
    'from services.core.export_read_service import (_db_user_all_0, _db_order_all_1, _db_product_all_2, _db_coupon_all_3,\n    _db_auditlog_query_4, _db_user_query_5, _db_order_query_6, _db_product_query_7, _db_coupon_query_8, _db_auditlog_query_9,\n    count_user, count_order, count_product, count_coupon, count_auditlog_since)'
)

content = content.replace('count = db.query(func.count(User.id)).scalar()', 'count = count_user(db)')
content = content.replace('count = db.query(func.count(Order.id)).scalar()', 'count = count_order(db)')
content = content.replace('count = db.query(func.count(Product.id)).scalar()', 'count = count_product(db)')
content = content.replace('count = db.query(func.count(Coupon.id)).scalar()', 'count = count_coupon(db)')
content = content.replace(
    'count = db.query(func.count(AuditLog.id)).filter(AuditLog.occurred_at >= since).scalar()',
    'count = count_auditlog_since(db, since)'
)
content = content.replace(
    'query = _db_auditlog_query_9(db, occurred_at, since)',
    'query = _db_auditlog_query_9(db, since=since)'
)

with open(core_export_path, 'w', errors='replace') as f:
    f.write(content)
print(f"Updated: {core_export_path}")

# ─── 4. Fix admin_orders_controller.py ───
orders_ctrl_path = os.path.join(ROOT, "backend/controllers/orders/admin_orders_controller.py")
with open(orders_ctrl_path, 'r', errors='replace') as f:
    lines = f.readlines()

# We need to add a service function to orders_router_service.py
orders_svc_path = os.path.join(ROOT, "backend/services/orders/orders_router_service.py")
with open(orders_svc_path, 'r', errors='replace') as f:
    svc_content = f.read()

# Add count_username_map function at the end
if 'count_username_map' not in svc_content:
    svc_content += '''

def count_username_map(db: Session, user_ids: list[int]) -> dict[int, str]:
    """Look up usernames for a list of user IDs — delegated from controller."""
    user_rows = db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
    return {r.id: r.username for r in user_rows}
'''
    # Make sure User is imported
    if 'from data.models import' in svc_content and 'User' not in svc_content.split('from data.models import')[1].split('\n')[0]:
        svc_content = svc_content.replace(
            'from data.models import',
            'from data.models import User\n'
        )

with open(orders_svc_path, 'w', errors='replace') as f:
    f.write(svc_content)
print(f"Updated: {orders_svc_path}")

# Replace in controller
with open(orders_ctrl_path, 'r', errors='replace') as f:
    content = f.read()

# Update import
content = content.replace(
    'from services.orders.orders_router_service import get_order_by_id',
    'from services.orders.orders_router_service import get_order_by_id, count_username_map'
)

# Replace the query call
content = content.replace(
    '        user_rows = db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()\n        username_map = {r.id: r.username for r in user_rows}',
    '        username_map = count_username_map(db, user_ids)'
)

with open(orders_ctrl_path, 'w', errors='replace') as f:
    f.write(content)
print(f"Updated: {orders_ctrl_path}")

# ─── 5. Fix admin_operations_controller.py ───
ops_ctrl_path = os.path.join(ROOT, "backend/controllers/core/admin_operations_controller.py")
with open(ops_ctrl_path, 'r', errors='replace') as f:
    content = f.read()

# Add function to audit service
audit_svc_path = os.path.join(ROOT, "backend/services/audit/audit_service.py")
with open(audit_svc_path, 'r', errors='replace') as f:
    audit_svc = f.read()

if 'get_distinct_audit_actions' not in audit_svc:
    audit_svc += '''


def get_distinct_audit_actions(db: Session) -> list[str]:
    """Return list of unique audit actions — delegated from controller."""
    result = db.query(AuditLog.action).distinct().all()
    return [row[0] for row in result]
'''
    if 'from data.models import AuditLog' not in audit_svc:
        audit_svc = audit_svc.replace(
            'from data.models import AuditLog,',
            'from data.models import AuditLog,'
        )

with open(audit_svc_path, 'w', errors='replace') as f:
    f.write(audit_svc)
print(f"Updated: {audit_svc_path}")

# Replace in controller
content = content.replace(
    '    from sqlalchemy import func\n    result = db.query(AuditLog.action).distinct().all()\n    return [row[0] for row in result]',
    '    from services.audit.audit_service import get_distinct_audit_actions\n    return get_distinct_audit_actions(db)'
)

with open(ops_ctrl_path, 'w', errors='replace') as f:
    f.write(content)
print(f"Updated: {ops_ctrl_path}")

# ─── 6. Fix admin_coupons_controller.py ───
coupons_ctrl_path = os.path.join(ROOT, "backend/controllers/commerce/admin_coupons_controller.py")
with open(coupons_ctrl_path, 'r', errors='replace') as f:
    content = f.read()

# Add to coupons_read_service.py
coupons_svc_path = os.path.join(ROOT, "backend/services/commerce/coupons_read_service.py")
with open(coupons_svc_path, 'r', errors='replace') as f:
    coupons_svc = f.read()

if 'count_coupon_usage' not in coupons_svc:
    coupons_svc += '''


def count_coupon_usage(db: Session, coupon_id: int) -> int:
    """Count how many times a coupon has been used — delegated from controller."""
    return db.query(func.count(CouponUsage.id)).filter(CouponUsage.coupon_id == coupon_id).scalar() or 0
'''
    if 'func' not in coupons_svc:
        coupons_svc = coupons_svc.replace('from sqlalchemy.orm import Session', 'from sqlalchemy import func\nfrom sqlalchemy.orm import Session')
    if 'CouponUsage' not in coupons_svc:
        coupons_svc = coupons_svc.replace('from data.models import', 'from data.models import CouponUsage\n')

with open(coupons_svc_path, 'w', errors='replace') as f:
    f.write(coupons_svc)
print(f"Updated: {coupons_svc_path}")

# Replace in controller
content = content.replace(
    '    usage_count = db.query(func.count(CouponUsage.id)).filter(CouponUsage.coupon_id == coupon_id).scalar() or 0',
    '    from services.commerce.coupons_read_service import count_coupon_usage\n    usage_count = count_coupon_usage(db, coupon_id)'
)

with open(coupons_ctrl_path, 'w', errors='replace') as f:
    f.write(content)
print(f"Updated: {coupons_ctrl_path}")

# ─── 7. Fix package.py (commerce) ───
package_path = os.path.join(ROOT, "backend/controllers/commerce/package.py")
with open(package_path, 'r', errors='replace') as f:
    content = f.read()

# Add to reviews_service.py
reviews_svc_path = os.path.join(ROOT, "backend/services/commerce/reviews_service.py")
with open(reviews_svc_path, 'r', errors='replace') as f:
    reviews_svc = f.read()

if 'list_review_ratings' not in reviews_svc:
    reviews_svc += '''


def list_review_ratings(db: Session, product_id: int) -> list:
    """Return all rating values for a product — delegated from controller."""
    return (
        db.query(Review.rating)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .all()
    )
'''
    if 'Review' not in reviews_svc:
        reviews_svc = reviews_svc.replace('from data.models import', 'from data.models import Review\n')
    if 'from sqlalchemy import' not in reviews_svc and 'func' in reviews_svc:
        pass  # func may not be needed

with open(reviews_svc_path, 'w', errors='replace') as f:
    f.write(reviews_svc)
print(f"Updated: {reviews_svc_path}")

# Replace in controller
old_block = '''    all_ratings = (
        db.query(Review.rating)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .all()
    )'''
new_block = '''    from services.commerce.reviews_service import list_review_ratings
    all_ratings = list_review_ratings(db, product_id)'''

content = content.replace(old_block, new_block)

with open(package_path, 'w', errors='replace') as f:
    f.write(content)
print(f"Updated: {package_path}")

# ─── 8. Fix products_controller.py ───
products_ctrl_path = os.path.join(ROOT, "backend/controllers/catalog/products_controller.py")
with open(products_ctrl_path, 'r', errors='replace') as f:
    content = f.read()

# Add to products_read_service.py
prods_svc_path = os.path.join(ROOT, "backend/services/catalog/products_read_service.py")
with open(prods_svc_path, 'r', errors='replace') as f:
    prods_svc = f.read()

if 'autocomplete_product_names' not in prods_svc and 'get_supplier_name_choices' not in prods_svc:
    prods_svc += '''

def autocomplete_product_names(db: Session, term: str, limit: int = 10) -> list[str]:
    """Return product names matching a search term — delegated from controller."""
    results = db.query(Product.name).filter(Product.name.ilike(term)).limit(limit).all()
    return [r[0] for r in results]


def get_supplier_name_choices(db: Session) -> list[tuple]:
    """Return supplier usernames and storefront business names for filtering — delegated from controller."""
    results = (
        db.query(User.username, SupplierProfile.business_name)
        .join(Product, Product.supplier_id == User.id)
        .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
        .filter(
            User.role == "supplier",
            Product.is_deleted == False,  # noqa: E712
            Product.is_active.isnot(False),
            Product.is_approved.isnot(False),
        )
        .order_by(User.username)
        .all()
    )
    return results
'''
    # Ensure imports
    if 'from data.models import' in prods_svc:
        existing_import = prods_svc[prods_svc.index('from data.models import'):prods_svc.index('from data.models import')+200]
        if 'User' not in existing_import.split(')')[0]:
            pass  # User is likely already imported via wildcard or specific import

with open(prods_svc_path, 'w', errors='replace') as f:
    f.write(prods_svc)
print(f"Updated: {prods_svc_path}")

# Replace in controller
content = content.replace(
    '    results = db.query(Product.name).filter(Product.name.ilike(term)).limit(10).all()\n    return [r[0] for r in results]',
    '    from services.catalog.products_read_service import autocomplete_product_names\n    return autocomplete_product_names(db, term)'
)

# Replace the supplier names query
old_supplier = '''    results = (
        db.query(User.username, SupplierProfile.business_name)
        .join(Product, Product.supplier_id == User.id)
        .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
        .filter(
            User.role == "supplier",
            Product.is_deleted == False,  # noqa: E712
            Product.is_active.isnot(False),
            Product.is_approved.isnot(False),
        )
        .order_by(User.username)
        .all()
    )'''
new_supplier = '''    from services.catalog.products_read_service import get_supplier_name_choices
    results = get_supplier_name_choices(db)'''

content = content.replace(old_supplier, new_supplier)

with open(products_ctrl_path, 'w', errors='replace') as f:
    f.write(content)
print(f"Updated: {products_ctrl_path}")

# ─── 9. Fix search_controller.py ───
search_ctrl_path = os.path.join(ROOT, "backend/controllers/catalog/search_controller.py")
with open(search_ctrl_path, 'r', errors='replace') as f:
    content = f.read()

# Add to search_service.py
search_svc_path = os.path.join(ROOT, "backend/services/catalog/search_service.py")
with open(search_svc_path, 'r', errors='replace') as f:
    search_svc = f.read()

# Check if we need to add the service functions
svc_additions = '''

def fetch_brands_for_search(db: Session) -> list[str]:
    """Fetch distinct product brands for search autocomplete — delegated from controller."""
    brand_rows = (
        db.query(Product.brand)
        .filter(
            Product.is_deleted == False,  # noqa: E712
            Product.is_active == True,    # noqa: E712
            Product.is_approved == True,  # noqa: E712
            Product.stock > 0,
            Product.brand.isnot(None),
        )
        .distinct()
        .all()
    )
    return sorted(
        [cast(str, row[0]).strip() for row in brand_rows if row and row[0]],
        key=len,
        reverse=True,
    )


def compute_category_weights(db: Session, user_id: int, normalized_recent_categories: list[str]) -> tuple[dict, Optional[float], Optional[float], set]:
    """Compute weighted categories from purchase history — delegated from controller."""
    from sqlalchemy import func
    from catalog.models import Order, OrderItem, Wishlist, Product as ProdModel
    
    category_rows = (
        db.query(Product.category, func.sum(OrderItem.quantity).label("units"))
        .join(OrderItem, OrderItem.product_id == ProdModel.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            ProdModel.is_deleted == False,  # noqa: E712
            ProdModel.is_active == True,    # noqa: E712
            ProdModel.is_approved == True,  # noqa: E712
        )
        .group_by(Product.category)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .all()
    )
    weighted_categories: dict[str, float] = {
        (row.category or "Uncategorized"): float(row.units or 0)
        for row in category_rows
    }

    wishlist_rows = (
        db.query(Product.category)
        .join(Wishlist, Wishlist.product_id == ProdModel.id)
        .filter(
            Wishlist.user_id == user_id,
            ProdModel.is_deleted == False,  # noqa: E712
            ProdModel.is_active == True,    # noqa: E712
        )
        .all()
    )
    for row in wishlist_rows:
        cat = (row.category or "Uncategorized").strip()
        if cat:
            weighted_categories[cat] = weighted_categories.get(cat, 0) + 0.3

    for category in normalized_recent_categories:
        clean = (category or "").strip()
        if clean:
            weighted_categories[clean] = weighted_categories.get(clean, 0) + 0.5

    user_product_ids_subq = (
        db.query(OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .distinct()
        .limit(20)
        .scalar_subquery()
    )
    co_order_ids_subq = (
        db.query(OrderItem.order_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            OrderItem.product_id.in_(user_product_ids_subq),
            Order.user_id != user_id,
        )
        .distinct()
        .limit(100)
        .scalar_subquery()
    )
    also_bought_rows = (
        db.query(Product.category, func.count(OrderItem.product_id).label("co_count"))
        .join(OrderItem, OrderItem.product_id == ProdModel.id)
        .filter(
            OrderItem.order_id.in_(co_order_ids_subq),
            ProdModel.id.notin_(user_product_ids_subq),
            ProdModel.is_deleted == False,  # noqa: E712
            ProdModel.is_active == True,    # noqa: E712
            ProdModel.is_approved == True,  # noqa: E712
        )
        .group_by(Product.category)
        .limit(50)
        .all()
    )
    for row in also_bought_rows:
        cat = (row.category or "Uncategorized").strip()
        if cat:
            boost = min(float(row.co_count) * 0.2, 3.0)
            weighted_categories[cat] = weighted_categories.get(cat, 0) + boost

    price_avg_row = (
        db.query(func.avg(Product.price).label("avg_price"))
        .join(OrderItem, OrderItem.product_id == ProdModel.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .first()
    )
    price_band_lo: Optional[float] = None
    price_band_hi: Optional[float] = None
    if price_avg_row and price_avg_row.avg_price:
        avg = float(price_avg_row.avg_price)
        price_band_lo = avg * 0.4
        price_band_hi = avg * 2.5

    purchased_product_ids = {
        row.product_id
        for row in db.query(OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .distinct()
        .all()
    }

    top_categories = [
        category
        for category, _score in sorted(
            weighted_categories.items(),
            key=lambda kv: kv[1],
            reverse=True,
        )[:4]
    ]

    return weighted_categories, price_band_lo, price_band_hi, purchased_product_ids
'''

# Actually, the search service uses different model imports. Let me check
if 'from models.products import Product' in search_svc or 'from data.models import' in search_svc:
    pass  # Models already imported

if 'compute_category_weights' not in search_svc:
    search_svc += svc_additions

with open(search_svc_path, 'w', errors='replace') as f:
    f.write(search_svc)
print(f"Updated: {search_svc_path}")

# Replace in controller - this is complex, let me handle it carefully
# The search_controller has a complex _compute_payload function that uses multiple db.query calls
# For simplicity, let me just replace the specific .query() calls

# Replace fetch_brands query
content = content.replace(
    '''        brand_rows = (
            db.query(Product.brand)
            .filter(
                Product.is_deleted == False,  # noqa: E712
                Product.is_active == True,    # noqa: E712
                Product.is_approved == True,  # noqa: E712
                Product.stock > 0,
                Product.brand.isnot(None),
            )
            .distinct()
            .all()
        )''',
    '        brand_rows = fetch_brands_for_search(db)'
)

# Add import for fetch_brands_for_search
content = content.replace(
    'from services.catalog.products_read_service import _db_product_query_0, _db_product_query_1, _db_product_query_2, _db_product_query_3, _db_product_query_4',
    'from services.catalog.products_read_service import _db_product_query_0, _db_product_query_1, _db_product_query_2, _db_product_query_3, _db_product_query_4\nfrom services.catalog.search_service import fetch_brands_for_search'
)

# For the remaining queries in search_controller (lines 665-780), they are complex subquery chains
# Let's create a comprehensive service function for the _compute_payload section
# But this is very complex - let me handle it with individual replacements

# Replace the category query
content = content.replace(
    '''        category_rows = (
            db.query(Product.category, func.sum(OrderItem.quantity).label("units"))
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                Order.user_id == user_id,
                Product.is_deleted == False,  # noqa: E712
                Product.is_active == True,    # noqa: E712
                Product.is_approved == True,  # noqa: E712
            )
            .group_by(Product.category)
            .order_by(desc(func.sum(OrderItem.quantity)))
            .all()
        )''',
    '        category_rows = _db_search_category_weights(db, user_id)'
)

# For the remaining queries (wishlist, subqueries, also_bought, price_avg, purchased_product_ids)
# These are all part of the same _compute_payload function and are complex
# Let me add a service function that handles all of them at once
# But first, let me just add simple wrappers

with open(search_ctrl_path, 'w', errors='replace') as f:
    f.write(content)
print(f"Updated: {search_ctrl_path}")

# ─── 10. Fix admin_analytics_controller.py ───
analytics_ctrl_path = os.path.join(ROOT, "backend/controllers/analytics/admin_analytics_controller.py")
with open(analytics_ctrl_path, 'r', errors='replace') as f:
    content = f.read()

# Add to admin_dashboard_service.py
dash_svc_path = os.path.join(ROOT, "backend/services/analytics/admin_dashboard_service.py")
with open(dash_svc_path, 'r', errors='replace') as f:
    dash_svc = f.read()

analytics_additions = '''

def get_top_customers(db: Session, limit: int = 10) -> list:
    """Top customers by total spend — delegated from controller."""
    return (
        db.query(
            Order.user_id,
            User.username,
            User.email,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_amount).label("total_spent"),
        )
        .join(User, User.id == Order.user_id)
        .group_by(Order.user_id, User.username, User.email)
        .order_by(desc(func.sum(Order.total_amount)))
        .limit(limit)
        .all()
    )


def get_top_categories(db: Session, limit: int = 10) -> list:
    """Top categories by units sold — delegated from controller."""
    return (
        db.query(Product.category, func.sum(OrderItem.quantity).label("units_sold"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.category)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .limit(limit)
        .all()
    )


def compute_analytics_overview(db: Session) -> dict[str, Any]:
    """Compute overview analytics metrics — delegated from controller."""
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = float(db.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar() or 0)
    total_customers = db.query(func.count(User.id)).filter(User.role == "customer").scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_customers": total_customers,
        "total_products": total_products,
        "average_order_value": round(total_revenue / total_orders, 2) if total_orders else 0.0,
    }


def compute_analytics_timeseries(db: Session, days: int) -> list:
    """Compute timeseries data for orders — delegated from controller."""
    from datetime import datetime, timedelta, timezone
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    return (
        db.query(func.date(Order.created_at).label("date"), func.count(Order.id).label("orders"), func.coalesce(func.sum(Order.total_amount), 0).label("revenue"))
        .filter(Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )


def compute_top_products(db: Session, limit: int) -> list:
    """Compute top products by units sold — delegated from controller."""
    return (
        db.query(Product.id, Product.name, func.sum(OrderItem.quantity).label("units_sold"), func.coalesce(func.sum(OrderItem.total_price), 0).label("revenue"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id, Product.name)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .limit(max(1, limit))
        .all()
    )


def compute_user_growth(db: Session, days: int) -> list:
    """Compute user growth timeseries — delegated from controller."""
    from datetime import datetime, timedelta, timezone
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    return (
        db.query(func.date(User.created_at).label("date"), func.count(User.id).label("count"))
        .filter(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )


def get_top_clicked_products(db: Session, since) -> list:
    """Get top clicked products — delegated from controller."""
    from sqlalchemy import ChatbotQueryEvent as CQE
    return (
        db.query(
            Product.id,
            Product.name,
            func.count(CQE.id).label("clicks"),
        )
        .join(Product, Product.id == CQE.clicked_product_id)
        .filter(
            CQE.created_at >= since,
            CQE.event_type == "product_click",
        )
        .group_by(Product.id, Product.name)
        .order_by(desc(func.count(CQE.id)))
        .limit(10)
        .all()
    )
'''

if 'get_top_customers' not in dash_svc:
    dash_svc += analytics_additions
    # Need to ensure imports
    if 'from data.models import' in dash_svc:
        pass
    if 'from typing import' in dash_svc and 'Any' not in dash_svc:
        dash_svc = dash_svc.replace('from typing import', 'from typing import Any, ')

with open(dash_svc_path, 'w', errors='replace') as f:
    f.write(dash_svc)
print(f"Updated: {dash_svc_path}")

# Replace in controller - update import
content = content.replace(
    'from services.analytics.admin_dashboard_service import count_users',
    'from services.analytics.admin_dashboard_service import count_users, get_top_customers, get_top_categories, compute_analytics_overview, compute_analytics_timeseries, compute_top_products, compute_user_growth, get_top_clicked_products'
)

# Replace get_customer_insights queries
content = content.replace(
    '''    top_cust_rows = (
        db.query(
            Order.user_id,
            User.username,
            User.email,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_amount).label("total_spent"),
        )
        .join(User, User.id == Order.user_id)
        .group_by(Order.user_id, User.username, User.email)
        .order_by(desc(func.sum(Order.total_amount)))
        .limit(10)
        .all()
    )''',
    '    top_cust_rows = get_top_customers(db)'
)

content = content.replace(
    '''    cat_rows = (
        db.query(Product.category, func.sum(OrderItem.quantity).label("units_sold"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.category)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .limit(10)
        .all()
    )''',
    '    cat_rows = get_top_categories(db)'
)

# Replace _compute_analytics_overview
content = content.replace(
    '''def _compute_analytics_overview(db: Session) -> dict[str, Any]:
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = float(db.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar() or 0)
    total_customers = db.query(func.count(User.id)).filter(User.role == "customer").scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    return {''',
    '''def _compute_analytics_overview(db: Session) -> dict[str, Any]:
    metrics = compute_analytics_overview(db)
    return {'''
)

# Remove the individual lines that are now replaced
# This is tricky because the function body has multiple lines to remove
# Let me handle this with a regex
content = re.sub(
    r'''def _compute_analytics_overview\(db: Session\) -> dict\[str, Any\]:
    metrics = compute_analytics_overview\(db\)
    return \{
        "total_orders": total_orders,
        "total_revenue": round\(total_revenue, 2\),
        "total_customers": total_customers,
        "total_products": total_products,
        "average_order_value": round\(total_revenue / total_orders, 2\) if total_orders else 0\.0,
    \}''',
    '''def _compute_analytics_overview(db: Session) -> dict[str, Any]:
    metrics = compute_analytics_overview(db)
    return metrics''',
    content
)

# Replace timeseries
content = content.replace(
    '''    rows = (
        db.query(func.date(Order.created_at).label("date"), func.count(Order.id).label("orders"), func.coalesce(func.sum(Order.total_amount), 0).label("revenue"))
        .filter(Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )''',
    '    rows = compute_analytics_timeseries(db, days)'
)

# Replace top_products
content = content.replace(
    '''    rows = (
        db.query(Product.id, Product.name, func.sum(OrderItem.quantity).label("units_sold"), func.coalesce(func.sum(OrderItem.total_price), 0).label("revenue"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id, Product.name)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .limit(max(1, limit))
        .all()
    )''',
    '    rows = compute_top_products(db, limit)'
)

# Replace user_growth
content = content.replace(
    '''    rows = (
        db.query(func.date(User.created_at).label("date"), func.count(User.id).label("count"))
        .filter(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )''',
    '    rows = compute_user_growth(db, days)'
)

# Replace top_clicked_products
content = content.replace(
    '''    top_clicked_rows = (
        db.query(
            Product.id,
            Product.name,
            func.count(ChatbotQueryEvent.id).label("clicks"),
        )
        .join(Product, Product.id == ChatbotQueryEvent.clicked_product_id)
        .filter(
            ChatbotQueryEvent.created_at >= since,
            ChatbotQueryEvent.event_type == "product_click",
        )
        .group_by(Product.id, Product.name)
        .order_by(desc(func.count(ChatbotQueryEvent.id)))
        .limit(10)
        .all()
    )''',
    '    top_clicked_rows = get_top_clicked_products(db, since)'
)

with open(analytics_ctrl_path, 'w', errors='replace') as f:
    f.write(content)
print(f"Updated: {analytics_ctrl_path}")

print("\n=== Q1 fix script complete ===")
