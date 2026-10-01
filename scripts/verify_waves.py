"""Final comprehensive verification of all Wave 1-4 fixes."""
import os
import re
import sys

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
BACKEND = os.path.join(ROOT, "backend")

results = []


def check(name, status, detail=""):
    results.append((name, status, detail))
    mark = "PASS" if status else "FAIL"
    line = f"  [{mark}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)


def rel(path):
    return os.path.relpath(path, ROOT)


# ============================================================
# C1: Duplicate security_dependencies.py deleted
# ============================================================
print("\n=== C1: Duplicate security_dependencies.py ===")
dup = os.path.join(BACKEND, "domains", "security", "services", "iam", "security_dependencies.py")
canonical = os.path.join(BACKEND, "domains", "accounts", "services", "auth", "security_dependencies.py")
check("C1a: Duplicate deleted", not os.path.exists(dup), rel(dup))
check("C1b: Canonical exists", os.path.exists(canonical), rel(canonical))

# ============================================================
# C3: Stale DOMAIN_ALLOWLIST entries removed
# ============================================================
print("\n=== C3: Stale DOMAIN_ALLOWLIST entries ===")
allowlist_path = os.path.join(BACKEND, "DOMAIN_ALLOWLIST.yaml")
if os.path.exists(allowlist_path):
    raw = open(allowlist_path, encoding="utf-8", errors="replace").read()
    has_core_users = "core.users" in raw
    has_domains_payments = "domains.payments." in raw
    check("C3a: No core.users entries", not has_core_users)
    check("C3b: No domains.payments.* entries", not has_domains_payments)
else:
    check("C3: Allowlist file exists", False, rel(allowlist_path))

# ============================================================
# H6: FX rates configurable
# ============================================================
print("\n=== H6: FX rates configurable ===")
fx_rates = os.path.join(BACKEND, "providers", "finance", "fx_rates.py")
settlement = os.path.join(BACKEND, "domains", "suppliers", "services", "settlement", "multi_currency_settlement.py")
check("H6a: fx_rates.py exists", os.path.exists(fx_rates), rel(fx_rates))

if os.path.exists(settlement):
    content = open(settlement, encoding="utf-8", errors="replace").read()
    has_import = "providers.finance" in content or "from providers" in content
    check("H6b: settlement imports from providers.finance", has_import, rel(settlement))
elif os.path.exists(settlement.replace("multi_currency_settlement", "settlement")):
    alt = settlement.replace("multi_currency_settlement", "settlement")
    content = open(alt, encoding="utf-8", errors="replace").read()
    has_import = "providers.finance" in content or "from providers" in content
    check("H6b: settlement imports from providers.finance", has_import, rel(alt))
else:
    check("H6b: settlement file exists", False, rel(settlement))

# ============================================================
# H4: Unbounded queries limited
# ============================================================
print("\n=== H4: Unbounded queries limited ===")
h4_files = [
    os.path.join(BACKEND, "domains", "orders", "services", "core", "admin.py"),
    os.path.join(BACKEND, "domains", "finance", "services", "payouts", "payout_batch_service.py"),
    os.path.join(BACKEND, "domains", "hr", "services", "ess_service.py"),
    os.path.join(BACKEND, "domains", "hr", "services", "ess", "ess_service.py"),
]
for fpath in h4_files:
    if os.path.exists(fpath):
        content = open(fpath, encoding="utf-8", errors="replace").read()
        has_limit = ".limit(" in content
        check(f"H4: {rel(fpath)} has .limit()", has_limit)
    else:
        check(f"H4: {rel(fpath)} exists", False)

# ============================================================
# H3: OFFSET pagination fixed (keyset)
# ============================================================
print("\n=== H3: Keyset pagination ===")
h3_files = [
    os.path.join(BACKEND, "domains", "orders", "services", "core", "admin.py"),
    os.path.join(BACKEND, "domains", "finance", "services", "payouts", "payout_batch_service.py"),
]
for fpath in h3_files:
    if os.path.exists(fpath):
        content = open(fpath, encoding="utf-8", errors="replace").read()
        has_keyset = bool(
            re.search(r">\s*:last_(?:id|cursor)", content)
            or re.search(r">=\s*:cursor", content)
            or re.search(r"where.*id\s*>\s*:", content, re.IGNORECASE)
        )
        has_offset = ".offset(" in content.lower()
        check(f"H3: {rel(fpath)} uses keyset", has_keyset)
        if has_offset:
            check(f"H3: {rel(fpath)} no offset()", False, "still has .offset()")
    else:
        check(f"H3: {rel(fpath)} exists", False)

