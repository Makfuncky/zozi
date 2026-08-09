import importlib.util, time, re, sys

AUDIT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\scripts\system_trackers\system_architecture_audit.py"
t = time.time()
spec = importlib.util.spec_from_file_location("sa_audit", AUDIT)
mod = importlib.util.module_from_spec(spec)
sys.modules["sa_audit"] = mod
spec.loader.exec_module(mod)
print("IMPORT OK in %.1fs" % (time.time() - t))

aliases = mod.PLACEMENT_ALIAS_TO_DOMAIN
stop = set(mod.PLACEMENT_STOP_TOKENS)
print("alias map size:", len(aliases))
print("stop has 'management':", "management" in stop)

surfaces = {"public", "admin", "supplier", "logistics", "customer"}

def tokens(stem):
    return [x.lower() for x in re.split(r"[^A-Za-z0-9]+", stem) if x]

def score(stem):
    toks = tokens(stem)
    surface = None
    for x in toks:
        if x in surfaces:
            surface = x
            break
    domain = None
    for x in toks:
        if x in aliases:
            domain = aliases[x]
            break
    has_op = False
    for x in toks:
        if len(x) < 3:
            continue
        if x in stop:
            continue
        if surface and x == surface:
            continue
        if domain and (x == domain or aliases.get(x) == domain):
            continue
        has_op = True
        break
    missing = []
    if not surface:
        missing.append("surface")
    if not domain:
        missing.append("domain")
    if not has_op:
        missing.append("operation")
    return missing

# Current 26
current = [
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
print("\n=== CURRENT 26 (missing) ===")
for c in current:
    print(" ", c, "->", score(c))

# Candidate target names (surface_domain_operation)
candidates = {
 "admin_core_management": "admin_configuration_core_settings",
 "admin_fallback_management": "admin_configuration_fallback_settings",
 "public_command_center_api_management": "public_analytics_command_center_api",
 "public_command_center_management": "public_analytics_command_center_dashboard",
 "public_contact_management": "public_comms_contact_messaging",
 "public_ediscovery_management": "public_audit_ediscovery_search",
 "public_escalation_management": "public_security_escalation_handling",
 "public_ess_management": "public_hr_ess_portal",
 "public_expenses_management": "public_hr_expenses_tracking",
 "public_flash_sales_management": "public_commerce_flash_sales",
 "public_frontend_errors_management": "public_analytics_frontend_errors",
 "public_health_management": "public_configuration_health_status",
 "public_hierarchy_management": "public_hr_hierarchy_org",
 "public_imports_management": "public_catalog_import_bulk",
 "public_internal_channels_management": "public_comms_internal_channels",
 "public_jobs_management": "public_comms_jobs_scheduling",
 "public_location_api_management": "public_geography_location_api",
 "public_messaging_management": "public_comms_messaging_center",
 "public_okr_management": "public_hr_okr_tracking",
 "public_payments_management": "public_gateway_payment_processing",
 "public_referrals_management": "public_commerce_referrals_tracking",
 "public_shop_locations_management": "public_logistics_shop_locations",
 "public_tickets_management": "public_comms_tickets_handling",
 "public_trading_management": "public_finance_trading_desk",
 "public_translate_management": "public_configuration_translate_text",
 "public_workflows_management": "public_configuration_workflow_automation",
}
print("\n=== CANDIDATES (missing should be empty) ===")
bad = 0
for old, new in candidates.items():
    m = score(new)
    flag = "OK" if not m else "FAIL " + ",".join(m)
    if m:
        bad += 1
    print("  %-42s -> %-45s %s" % (old, new, flag))
print("\nCandidates failing:", bad)
