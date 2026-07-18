import sys, traceback
sys.path.insert(0, r"F:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")

try:
    from routers import (
        products, auth, orders, payments, admin, supplier,
        reviews, wishlist, notifications, categories, coupons, search, ai, translate, tickets, logistics,
        cart, email, currency, addresses, returns, push_notifications, chatbot, banners,
        invoices, logistics_partner, supplier_documents, product_verification, public_suppliers, jobs,
        cash_management, commission, countries, country_payouts,
        admin_products, admin_users, admin_orders, admin_logistics,
        admin_categories, admin_countries, admin_suppliers, admin_promotions,
        accounting, treasury,
    )
    print("SUCCESS: All routers imported from single statement (matches main.py)")
    print(f"  Total modules imported: {len([products, auth, orders, payments, admin, supplier, reviews, wishlist, notifications, categories, coupons, search, ai, translate, tickets, logistics, cart, email, currency, addresses, returns, push_notifications, chatbot, banners, invoices, logistics_partner, supplier_documents, product_verification, public_suppliers, jobs, cash_management, commission, countries, country_payouts, admin_products, admin_users, admin_orders, admin_logistics, admin_categories, admin_countries, admin_suppliers, admin_promotions, accounting, treasury])}")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

