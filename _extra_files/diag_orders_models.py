import os, sys

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-audit")
os.environ.setdefault("CSRF_DISABLED", "true")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from models.orders.orders import Order  # canonical model

print("Order.__module__:", Order.__module__)
t = Order.__table__
print("tablename:", t.fullname)
idx_names = [i.name for i in t.indexes]
print("indexes:", idx_names)

cols = set(t.columns.keys())
print("has country_code:", "country_code" in cols)
print("has created_at:", "created_at" in cols)

composite_present = any(
    set(i.columns.keys()) == {"country_code", "created_at"}
    for i in t.indexes
)
print("composite (country_code, created_at) present:", composite_present)
