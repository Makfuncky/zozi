import os

write_patterns = ['db.add', 'db.commit', 'db.delete', 'session.add', 'session.commit', 'session.delete', 'db.execute']
files_to_check = [
    r'backend\routers\addresses.py',
    r'backend\routers\admin_banners.py',
    r'backend\routers\admin_categories.py',
    r'backend\routers\admin_email.py',
    r'backend\routers\admin_logistics.py',
    r'backend\routers\admin_orders.py',
    r'backend\routers\admin_products.py',
    r'backend\routers\admin_suppliers.py',
    r'backend\routers\admin_users.py',
    r'backend\routers\banners.py',
    r'backend\routers\cart.py',
    r'backend\routers\categories.py',
    r'backend\routers\chat_enrichment.py',
    r'backend\routers\command_center.py',
    r'backend\routers\commission.py',
    r'backend\routers\countries.py',
    r'backend\routers\country_admin.py',
    r'backend\routers\country_payouts.py',
    r'backend\routers\country_staff.py',
    r'backend\routers\coupons.py',
    r'backend\routers\email.py',
    r'backend\routers\email_controller.py',
    r'backend\routers\ess.py',
    r'backend\routers\fraud_detection.py',
    r'backend\routers\internal_channels.py',
    r'backend\routers\logistics.py',
    r'backend\routers\logistics_partner.py',
    r'backend\routers\permissions.py',
    r'backend\routers\products.py',
    r'backend\routers\push_notifications.py',
    r'backend\routers\reviews.py',
    r'backend\routers\supplier.py',
    r'backend\routers\supplier_orders.py',
    r'backend\routers\supplier_products.py',
    r'backend\routers\wishlist.py',
    r'backend\routers\ws_chat.py',
    r'backend\controllers\ai_controller.py',
    r'backend\controllers\treasury\admin_payouts_controller.py',
    r'backend\controllers\supplier\admin_suppliers_controller.py',
    r'backend\controllers\supplier\supplier_controller.py',
    r'backend\controllers\orders\admin_orders_controller.py',
    r'backend\controllers\orders\orders_controller.py',
    r'backend\controllers\country\country_controller.py',
    r'backend\controllers\commerce\package.py',
    r'backend\controllers\catalog\products.py',
    r'backend\controllers\catalog\products_controller.py',
    r'backend\controllers\ai\chatbot_controller.py',
]

real_w1 = {}
false_pos = []

for fpath in files_to_check:
    if not os.path.exists(fpath):
        continue
    with open(fpath, 'r', errors='replace') as f:
        flines = f.readlines()
    writes = []
    for i, line in enumerate(flines, 1):
        stripped = line.strip()
        if not stripped.startswith('#') and not stripped.startswith('"""'):
            for p in write_patterns:
                if p in stripped:
                    writes.append((i, p, stripped[:120]))
    if writes:
        real_w1[fpath] = writes
    else:
        false_pos.append(fpath)

print("=== REAL W1 VIOLATIONS ===")
for fpath, writes in real_w1.items():
    print(f"--- {fpath} ({len(writes)} writes) ---")
    for ln, pat, text in writes:
        print(f"  L{ln} [{pat}]: {text}")

print()
print("=== FALSE POSITIVES (can skip) ===")
for fpath in false_pos:
    print(f"  {fpath}")
