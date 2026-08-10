"""Parse SYSTEM_AUDIT_REPORT.md section 6 and aggregate findings by domain module."""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "SYSTEM_AUDIT_REPORT.md"

SEV = {"🔴": "RED", "🟡": "YEL", "🟢": "INF"}

LINE_RE = re.compile(r"^- (🔴|🟡|🟢) \*\*([A-Z0-9]+)\*\* `([^`]+)` — (.*)$")

DOMAIN_KEYWORDS = {
    "security": ["security", "auth", "fraud", "rls", "csrf", "blacklist", "permission", "iam", "vault", "zero_trust", "biometric", "incident", "dlp", "ghost_watchdog", "device_binding"],
    "hr": ["employee", "hr_", "_hr", "payroll", "attendance", "leave", "coi", "dei", "hse", "lms", "offboarding", "onboarding", "background_check", "okr", "successor"],
    "treasury": ["treasury", "payout", "cash", "settlement", "bank", "fx", "payment_engine", "payment_orchestrator"],
    "finance": ["finance", "financial", "accounting", "ledger", "commission", "budget", "erp", "fiscal", "credit_control", "refund_posting"],
    "comms": ["comms", "chat", "message", "messaging", "email", "notification", "ticket", "sms", "push"],
    "geography": ["geography", "country", "geo", "city", "cities", "border", "currency", "localization"],
    "logistics": ["logistic", "shipment", "parcel", "carrier", "delivery", "dispatch", "fleet", "route", "tracking", "pod"],
    "catalog": ["catalog", "product", "category", "categories", "sku", "variant", "moderation", "filter"],
    "orders": ["order", "cart", "checkout", "return", "dispute", "fulfillment", "purchase"],
    "media": ["media", "image", "upload", "asset", "cdn", "video", "bg_remov", "free_image"],
    "supplier": ["supplier", "vendor", "kyc", "badge", "storefront", "contract"],
    "customer": ["customer", "address", "wishlist", "referral", "coupon", "loyalty", "segment", "profile"],
    "ai": ["ai_", "_ai", "chatbot", "ml_", "embedding", "ocr", "recommendation", "vision", "voice"],
    "analytics": ["analytics", "dashboard", "kpi", "metric", "report", "insight", "snapshot", "command_center"],
    "identity": ["identity", "user", "role", "session", "token", "mfa", "otp", "oauth", "rbac", "device"],
    "search": ["search", "autocomplete", "synonym"],
    "commerce": ["commerce", "promotion", "banner", "flash_sale", "campaign", "discount", "voucher"],
    "infra": ["main.py", "lifespan", "seed", "middleware", "database", "alembic", "migration", "db/", "db\\"],
}


def classify(path: str) -> str:
    p = path.lower().replace("\\", "/")
    scores = Counter()
    for dom, kws in DOMAIN_KEYWORDS.items():
        for kw in kws:
            if kw in p:
                scores[dom] += 1
    if not scores:
        return "other"
    return scores.most_common(1)[0][0]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    text = REPORT.read_text(encoding="utf-8", errors="replace").splitlines()
    start = next(i for i, l in enumerate(text) if l.startswith("## 6. All Findings by Domain"))
    end = next(i for i, l in enumerate(text) if l.startswith("## 7. "))
    findings = []
    for line in text[start:end]:
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        sev, code, loc, msg = m.groups()
        findings.append((SEV[sev], code, loc, msg))

    print(f"parsed findings: {len(findings)}")

    by_dom = defaultdict(lambda: Counter())
    by_dom_codes = defaultdict(Counter)
    by_dom_files = defaultdict(set)
    for sev, code, loc, msg in findings:
        f = loc.split(":")[0]
        dom = classify(f)
        by_dom[dom][sev] += 1
        by_dom_codes[dom][code] += 1
        by_dom_files[dom].add(f)

    rows = sorted(by_dom.items(), key=lambda kv: (-kv[1]["RED"] * 10 - kv[1]["YEL"]))
    print(f"\n{'domain':<14}{'RED':>6}{'YEL':>6}{'INF':>6}{'files':>7}  top codes")
    for dom, c in rows:
        top = ", ".join(f"{k}:{v}" for k, v in by_dom_codes[dom].most_common(8))
        print(f"{dom:<14}{c['RED']:>6}{c['YEL']:>6}{c['INF']:>6}{len(by_dom_files[dom]):>7}  {top}")

    # detail for a requested domain
    if len(sys.argv) > 1:
        want = sys.argv[1]
        print(f"\n=== detail for {want} ===")
        det = defaultdict(list)
        for sev, code, loc, msg in findings:
            f = loc.split(":")[0]
            if classify(f) != want:
                continue
            det[f].append((sev, code, loc, msg))
        order = sorted(det.items(), key=lambda kv: -sum(1 for s, *_ in kv[1] if s == "RED") * 10 - len(kv[1]))
        for f, items in order:
            red = sum(1 for s, *_ in items if s == "RED")
            print(f"\n--- {f}  (RED {red} / TOTAL {len(items)})")
            for sev, code, loc, msg in items:
                print(f"   [{sev}] {code:<7} {loc} :: {msg[:170]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
