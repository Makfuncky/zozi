import sqlite3

con = sqlite3.connect("data/app.db")
cur = con.cursor()
tabs = [r[0] for r in cur.execute("select name from sqlite_master where type='table'")]
print("table_count", len(tabs))
audit_cols = {"created_at", "updated_at", "uuid", "version", "is_deleted", "deleted_at", "created_by", "updated_by"}
for t in ["orders", "users", "products", "media_assets", "import_shipments", "upload_jobs", "tenants"]:
    try:
        cols = [r[1] for r in cur.execute(f"PRAGMA table_info({t})")]
        hits = [c for c in cols if c in audit_cols]
        print(t, "->", hits if hits else "none")
    except Exception as e:
        print(t, "ERR", e)
con.close()
