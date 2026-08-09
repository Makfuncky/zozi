import os, sys
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("APP_ENV","test"); os.environ.setdefault("SECRET_KEY","t")
os.environ.setdefault("SEED_ADMIN_PASSWORD","a"); os.environ.setdefault("CSRF_DISABLED","true")
mods = [
 "controllers.catalog.category_admin_controller",
 "controllers.catalog.product_controller",
 "controllers.catalog.product_moderation_controller",
 "services.catalog.category_service",
 "services.catalog.product_service",
 "services.catalog.product_moderation_service",
 "routers.public_categories_access","routers.public_products_access","routers.supplier_products",
 "routers.admin_products_governance","routers.admin_categories_governance","routers.public_product_moderation_access",
]
for m in mods:
    __import__(m)
print("ALL CATALOG LAYERS IMPORT OK")
