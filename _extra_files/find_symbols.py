import re
from pathlib import Path
ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
syms = ["list_invoices","update_shipping_zone","SLA_ALERT_STATUSES","bulk_update_users_role_route","admin_create_thread","start_background_job","bulk_restore_coupons","bulk_archive_users","create_logistics_draft","assign_permission_to_role","_order_delivery_reference","assign_review"]
for s in syms:
    hits=[]
    for p in ROOT.rglob("*.py"):
        if "venv" in p.parts or "__pycache__" in p.parts: continue
        try:
            t=p.read_text(encoding="utf-8",errors="ignore")
        except: continue
        for i,line in enumerate(t.splitlines(),1):
            if s in line and ("def "+s in line or "class "+s in line or s+" =" in line or s+"=" in line):
                hits.append(f"{p.as_posix()}:{i}: {line.strip()[:100]}")
    print(f"=== {s} ({len(hits)}) ===")
    for h in hits[:15]:
        print("   ",h)
