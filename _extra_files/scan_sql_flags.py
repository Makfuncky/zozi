import re, pathlib, sys

ROOT = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
SKIP_DIRS = {"scripts", "tests"}

SEC_SQL_INJECTION_PATTERNS = [
    re.compile(r"f['\"].*SELECT.*\{", re.I),
    re.compile(r"f['\"].*INSERT.*\{", re.I),
    re.compile(r"f['\"].*UPDATE.*\{", re.I),
    re.compile(r"f['\"].*DELETE.*\{", re.I),
    re.compile(r"\.format\(.*(?:SELECT|INSERT|UPDATE|DELETE)", re.I),
    re.compile(r"%\s*(?:SELECT|INSERT|UPDATE|DELETE).*%\s*\(", re.I),
    re.compile(r"execute\(\s*f['\"]", re.I),
    re.compile(r"execute\(\s*['\"].*['\"]\s*\+", re.I),
]
SEC_SAFE_INTERPOLATION_RE = re.compile(
    r"\{(?:table_name|schema|column|field|index_name|constraint|order_by|sort_col)\}", re.I)
PARAM_BIND = re.compile(r":[\w]+|%\(\w+\)s|\?\s*[,)]", re.I)

def walk():
    for p in ROOT.rglob("*.py"):
        parts = set(p.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        yield p

print("=== SEC5-style f-string SQL with interpolation ===")
for p in sorted(walk()):
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        for rx in SEC_SQL_INJECTION_PATTERNS:
            if rx.search(line):
                rel = p.relative_to(ROOT)
                # collect interpolated tokens
                toks = re.findall(r"\{([^}]+)\}", line)
                safe = bool(SEC_SAFE_INTERPOLATION_RE.search(line))
                # check context for params
                ctx = "\n".join(lines[max(0,i-4):min(len(lines),i+1)])
                has_param = bool(PARAM_BIND.search(ctx))
                print(f"{rel}:{i} safeID={safe} paramctx={has_param} toks={toks}")
                print(f"    {line.strip()}")
                break

print()
print("=== SEC101-style text(f\"...\") ===")
sec101 = re.compile(r"text\s*\(\s*f['\"]", re.I)
for p in sorted(walk()):
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        if sec101.search(line):
            rel = p.relative_to(ROOT)
            toks = re.findall(r"\{([^}]+)\}", line)
            has_param = bool(PARAM_BIND.search(line))
            print(f"{rel}:{i} paramline={has_param} toks={toks}")
            print(f"    {line.strip()}")
