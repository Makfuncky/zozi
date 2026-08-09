"""Build an inventory of PERF2/PERF4 findings with code context, and apply a
conservative automatic classification (REAL vs FALSE_POSITIVE) that can be
manually reviewed. This script does NOT modify source files.
"""
import ast
import json
import re
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
REPORT = REPORT = REPO / "SYSTEM_AUDIT_REPORT.md"

text = REPORT.read_text(encoding="utf-8")
lines = text.splitlines()

# ---- Parse PERF2 and PERF4 rows from the report tables ----
perf2 = []  # (file, [lines])
perf4 = []  # (file, line)

for ln in lines:
    if "| PERF2 |" in ln and "backend |" in ln:
        # | 🟡 | PERF2 | backend | `backend\services\foo.py` | N possible ... (lines: a, b, c) | ...
        m = re.search(r"`([^`]+)`\s*\|\s*(\d+)\s*possible.*?\(lines:\s*([^)]*)\)", ln)
        if not m:
            continue
        fpath = m.group(1).replace("\\", "/")
        linestr = m.group(3)
        nums = [int(x) for x in re.findall(r"\d+", linestr)]
        perf2.append((fpath, nums))
    elif "| PERF4 |" in ln and "services |" in ln:
        # | 🟡 | PERF4 | services | `backend\services\foo.py:53` | unbounded ...
        m = re.search(r"`([^`]+)`", ln)
        if not m:
            continue
        ref = m.group(1).replace("\\", "/")
        if ":" in ref:
            fpath, lnum = ref.rsplit(":", 1)
            try:
                perf4.append((fpath, int(lnum)))
            except ValueError:
                pass

print(f"Parsed PERF2 files: {len(perf2)}  (total flags {sum(len(n) for _,n in perf2)})")
print(f"Parsed PERF4 flags: {len(perf4)}")


# ---- Reference / small-table model names that legitimately return all rows ----
REFERENCE_MODELS = {
    "country", "countries", "currency", "currencies", "setting", "settings",
    "config", "configuration", "featureflag", "feature_flag", "flag", "role",
    "roles", "permission", "permissions", "enum", "status", "status_type",
    "category", "categories", "type", "types", "tier", "tiers", "plan", "plans",
    "plan_type", "unit", "units", "uom", "tax", "tax_rate", "taxrate", "region",
    "language", "locale", "paymentmethod", "payment_method", "shippingmethod",
    "shipping_method", "tag", "label", "attribute", "attributes", "option",
    "options", "grade", "level", "rank", "department", "department_type",
    "designation", "title", "gender", "maritalstatus", "bloodgroup", "bank",
    "banks", "tenant", "tenant_config", "systemconfig", "preference",
    "lookup", "lookup_table", "codetype", "codename", "state", "province",
    "city", "district", "brand", "brands", "color", "size", "sizes", "reason",
    "reasons", "template", "templates",
}

# User-facing / large transactional tables where unbounded .all() is a real risk
LARGE_TABLES = {
    "user", "users", "customer", "customers", "order", "orders", "product",
    "products", "transaction", "transactions", "payment", "payments",
    "invoice", "invoices", "shipment", "shipments", "supplier", "suppliers",
    "employee", "employees", "ledger", "journal", "entry", "entries",
    "event", "events", "log", "logs", "session", "message", "messages",
    "notification", "notification", "cart", "carts", "review", "reviews",
    "comment", "comments", "audit", "auditlog", "activity", "attendance",
    "payout", "payouts", "commission", "commissions", "ticket", "tickets",
    "asset", "assets", "task", "tasks", "job", "jobs", "report", "reports",
    "subscription", "subscriptions", "wallet", "wallets", "transfer",
    "transfers", "refund", "refunds", "claim", "claims", "dispute", "disputes",
}


def model_from_query(line: str):
    """Heuristically extract a model name from a query/scalars line."""
    m = re.search(r"\b(query|select)\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\b", line)
    if m:
        return m.group(2)
    m = re.search(r"\bfrom\s*\(?\s*([A-Za-z_][A-Za-z0-9_]*)\b", line)
    if m:
        return m.group(1)
    m = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\.__table__", line)
    if m:
        return m.group(1)
    return None


