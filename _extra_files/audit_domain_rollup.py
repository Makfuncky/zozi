"""Read-only helper: roll up SYSTEM_AUDIT_REPORT.md findings by domain keyword.

Parses section 8 ("Problems by File") headers and aggregates RED/YELLOW counts
into coarse domain buckets so we can pick the most damaged module objectively.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

REPORT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\SYSTEM_AUDIT_REPORT.md")

HEADER_RE = re.compile(r"^### `([^`]+)`\s+\(🔴 (\d+) · 🟡 (\d+)\)")

DOMAIN_KEYWORDS = {
    "treasury": ("treasury", "cash_management", "cash_", "payout", "settlement", "payment_engine", "payment_orchestrator", "treasurer", "gateway_reconciliation"),
    "finance": ("finance", "accounting", "invoice", "commission", "general_ledger", "ledger", "financial", "expense", "je_", "period_close", "sub_ledger", "credit_control", "refund_posting"),
    "security": ("security", "auth", "fraud", "rls", "permission", "iam", "vault", "csrf", "blacklist", "biometric", "zero_trust", "triple_auth", "impossible_travel", "coi_middleware"),
    "geography": ("geography", "country", "geo", "cross_border", "localization", "currency"),
    "comms": ("comms", "comm_", "communication", "chat", "email", "notification", "messaging", "ticket", "escalation", "video", "websocket", "ws_"),
    "orders": ("orders", "order_", "cart", "checkout", "return", "dispute", "fulfillment", "ghost"),
    "catalog": ("catalog", "product", "categor", "moderation", "variant", "sku"),
    "logistics": ("logistics", "shipment", "parcel", "carrier", "delivery", "route", "fleet", "shop_location"),
    "supplier": ("supplier", "vendor", "kyc", "onboarding", "badge", "storefront"),
    "hr": ("hr_", "employee", "payroll", "attendance", "lms", "okr", "succession", "shift", "offboarding", "dei", "travel"),
    "media": ("media", "image", "bg_remov", "upload", "asset", "video_"),
    "ai": ("ai_", "chatbot", "ocr", "vision", "embedding", "ml_", "system_ai"),
    "analytics": ("analytics", "dashboard", "command_center", "report", "kpi", "metric", "telemetry"),
    "identity": ("identity", "users", "user_", "session", "device", "mfa", "otp", "role"),
    "platform": ("main.py", "lifespan", "seed_all", "db\\", "db/", "middleware", "utils", "tools", "alembic", "jobs", "tasks", "settings"),
}


def bucket(path: str) -> str:
    low = path.lower().replace("\\", "/")
    best = None
    for dom, kws in DOMAIN_KEYWORDS.items():
        for kw in kws:
            k = kw.replace("\\", "/")
            if k in low:
                # prefer more specific (longer) keyword match
                if best is None or len(k) > best[1]:
                    best = (dom, len(k))
    return best[0] if best else "other"


def main() -> int:
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    red = defaultdict(int)
    yel = defaultdict(int)
    files = defaultdict(list)
    for line in text.splitlines():
        m = HEADER_RE.match(line)
        if not m:
            continue
        path, r, y = m.group(1), int(m.group(2)), int(m.group(3))
        dom = bucket(path)
        red[dom] += r
        yel[dom] += y
        files[dom].append((r, y, path))

    rows = sorted(red.keys(), key=lambda d: (-red[d], -yel[d]))
    print(f"{'domain':<12} {'RED':>6} {'YEL':>6} {'files':>6}")
    for d in rows:
        print(f"{d:<12} {red[d]:>6} {yel[d]:>6} {len(files[d]):>6}")

    focus = sys.argv[1] if len(sys.argv) > 1 else None
    if focus:
        print(f"\n--- files in domain '{focus}' ---")
        for r, y, p in sorted(files[focus], key=lambda t: (-t[0], -t[1])):
            print(f"  R{r:<3} Y{y:<3} {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
