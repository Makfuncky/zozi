import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACK = os.path.join(ROOT, "backend")

# 1) Fraud engine + threat updater: declare deps + rename param to canonical emit name
fraud_files = [
    "controllers/admin/admin_security_detection_controller.py",
    "controllers/public/public_security_detection_controller.py",
]
for rel in fraud_files:
    p = os.path.join(BACK, rel)
    lines = open(p, encoding="utf-8").read().split("\n")
    for idx, line in enumerate(lines):
        if line.strip().startswith("def ") and "engine: FraudScoringEngine" in line:
            lines[idx] = line.replace("engine: FraudScoringEngine", "fraud_engine: FraudScoringEngine")
            j = idx - 1
            while j >= 0 and not lines[j].lstrip().startswith("@"):
                j -= 1
            if j >= 0 and "deps=" not in lines[j]:
                d = lines[j].rstrip()
                d = d[:-1].rstrip() + ', deps=["fraud_engine"])'
                lines[j] = d
        if line.strip().startswith("def ") and "updater: ThreatFeedUpdater" in line:
            lines[idx] = line.replace("updater: ThreatFeedUpdater", "threat_updater: ThreatFeedUpdater")
            j = idx - 1
            while j >= 0 and not lines[j].lstrip().startswith("@"):
                j -= 1
            if j >= 0 and "deps=" not in lines[j]:
                d = lines[j].rstrip()
                d = d[:-1].rstrip() + ', deps=["threat_updater"])'
                lines[j] = d
        line = line.replace("engine=engine)", "engine=fraud_engine)")
        line = line.replace("updater=updater)", "updater=threat_updater)")
    open(p, "w", encoding="utf-8").write("\n".join(lines))

# 2) Flask-style typed path params {banner_id:int} -> {banner_id} (FastAPI invalid)
banner_files = [
    "controllers/admin/admin_logistics_operations_controller.py",
    "controllers/core/admin_controller.py",
]
for rel in banner_files:
    p = os.path.join(BACK, rel)
    text = open(p, encoding="utf-8").read()
    text = text.replace("{banner_id:int}", "{banner_id}")
    open(p, "w", encoding="utf-8").write(text)

# 3) coupons: drop conflicting "user" dep (admin already injects current_user)
rel = "controllers/public/customer_coupons_create_controller.py"
p = os.path.join(BACK, rel)
text = open(p, encoding="utf-8").read()
text = text.replace('deps=["admin", "db", "user"]', 'deps=["admin", "db"]')
open(p, "w", encoding="utf-8").write(text)

print("controller fixes applied")
