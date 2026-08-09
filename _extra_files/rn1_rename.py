import os, re, io

backend = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
routers = os.path.join(backend, "routers")

cand = {
 "admin_core_management":"admin_identity_user_governance",
 "admin_fallback_management":"admin_analytics_fallback_dashboard",
 "public_command_center_api_management":"public_analytics_command_center_api",
 "public_command_center_management":"public_analytics_command_center_dashboard",
 "public_contact_management":"public_comms_contact_messaging",
 "public_ediscovery_management":"public_audit_ediscovery_search",
 "public_escalation_management":"public_security_escalation_handling",
 "public_ess_management":"public_hr_ess_portal",
 "public_expenses_management":"public_hr_expenses_tracking",
 "public_flash_sales_management":"public_commerce_flash_sales",
 "public_frontend_errors_management":"public_analytics_frontend_telemetry",
 "public_health_management":"public_configuration_health_status",
 "public_hierarchy_management":"public_hr_hierarchy_org",
 "public_imports_management":"public_logistics_import_manifest",
 "public_internal_channels_management":"public_comms_internal_channels",
 "public_jobs_management":"public_configuration_jobs_status",
 "public_location_api_management":"public_geography_location_api",
 "public_messaging_management":"public_comms_messaging_center",
 "public_okr_management":"public_hr_okr_tracking",
 "public_payments_management":"public_gateway_payment_processing",
 "public_referrals_management":"public_commerce_referrals_tracking",
 "public_shop_locations_management":"public_logistics_shop_locations",
 "public_tickets_management":"public_comms_tickets_handling",
 "public_trading_management":"public_inventory_trading_operations",
 "public_translate_management":"public_configuration_translate_text",
 "public_workflows_management":"public_configuration_workflow_automation",
}

# 1) Rename files
for old, new in cand.items():
    src = os.path.join(routers, old + ".py")
    dst = os.path.join(routers, new + ".py")
    if not os.path.isfile(src):
        print("MISSING SRC:", src); continue
    if os.path.exists(dst):
        print("DST EXISTS:", dst); continue
    os.rename(src, dst)
    print("renamed", old, "->", new)

# 2) Update main.py router_names
mainp = os.path.join(backend, "main.py")
with open(mainp, encoding="utf-8") as f:
    text = f.read()
new_text = text
for old, new in cand.items():
    # only replace exact stem occurrences (module path tokens in tuples / comments)
    new_text = new_text.replace('"%s"' % old, '"%s"' % new)
    new_text = new_text.replace("`%s`" % old, "`%s`" % new)
    new_text = new_text.replace(old + ".py", new + ".py")
if new_text != text:
    with open(mainp, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("main.py updated")
else:
    print("main.py: no changes made")

# 3) Update import in public_command_center_management.py
cc = os.path.join(routers, "public_analytics_command_center_dashboard.py")
if os.path.isfile(cc):
    with open(cc, encoding="utf-8") as f:
        cct = f.read()
    old_imp = "from routers.public_command_center_api_management import router as command_router"
    new_imp = "from routers.public_analytics_command_center_api import router as command_router"
    if old_imp in cct:
        cct = cct.replace(old_imp, new_imp)
        with open(cc, "w", encoding="utf-8") as f:
            f.write(cct)
        print("command_center_management.py import updated")
    else:
        print("WARN: import line not found in", cc)
