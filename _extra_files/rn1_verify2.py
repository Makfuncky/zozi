import importlib.util, time, re, os, sys

AUDIT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\scripts\system_trackers\system_architecture_audit.py"
spec = importlib.util.spec_from_file_location("sa_audit", AUDIT)
mod = importlib.util.module_from_spec(spec)
sys.modules["sa_audit"] = mod
spec.loader.exec_module(mod)

aliases = mod.PLACEMENT_ALIAS_TO_DOMAIN
stop = set(mod.PLACEMENT_STOP_TOKENS)
surfaces = {"public", "admin", "supplier", "logistics", "customer"}
routers_dir = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\routers"

def tokens(stem):
    return [x.lower() for x in re.split(r"[^A-Za-z0-9]+", stem) if x]

def score(stem):
    toks = tokens(stem)
    surface = next((x for x in toks if x in surfaces), None)
    domain = next((x for x in toks if x in aliases), None)
    has_op = False
    for x in toks:
        if len(x) < 3: continue
        if x in stop: continue
        if surface and x == surface: continue
        if domain and (x == domain or aliases.get(x) == domain): continue
        has_op = True; break
    missing = []
    if not surface: missing.append("surface")
    if not domain: missing.append("domain")
    if not has_op: missing.append("operation")
    return missing

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

existing = {f[:-3] for f in os.listdir(routers_dir) if f.endswith(".py")}
print("=== CANDIDATE VERIFICATION ===")
bad=0; coll=0
for old,new in cand.items():
    m = score(new)
    flag = "OK" if not m else "FAIL:"+",".join(m)
    if m: bad+=1
    c = "COLLISION!" if new in existing else ""
    if new in existing: coll+=1
    print("  %-40s -> %-45s %s %s" % (old,new,flag,c))
print("\nFailing RN1:", bad, "| Collisions:", coll)
