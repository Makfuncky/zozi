import os, re

backend = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
stems = [
 "admin_core_management","admin_fallback_management","public_command_center_api_management",
 "public_command_center_management","public_contact_management","public_ediscovery_management",
 "public_escalation_management","public_ess_management","public_expenses_management",
 "public_flash_sales_management","public_frontend_errors_management","public_health_management",
 "public_hierarchy_management","public_imports_management","public_internal_channels_management",
 "public_jobs_management","public_location_api_management","public_messaging_management",
 "public_okr_management","public_payments_management","public_referrals_management",
 "public_shop_locations_management","public_tickets_management","public_trading_management",
 "public_translate_management","public_workflows_management",
]
# candidates
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
 "public_imports_management":"public_logistics_import_shipments",
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

# find references to each stem as a module path (routers.<stem> or backend.routers.<stem> or import <stem>)
ref_re = re.compile(r'(?:routers|backend\.routers)[.\s]' + r'([A-Za-z_][A-Za-z0-9_]*)')
# We'll scan whole backend for literal stem occurrences
results = {}
for stem in stems:
    refs = []
    for root, dirs, files in os.walk(backend):
        if "_extra_files" in root or "tests" in root.split(os.sep)[-1:]:
            # skip tests dir entirely to avoid noise? keep but mark
            pass
        for fn in files:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(root, fn)
            try:
                with open(p, encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception:
                continue
            for i, line in enumerate(lines, 1):
                if stem in line:
                    refs.append((os.path.relpath(p, backend), i, line.strip()[:120]))
    results[stem] = refs

for stem in stems:
    new = cand[stem]
    refs = results[stem]
    # exclude the router file itself
    ext = [r for r in refs if not r[0].startswith("routers/" + stem + ".py")]
    print("### %s -> %s  (refs outside self: %d)" % (stem, new, len(ext)))
    for r in ext:
        print("    %s:%d  %s" % r)