def classify_perf4(fpath, lnum):
    """Return (classification, reason)."""
    src = (REPO / fpath)
    if not src.exists():
        return ("UNKNOWN", "source file missing")
    src_lines = src.read_text(encoding="utf-8", errors="ignore").splitlines()
    if lnum < 1 or lnum > len(src_lines):
        return ("UNKNOWN", "line out of range")
    line = src_lines[lnum - 1]
    # Only flag lines that actually call .all()
    if ".all()" not in line:
        return ("FALSE_POSITIVE", "no .all() on flagged line (report/scan mismatch)")
    # Scan a wide window (statement may span lines) to find the model.
    window = "\n".join(src_lines[max(0, lnum - 12): min(len(src_lines), lnum + 2)])
    model = model_from_query(window)
    has_filter = ".filter(" in window
    if model:
        low = model.lower()
        for ref in REFERENCE_MODELS:
            if ref in low:
                return ("FALSE_POSITIVE", f"loads reference/small table '{model}'")
        for lg in LARGE_TABLES:
            if lg in low:
                if has_filter:
                    return ("REAL_FILTERED", f"large table '{model}' but .filter()-bounded (low risk)")
                return ("REAL_UNBOUNDED", f"large table '{model}' with NO .filter() -> truly unbounded, needs limit")
    # Heuristics for obvious non-query .all() (list/dict .all() misuse etc.)
    stripped = line.strip()
    if re.search(r"\.all\(\)\s*$", stripped) and "query" not in window and "select" not in window:
        if "scalars" in window or "scalar" in window:
            return ("REVIEW", "scalars().all() on unidentified model")
        return ("REVIEW", "list/dict .all() (non-ORM) — manual check")
    return ("REVIEW", "ORM .all() model not identified; manual check needed")


def _call_has_attr(func, attrs):
    cur = func
    depth = 0
    while cur is not None and depth < 32:
        if isinstance(cur, ast.Attribute):
            if cur.attr in attrs:
                return True
            cur = cur.value
        elif isinstance(cur, ast.Call):
            cur = cur.func
        elif isinstance(cur, ast.Name):
            return cur.id in attrs
        else:
            break
        depth += 1
    return False


def get_perf2_snippet(fpath, lnum, window=12):
    src = (REPO / fpath)
    if not src.exists():
        return ""
    src_lines = src.read_text(encoding="utf-8", errors="ignore").splitlines()
    if lnum < 1 or lnum > len(src_lines):
        return ""
    return "\n".join(src_lines[max(0, lnum - window): min(len(src_lines), lnum + window)])


def classify_perf2(fpath, lnum):
    """AST-based: determine if the in-loop query is a genuine N+1 (depends on
    the loop variable) or a false positive (setup query / result iteration /
    nested function def)."""
    src = (REPO / fpath)
    if not src.exists():
        return ("UNKNOWN", "source file missing")
    tree = ast.parse(src.read_text(encoding="utf-8", errors="ignore"))
    # Find the enclosing loop for the flagged line
    loop_info = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and getattr(child, "lineno", 0) == lnum:
                    # Found the loop containing the flagged call
                    targets = []
                    if isinstance(node, (ast.For, ast.AsyncFor)):
                        targets = [n.id for n in ast.walk(node.target)
                                   if isinstance(n, ast.Name)]
                    # Gather source of the whole loop
                    src_lines = src.read_text(encoding="utf-8", errors="ignore").splitlines()
                    loop_src = "\n".join(
                        src_lines[max(0, node.lineno - 1): node.end_lineno])
                    call_src = "\n".join(
                        src_lines[max(0, child.lineno - 1): child.end_lineno])
                    # Count query-like calls inside the loop
                    q_calls = sum(
                        1 for c in ast.walk(node)
                        if isinstance(c, ast.Call) and _call_has_attr(c.func, {"query", "execute", "scalar", "scalars"})
                    )
                    # Genuine N+1 if the loop variable name appears in the call source
                    depends_on_loop = any(t in call_src for t in targets)
                    if targets and depends_on_loop:
                        return ("REAL_N+1", f"loop var {targets} referenced in query -> per-item lookup")
                    if q_calls > 1:
                        return ("REAL_N+1", f"{q_calls} query-like calls inside loop -> batch candidate")
                    return ("FALSE_POSITIVE", "single loop-scoped query not depending on loop var (setup/iteration)")
    return ("UNKNOWN", "could not locate enclosing loop")


# ---- Build inventory ----
inventory = {"perf2": [], "perf4": []}

for fpath, nums in perf2:
    for n in nums:
        cls, reason = classify_perf2(fpath, n)
        inventory["perf2"].append({
            "file": fpath, "line": n, "classification": cls,
            "reason": reason, "snippet": get_perf2_snippet(fpath, n),
        })

for fpath, lnum in perf4:
    cls, reason = classify_perf4(fpath, lnum)
    inventory["perf4"].append({
        "file": fpath, "line": lnum, "classification": cls, "reason": reason,
    })

# ---- Summaries ----
from collections import Counter
c4 = Counter(x["classification"] for x in inventory["perf4"])
c2 = Counter(x["classification"] for x in inventory["perf2"])
print("\nPERF4 classification summary:", dict(c4))
print("PERF2 classification summary:", dict(c2))

out = REPO / "_extra_files" / "perf_inventory.json"
out.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
print(f"Wrote inventory -> {out}")

real4 = [x for x in inventory["perf4"] if x["classification"].startswith("REAL")]
print(f"\nPERF4 REAL* count: {len(real4)}")
for x in real4:
    print(f"  {x['file']}:{x['line']}  [{x['classification']}] {x['reason']}")

print(f"\nPERF2 REAL_N+1 count: {c2.get('REAL_N+1',0)}")
for x in inventory["perf2"]:
    if x["classification"] == "REAL_N+1":
        print(f"  {x['file']}:{x['line']}  {x['reason']}")