# ============================================================
# M1: bcrypt rounds=13
# ============================================================
print("\n=== M1: bcrypt rounds=13 ===")
auth_path = os.path.join(BACKEND, "infrastructure", "utils", "auth.py")
if os.path.exists(auth_path):
    content = open(auth_path, encoding="utf-8", errors="replace").read()
    match = re.search(r"bcrypt\.gensalt\s*\(.*?rounds\s*=\s*13", content, re.DOTALL)
    check("M1: bcrypt rounds=13", match is not None)
else:
    check("M1: auth.py exists", False)

# ============================================================
# M6: SQL injection fixed
# ============================================================
print("\n=== M6: SQL injection fixed ===")
m6_files = [
    os.path.join(BACKEND, "domains", "hr", "services", "ess_service.py"),
    os.path.join(BACKEND, "domains", "hr", "services", "ess", "ess_service.py"),
]
for fpath in m6_files:
    if os.path.exists(fpath):
        content = open(fpath, encoding="utf-8", errors="replace").read()
        has_fstring_sql = bool(
            re.search(r'f["\'].*SELECT', content, re.IGNORECASE)
            or re.search(r'execute\s*\(\s*f["\']', content, re.IGNORECASE)
        )
        check(f"M6: {rel(fpath)} no f-string SQL", not has_fstring_sql)
    else:
        check(f"M6: {rel(fpath)} exists", False)

# ============================================================
# M8: Controller renamed
# ============================================================
print("\n=== M8: Controller renamed ===")
new_svc = os.path.join(BACKEND, "domains", "orders", "services", "logistics_partner_service.py")
old_ctrl = os.path.join(BACKEND, "domains", "orders", "services", "logistics_partner_controller.py")
check("M8a: New service exists", os.path.exists(new_svc), rel(new_svc))
check("M8b: Old controller deleted", not os.path.exists(old_ctrl), rel(old_ctrl))

# ============================================================
# Compile check
# ============================================================
print("\n=== Compile Check ===")
import py_compile

compile_files = [
    os.path.join(BACKEND, "infrastructure", "utils", "auth.py"),
    os.path.join(BACKEND, "domains", "orders", "services", "logistics_partner_service.py"),
    os.path.join(BACKEND, "domains", "orders", "services", "core", "admin.py"),
    os.path.join(BACKEND, "domains", "finance", "services", "payouts", "payout_batch_service.py"),
    os.path.join(BACKEND, "domains", "hr", "services", "ess_service.py"),
    os.path.join(BACKEND, "domains", "hr", "services", "ess", "ess_service.py"),
    os.path.join(BACKEND, "providers", "finance", "fx_rates.py"),
    os.path.join(BACKEND, "domains", "accounts", "services", "auth", "security_dependencies.py"),
    os.path.join(BACKEND, "domains", "suppliers", "services", "settlement", "multi_currency_settlement.py"),
]

compile_pass = 0
compile_fail = 0
for fpath in compile_files:
    if os.path.exists(fpath):
        try:
            py_compile.compile(fpath, doraise=True)
            compile_pass += 1
            print(f"  [OK] {rel(fpath)}")
        except py_compile.PyCompileError as e:
            compile_fail += 1
            print(f"  [FAIL] {rel(fpath)} — {e}")
    else:
        print(f"  [SKIP] {rel(fpath)} not found")

check("Compile check", compile_fail == 0, f"{compile_pass} passed, {compile_fail} failed")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("VERIFICATION SUMMARY")
print("=" * 60)
passed = sum(1 for _, s, _ in results if s)
failed = sum(1 for _, s, _ in results if not s)
total = len(results)

for name, status, detail in results:
    mark = "PASS" if status else "FAIL"
    line = f"  [{mark}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)

print(f"\nTotal: {passed}/{total} passed, {failed} failed")
if failed == 0:
    print("ALL CHECKS PASSED")
else:
    print(f"WARNING: {failed} check(s) failed")
    sys.exit(1)
