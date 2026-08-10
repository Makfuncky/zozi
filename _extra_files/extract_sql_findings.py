import os

BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

# (relative_path, [line numbers])
findings = {
    "seed_all.py": [292],
    "utils/rls_interceptor.py": [496, 498],
    "services/employee_activity_logger.py": [147, 270, 281],
    "services/employee_communication_service.py": [502],
    "services/financial_reports_service.py": [526, 537, 582],
    "services/performance_service.py": [333],
    "routers/admin_logistics_operations.py": [2065],
    "routers/employee_hr_health.py": [85, 98, 122, 136, 148, 174],
    "services/command_center_background.py": [57],
    "services/fraud_detection_service.py": [944],
    "services/logistics_engine.py": [160],
    "services/order_tracking_service.py": [737, 375],
    "services/permission_service.py": [77, 85],
    "services/transactional_email_service.py": [146],
    "scripts/add_schema_to_models.py": [100],
    "routers/admin_identity_operations.py": [120],
    "routers/admin_orders_status.py": [182],
    "routers/logistics_reporting.py": [263],
    "providers/legacy/br_08.py": [376],
    "middleware/behavioral_analytics.py": [103],
    "middleware/rate_limit_middleware.py": [225],
    "jobs/threat_feed_updater.py": [52],
    "controllers/cart_controller.py": [91],
    "controllers/logistics_partner_controller.py": [3182],
    "controllers/orders_controller.py": [181],
    "controllers/supplier_controller.py": [1070],
    "services/chat_enrichment.py": [154, 183, 235],
    "services/hr/ess_write_service.py": [47],
    "scripts/add_schema_declarations.py": [139],
    "scripts/add_schema_declarations_debug.py": [134],
    "routers/customer_payments.py": [81],
    "controllers/command_center_controller.py": [57],
}

CTX = 10

out = []
for rel, lines in findings.items():
    path = os.path.join(BASE, rel)
    out.append("=" * 90)
    out.append(f"FILE: {rel}")
    out.append("=" * 90)
    if not os.path.exists(path):
        out.append(f"  [NOT FOUND: {path}]")
        continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.readlines()
    maxline = len(content)
    for ln in lines:
        start = max(1, ln - CTX)
        end = min(maxline, ln + CTX)
        out.append(f"--- around line {ln} (showing {start}-{end}) ---")
        for i in range(start, end + 1):
            marker = ">>>" if i == ln else "   "
            txt = content[i - 1].rstrip("\n")
            out.append(f"{marker} {i:5}: {txt}")
        out.append("")

text = "\n".join(out)
with open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\sql_findings_dump.txt", "w", encoding="utf-8") as f:
    f.write(text)
print(f"Wrote {len(out)} lines to sql_findings_dump.txt")
print(f"Files processed: {len(findings)}")
