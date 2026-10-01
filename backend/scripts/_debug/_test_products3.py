import json
import sqlite3
import sys
sys.path.insert(0, '.')
from scripts.seed_loader import _load_json, _filter_by_country

conn = sqlite3.connect('var/zozi.db')
conn.execute("PRAGMA foreign_keys = OFF")
cur = conn.cursor()
data = _load_json("products_full.json").get("products", [])
p = data[0]
sql = "INSERT OR IGNORE INTO products (id, name, slug, description, short_description, ai_description, sku, barcode, price, compare_price, cost_price, stock, low_stock_threshold, weight, dimensions, materials, image_url, images, category, category_id, tags, attributes, supplier_id, country_code, is_active, is_featured, is_digital, is_verified, moderation_status, brand, color, sizes, rating, sales_count, meta_title, meta_description, is_approved, is_deleted, discount_starts_at, discount_ends_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
try:
    cur.execute(sql, (
        p["id"], p["name"], p["slug"], p.get("description"), p.get("short_description"),
        p.get("ai_description"), p["sku"], p.get("barcode"), p["price"], p.get("compare_price"),
        p.get("cost_price"), p.get("stock",0), p.get("low_stock_threshold",5), p.get("weight"),
        p.get("dimensions"), p.get("materials"), p.get("image_url"), p.get("images"),
        p.get("category"), p.get("category_id"), p.get("tags"), p.get("attributes"),
        p["supplier_id"], p["country_code"], 1 if p.get("is_active",True) else 0,
        1 if p.get("is_featured",False) else 0, 0, 1 if p.get("is_approved",True) else 0,
        "approved", p.get("brand"), p.get("color"), p.get("sizes"),
        p.get("rating",0.0), p.get("sales_count",0), p.get("meta_title"),
        p.get("meta_description"), 1 if p.get("is_approved",True) else 0, 0,
        p.get("discount_starts_at"), p.get("discount_ends_at"), "2026-09-04T22:00:00", "2026-09-04T22:00:00"
    ))
    conn.commit()
    print("OK")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
