import json
import sqlite3
import sys
sys.path.insert(0, '.')
from scripts.seed_loader import seed_products, _load_json, _filter_by_country

conn = sqlite3.connect('var/zozi.db')
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()
try:
    n = seed_products(cur, "ALL")
    conn.commit()
    print(f"products: {n} rows")
    for r in cur.execute("SELECT id, name, supplier_id, country_code FROM products"):
        print(" ", r)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
