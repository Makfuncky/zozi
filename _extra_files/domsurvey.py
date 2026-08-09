import json, collections, re
rows = json.load(open("_extra_files/findings.json",encoding="utf-8"))
def norm(l): return l.replace("\\","/").split(":")[0]
S = {"\U0001f534":"RED","\U0001f7e1":"ADV","\U0001f7e2":"INFO"}
for r in rows: r["s"] = S.get(r["sev"], r["sev"])
DOMAINS = {
 "hr": r"(employee|payroll|attendance|leave|hr_|/hr/|hr\.py|lms|offboard|onboard_emp|hse|dei|coi|background_check|ess)",
 "logistics": r"(logistic|carrier|delivery|dispatch|fleet|geofence|geo_fence|parcel|pod|route|shipment|shipping|tracking)",
 "media": r"(media|image|upload|asset|storage|file_)",
 "orders": r"(order|cart|checkout|dispute|fulfil|return|purchase)",
 "catalog": r"(catalog|product|categor|inventory|search|filter|moderation)",
 "security": r"(auth|mfa|otp|fraud|csrf|biometric|blacklist|iam|incident|device_binding|permission|rbac|ghost)",
 "comms": r"(chat|comm|email|message|notification|push|sms|ticket|meeting)",
 "analytics": r"(analytic|dashboard|insight|kpi|metric|report|snapshot)",
 "geography": r"(geograph|countr|city|cities|currency|border|region)",
 "supplier": r"(supplier|vendor|kyc|badge|storefront)",
 "ai": r"(/ai|ai_|chatbot|embedding|ocr|recommend|_ai\.py|research)",
 "commerce": r"(coupon|discount|promotion|loyalty|referral|review|wishlist|flash_sale)",
 "treasury": r"(treasury|payout|payment|cash|settlement|reconcil|bank|gateway)",
 "finance": r"(finance|commission|accounting|billing|erp|ledger|invoice)",
}
print(f"{'domain':12} {'total':>6} {'RED':>5} {'files':>6}")
for d, pat in DOMAINS.items():
    p = re.compile(pat, re.I)
    sel = [r for r in rows if p.search(norm(r["loc"])) and norm(r["loc"]).startswith("backend")]
    red = sum(1 for r in sel if r["s"]=="RED")
    files = len(set(norm(r["loc"]) for r in sel))
    print(f"{d:12} {len(sel):6d} {red:5d} {files:6d}")
