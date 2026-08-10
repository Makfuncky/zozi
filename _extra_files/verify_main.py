import os, sys, importlib, logging
backend = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, backend); os.chdir(backend)
# silence noisy loggers
for n in ("","sqlalchemy","uvicorn"):
    logging.getLogger(n).setLevel(logging.CRITICAL)

import main
app = main.app

# Re-run the registry load logic to capture failures explicitly
fail = []
registered = 0
for r in app.routes:
    registered += 1

# reproduce failed_routers detection by importing each expected module
names = ["auth","users","products","orders","payments","admin_catalog_categories","countries",
 "logistics_operations","logistics_health","logistics_partner","logistics_orders","logistics_locations",
 "admin_finance_operations","jobs","treasury","admin_treasury","admin","system_notifications_operations",
 "system_search_operations","customer_reviews","customer_wishlist","customer_coupons","banners",
 "internal_chat_api_access","chatbot","employee_hr_operations","hr_dashboard","employee_hr_expenses_tracking",
 "export","admin_treasury_cash_position","invoices","commission","compliance","risk","admin_audit_operations",
 "supplier_documents","supplier","supplier_health","supplier_analytics","supplier_orders","supplier_payouts",
 "supplier_finance","supplier_products","supplier_profile","logistics_orders_v2","parcel_tracking","shop_locations",
 "cross_border","admin_geography_maps","country_admin","admin_geography_dropdown","country_staff","country_payouts",
 "country_auto_populate","admin_analytics_command_center_api","ai","system_ai_media","system_ai_upload",
 "admin_comms_entity_chat","admin_comms_entity_communication","internal_comms_internal_channels","onboarding",
 "admin_comms_proxy_communication","customer_translate","video_controller","travel","shift_handover","succession",
 "performance","okr","ediscovery","workflows","tickets","video","upload","flash_sales","admin_users","admin_products",
 "admin_orders","admin_settings","admin_promotions","admin_categories","admin_banners","admin_payouts",
 "payout_approval","admin_cash","admin_commission","admin_logistics","admin_email","admin_suppliers","admin_analytics",
 "admin_chat","admin_video","admin_fallback","accounting","finance_automation","finance_erp","addresses","returns",
 "admin_geography_operations","iam","currency","csp_reporting","product_videos","referrals","fraud_detection",
 "product_verification","public_suppliers","push_notifications","messaging","ws_chat","customer_contact","email",
 "customer_health","permissions","payroll","comm","admin_comms_unified","admin_security_escalation_handling","incident",
 "hierarchy","lms","product_moderation","shipments","system_geography_location_api","supplier_bg_ab_test","upload_jobs",
 "batch_upload","trading","imports","automation","system_ai_country_research","ai_research","frontend_errors",
 "admin_comms_enrichment","system_comms_email_enrichment","ess","email_controller"]

for name in names:
    try:
        importlib.import_module(f"routers.{name}")
    except ImportError:
        try:
            importlib.import_module(f"controllers.{name}")
        except Exception as e:
            fail.append((name, str(e)[:100]))
    except Exception as e:
        fail.append((name, "LOAD_ERR: "+str(e)[:120]))

print("TOTAL registry names:", len(names))
print("FAILED to import:", len(fail))
for n,e in fail:
    print("  FAIL", n, "->", e)
print("APP total routes:", registered)
