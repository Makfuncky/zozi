"""Analyze all non-decorated controllers for auto-router migration eligibility."""
import os
import re
import ast

CONTROLLERS_DIR = "controllers"
ROUTERS_DIR = "routers"

# All non-decorated controllers
non_decorated = [
    "admin.admin_controller",
    "admin.admin_dashboard_controller",
    "admin.admin_supplier_trading_controller",
    "admin.admin_treasury_payments_controller",
    "admin.auth",
    "catalog.banner_controller",
    "catalog.categories_controller",
    "commerce.cart_controller",
    "commerce.coupons_controller",
    "commerce.flash_sale_controller",
    "commerce.promotion_controller",
    "comms.chatbot_controller",
    "comms.comm_controller",
    "finance.commission_controller",
    "finance.finance_controller",
    "finance.invoice_controller",
    "geography.country_communication_controller",
    "geography.country_controller",
    "hr.employees_controller",
    "hr.lms_controller",
    "identity.iam_controller",
    "logistics.logistics_orders_list_controller",
    "logistics.logistics_orders_v2_controller",
    "orders.disputes_controller",
    "orders.logistics_controller",
    "orders.logistics_partner_controller",
    "orders.returns_controller",
    "products.products_controller",
    "security.auth_controller",
    "supplier.supplier_analytics_controller",
    "supplier.supplier_controller",
    "supplier.supplier_document_controller",
    "treasury.cash_management_controller",
]

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"ERROR: {e}"

def has_self_router(content):
    """Check if controller defines its own APIRouter."""
    return "APIRouter" in content or "router = " in content or "@router." in content

def has_decorator_import(content):
    """Check if controller already imports auto_router decorators."""
    return "from modules.routers.generated.auto_router import" in content or "from core.route_contract import" in content

def has_commit(content):
    """Check for commit/flush patterns."""
    patterns = ["db.commit", "session.commit", "db.flush", "session.flush"]
    return [p for p in patterns if p in content]

def get_functions(content):
    """Extract function names from controller."""
    try:
        tree = ast.parse(content)
        return [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    except:
        return []

def find_router_files():
    """Map controller modules to router files."""
    router_map = {}
    for fn in os.listdir(ROUTERS_DIR):
        if not fn.endswith(".py") or fn == "__init__.py":
            continue
        fp = os.path.join(ROUTERS_DIR, fn)
        content = read_file(fp)
        if "AUTO-GENERATED" in content[:100]:
            continue
        # Find imports of controllers
        for mod in non_decorated:
            short = mod.split(".")[-1]
            if f"controllers.{mod}" in content or f"controllers.{mod.replace('_controller', '')}" in content:
                if mod not in router_map:
                    router_map[mod] = []
                router_map[mod].append(fn)
    return router_map

# Analyze each non-decorated controller
print("=" * 80)
print("NON-DECORATED CONTROLLERS ANALYSIS")
print("=" * 80)

for mod in non_decorated:
    parts = mod.split(".")
    filename = parts[-1] + ".py"
    subdir = os.path.join(*parts[:-1])
    path = os.path.join(CONTROLLERS_DIR, subdir, filename)
    
    if not os.path.exists(path):
        print(f"\n{mod}: FILE NOT FOUND at {path}")
        continue
    
    content = read_file(path)
    
    # Check various properties
    self_router = has_self_router(content)
    has_decor = has_decorator_import(content)
    commits = has_commit(content)
    functions = get_functions(content)
    
    # Determine eligibility
    reasons = []
    if self_router:
        reasons.append("SELF-ROUTING (defines own APIRouter)")
    if has_decor:
        reasons.append("ALREADY HAS DECORATOR IMPORT")
    if commits:
        reasons.append(f"HAS COMMIT/FLUSH: {commits}")
    
    # Check for test files
    test_name = f"tests/test_{parts[-1].replace('_controller', '')}.py"
    has_test = os.path.exists(test_name)
    
    print(f"\n--- {mod} ---")
    print(f"  Path: {path}")
    print(f"  Functions: {len(functions)} ({', '.join(functions[:5])}{'...' if len(functions) > 5 else ''})")
    print(f"  Self-router: {self_router}")
    print(f"  Has decorator import: {has_decor}")
    print(f"  Has commits/flush: {bool(commits)}")
    print(f"  Has test: {has_test}")
    if reasons:
        print(f"  ELIGIBILITY: NO - {', '.join(reasons)}")
    else:
        print(f"  ELIGIBILITY: YES (needs router mapping check)")

# Find router files
print("\n" + "=" * 80)
print("ROUTER FILE MAPPING")
print("=" * 80)

router_map = find_router_files()
for mod, routers in sorted(router_map.items()):
    print(f"  {mod}: {', '.join(routers)}")

# Check for controllers not in any router
unmapped = [m for m in non_decorated if m not in router_map]
if unmapped:
    print(f"\nUnmapped controllers (no router found): {len(unmapped)}")
    for m in unmapped:
        print(f"  {m}")
