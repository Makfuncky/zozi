import os, re, json

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
ROUTERS = os.path.join(ROOT, "backend", "routers")

files = sorted(f for f in os.listdir(ROUTERS) if f.endswith(".py") and f != "__init__.py")

PREFIXED = {"admin", "supplier", "public", "customer", "country", "system", "logistics"}

# storefront commerce domains -> surface=store
STORE = {"products", "orders", "cart", "payments", "categories", "banners",
         "coupons", "wishlist", "reviews", "returns", "shipments", "addresses",
         "referrals", "flash_sales", "currencies", "currency", "trading",
         "cross_border", "parcel_tracking", "shop_locations", "countries",
         "commission", "invoices", "payments", "treasury", "finance"}

# platform / infra -> surface=core
CORE = {"auth", "users", "admin", "ai", "jobs", "automation", "workflows",
        "notifications", "email", "messaging", "comm", "chatbot", "upload",
        "uploads", "currency", "risk", "compliance", "audit", "csp_reporting",
        "frontend_errors", "hierarchy", "incident", "tickets", "okr", "ess",
        "lms", "payroll", "performance", "succession", "travel", "shift_handover",
        "onboarding", "permissions", "iam", "ediscovery", "fraud_detection",
        "export", "imports", "batch_upload", "upload_jobs", "video", "ws_chat",
        "internal_comms_channels", "email_controller", "push_notifications",
        "product_moderation", "product_verification", "product_videos",
        "accounting", "finance_automation", "finance_erp", "payout_approval",
        "customer_health", "hr_dashboard", "logistics_health"}

def classify(name):
    base = name[:-3]
    toks = base.split("_")
    if toks[0] in PREFIXED:
        surface = toks[0]
        rest = toks[1:]
    else:
        # decide surface
        if base in STORE or toks[0] in STORE:
            surface = "store"
        else:
            surface = "core"
        rest = toks
    # domain = first meaningful token group; operation = the rest
    # Heuristic: domain is the leading noun, operation is trailing qualifiers
    if not rest:
        domain, operation = "core", "routes"
    else:
        # operation candidates (trailing modifiers)
        OP_WORDS = {"management", "fulfillment", "tracking", "status", "creation",
                    "geography", "configuration", "operations", "analytics", "health",
                    "fallback", "imports", "settings", "promotions", "reporting",
                    "payments", "cash_position", "identity", "sync", "upload", "profile",
                    "products", "orders", "payouts", "finance", "documents", "reviews",
                    "trading", "supplier", "detection", "registration", "validation",
                    "permissions", "access", "api", "research", "messaging", "media",
                    "location", "channels", "unified", "dashboard", "automation",
                    "erp", "moderation", "verification", "videos", "audit", "catalog",
                    "commission", "banners", "cash", "email", "chat", "categories",
                    "users", "video", "jobs", "security", "comms", "commerce"}
        # find split point: longest domain prefix
        # default: domain = rest[0], operation = '_'.join(rest[1:]) or 'routes'
        domain = rest[0]
        operation = "_".join(rest[1:]) if len(rest) > 1 else "routes"
    new = f"{surface}_{domain}_{operation}"
    return new

mapping = {}
for f in files:
    new = classify(f)
    mapping[f] = new

# detect collisions
from collections import defaultdict
rev = defaultdict(list)
for old, new in mapping.items():
    rev[new].append(old)
collisions = {k: v for k, v in rev.items() if len(v) > 1}

out = []
for old in files:
    new = mapping[old]
    flag = "  <<< COLLISION" if new in collisions else ""
    out.append(f"{old:<42} -> {new}{flag}")

os.makedirs(os.path.join(ROOT, "_extra_files"), exist_ok=True)
with open(os.path.join(ROOT, "_extra_files", "rename_map_proposed.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
    fh.write("\n\nCOLLISIONS:\n")
    for k, v in collisions.items():
        fh.write(f"  {k} <= {v}\n")

print("\n".join(out))
print("\nTOTAL:", len(mapping), "COLLISIONS:", len(collisions))
