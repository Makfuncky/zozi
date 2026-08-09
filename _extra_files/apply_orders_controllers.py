import os
BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

def patch(path, import_old, import_new, replacements):
    p = os.path.join(BASE, path)
    s = open(p, encoding="utf-8").read()
    if import_old is not None:
        assert import_old in s, f"import not found in {path}"
        s = s.replace(import_old, import_new, 1)
    for old, new in replacements:
        if old not in s:
            raise AssertionError(f"pattern not found in {path}:\n{old!r}")
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8").write(s)
    print(f"patched {path}")

patch(
    r"controllers\orders\admin_orders_controller.py",
    "from utils.pagination import SAFE_QUERY_LIMIT",
    "from utils.pagination import SAFE_QUERY_LIMIT, keyset_page",
    [(
'''    if offset:
        query = query.offset(offset)
    query = query.limit(resolved_limit)
    orders = query.all()''',
'''    if offset:
        orders = keyset_page(query, offset, resolved_limit, sort_col=Order.created_at, desc=True)
    else:
        query = query.limit(resolved_limit)
        orders = query.all()'''),
    ],
)

patch(
    r"controllers\orders\disputes_controller.py",
    "from sqlalchemy.orm import Session",
    "from sqlalchemy.orm import Session\nfrom utils.pagination import keyset_page",
    [(
'''    items = (
        query.order_by(SupplierDispute.created_at.desc())
        .offset(max(offset, 0))
        .limit(min(max(limit, 1), 500))
        .all()
    )''',
'''    items = keyset_page(
        query,
        max(offset, 0),
        min(max(limit, 1), 500),
        sort_col=SupplierDispute.created_at,
        desc=True,
        max_size=500,
    )'''),
    ],
)

patch(
    r"controllers\orders\returns_controller.py",
    "from utils.pagination import SAFE_QUERY_LIMIT",
    "from utils.pagination import SAFE_QUERY_LIMIT, keyset_page",
    [
    (
"    requests = query.order_by(ReturnRequest.created_at.desc()).offset(offset).limit(limit).all()",
"    requests = keyset_page(query, offset, limit, sort_col=ReturnRequest.created_at, desc=True)",
    ),
    (
'''    total = base_query.count()
    query = base_query
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    requests = query.all()''',
'''    total = base_query.count()
    if offset:
        requests = keyset_page(base_query, offset, limit if limit is not None else SAFE_QUERY_LIMIT, sort_col=ReturnRequest.created_at, desc=True)
    else:
        query = base_query
        if limit is not None:
            query = query.limit(limit)
        requests = query.all()'''),
    ],
)

print("ALL CONTROLLER PATCHES APPLIED")
