import json
import sqlite3
import sys
sys.path.insert(0, '.')
from scripts.seed_loader import _load_json, _filter_by_country, _exec_many

conn = sqlite3.connect('var/zozi.db')
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()

# Try the products insert manually
data = _load_json("products_full.json").get("products", [])
rows = _filter_by_country(data, "ALL")
print(f"Total product rows: {len(rows)}")
# Look at one row's first few fields
import sqlalchemy
for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'"):
    print("table products exists")
# Check the actual schema
for r in conn.execute("PRAGMA table_info(products)"):
    print(" col:", r[1], r[2])
