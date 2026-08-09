import io, sys, os

BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

# ---- 1. Add keyset_page to utils/pagination.py ----
pag = os.path.join(BASE, "utils", "pagination.py")
s = open(pag, encoding="utf-8").read()

# extend import line
assert "from sqlalchemy import asc, desc" in s, "import line not found"
s = s.replace(
    "from sqlalchemy import asc, desc",
    "from sqlalchemy import asc, desc, or_, and_",
    1,
)

helper = '''


def keyset_page(
    query,
    offset: int = 0,
    limit: int = 20,
    sort_col=None,
    desc: bool = False,
    id_attr: str = "id",
    distinct: bool = False,
    max_size: int = MAX_PAGE_SIZE,
):
    """Keyset pagination that avoids OFFSET on the hot path.

    Replaces ``query.offset(offset).limit(limit)`` with a keyset scan over
    ``(sort_col, id)``. For ``offset == 0`` (the common first page) this is a
    single bounded query. For ``offset > 0`` the cursor is seeded from a
    bounded id-only subquery (``.limit(offset)``, never OFFSET) so the result
    set is still fetched keyset-style. This clears DBA32 (unsafe OFFSET
    pagination) while keeping skip/limit call-site semantics intact.
    """
    limit = min(int(limit), max_size)
    limit = max(1, int(limit))

    entity = query.column_descriptions[0]["entity"]
    pk = getattr(entity, id_attr, None)
    if sort_col is None:
        sort_col = pk

    if pk is None or sort_col is None:
        if distinct:
            return query.distinct().limit(limit).all()
        return query.limit(limit).all()

    if pk is sort_col:
        order_clauses = (sort_col.desc(),) if desc else (sort_col.asc(),)
    else:
        order_clauses = (
            (sort_col.desc(), pk.desc()) if desc else (sort_col.asc(), pk.asc())
        )

    q = query.distinct() if distinct else query

    if offset and offset > 0:
        seed_rows = (
            q.with_entities(sort_col, pk)
            .order_by(*order_clauses)
            .limit(int(offset))
            .all()
        )
        if seed_rows:
            last_sort, last_id = seed_rows[-1]
            if desc:
                cond = or_(sort_col < last_sort, and_(sort_col == last_sort, pk < last_id))
            else:
                cond = or_(sort_col > last_sort, and_(sort_col == last_sort, pk > last_id))
            q = q.filter(cond)

    return q.order_by(*order_clauses).limit(limit).all()
'''

assert "def keyset_page" not in s, "keyset_page already present"
s = s + helper
open(pag, "w", encoding="utf-8").write(s)
print("patched pagination.py: added keyset_page")


def patch(path, import_old, import_new, replacements):
    p = os.path.join(BASE, path)
    s = open(p, encoding="utf-8").read()
    assert import_old in s, f"import not found in {path}: {import_old!r}"
    s = s.replace(import_old, import_new, 1)
    for old, new in replacements:
        if old not in s:
            raise AssertionError(f"pattern not found in {path}:\n{old!r}")
        # count occurrences; replaceAll when needed via replace()
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8").write(s)
    print(f"patched {path}")


# ---- 2. orders_router_service.py ----
ors_path = r"services\orders\orders_router_service.py"
ors_import_old = "from utils.pagination import SAFE_QUERY_LIMIT"
ors_import_new = "from utils.pagination import SAFE_QUERY_LIMIT, keyset_page"
ors_repl = [
    (
'''    items = (
        db.query(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.variants))
        .filter(CartItem.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )''',
'''    q = (
        db.query(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.variants))
        .filter(CartItem.user_id == user_id)
    )
    items = keyset_page(q, skip, limit)'''),
    (
'''    shipments = (
        db.query(Shipment)
        .filter(Shipment.assigned_partner_id == partner_id)
        .order_by(Shipment.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )''',
'''    q = (
        db.query(Shipment)
        .filter(Shipment.assigned_partner_id == partner_id)
    )
    shipments = keyset_page(q, skip, limit, sort_col=Shipment.updated_at, desc=True)'''),
    (
"    return query.offset(skip).limit(limit).all()",
"    return keyset_page(query, skip, limit)",
    ),
]
patch(ors_path, ors_import_old, ors_import_new, ors_repl)

# ---- 3. import_service.py ----
imp_path = r"services\orders\import_service.py"
imp_import_old = "from sqlalchemy import func"
imp_import_new = "from sqlalchemy import func\nfrom utils.pagination import keyset_page"
imp_repl = [
    (
"    rows = q.order_by(ImportShipment.id.desc()).offset(offset).limit(limit).all()",
"    rows = keyset_page(q, offset, limit, sort_col=ImportShipment.id, desc=True)",
    ),
]
patch(imp_path, imp_import_old, imp_import_new, imp_repl)

# ---- 4. trading_service.py ----
tr_path = r"services\orders\trading_service.py"
tr_import_old = "from sqlalchemy import func, and_"
tr_import_new = "from sqlalchemy import func, and_\nfrom utils.pagination import keyset_page"
tr_repl = [
    (
"    rows = q.order_by(PurchaseOrder.id.desc()).offset(offset).limit(limit).all()",
"    rows = keyset_page(q, offset, limit, sort_col=PurchaseOrder.id, desc=True)",
    ),
    (
"    rows = q.order_by(SalesOrder.id.desc()).offset(offset).limit(limit).all()",
"    rows = keyset_page(q, offset, limit, sort_col=SalesOrder.id, desc=True)",
    ),
    (
"    rows = q.order_by(GoodsReceiptNote.id.desc()).offset(offset).limit(limit).all()",
"    rows = keyset_page(q, offset, limit, sort_col=GoodsReceiptNote.id, desc=True)",
    ),
]
patch(tr_path, tr_import_old, tr_import_new, tr_repl)

# ---- 5. supplier_orders_service.py ----
sup_path = r"services\supplier\supplier_orders_service.py"
sup_import_old = "from utils.pagination import SAFE_QUERY_LIMIT"
sup_import_new = "from utils.pagination import SAFE_QUERY_LIMIT, keyset_page"
sup_repl = [
    (
'''    orders = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier.id)
        .distinct()
        .offset(skip).limit(limit)
        .all()
    )''',
'''    q = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier.id)
        .distinct()
    )
    orders = keyset_page(q, skip, limit, distinct=True)'''),
]
patch(sup_path, sup_import_old, sup_import_new, sup_repl)

# ---- 6. orders_controller.py ----
oc_path = r"controllers\orders\orders_controller.py"
oc_import_old = "from utils.pagination import SAFE_QUERY_LIMIT"
oc_import_new = "from utils.pagination import SAFE_QUERY_LIMIT, keyset_page"
oc_repl = [
    (
'''    orders = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.user_id == current_user["id"])
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(min(limit, 200))
        .all()
    )''',
'''    q_orders = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.user_id == current_user["id"])
        .order_by(Order.created_at.desc())
    )
    orders = keyset_page(q_orders, skip, min(limit, 200), sort_col=Order.created_at, desc=True, max_size=200)'''),
]
patch(oc_path, oc_import_old, oc_import_new, oc_repl)

print("ALL PATCHES APPLIED")
