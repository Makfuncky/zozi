"""Independent re-derivations for the audit's aggregate count claims.

Most findings in this suite are not "this line is wrong" but "N occurrences of
a thing exist across a tree". Token matching cannot adjudicate a count, so the
verifier could only ever answer UNVERIFIABLE for them -- which is how 101
findings across 85 clusters stayed unresolved regardless of probe tuning.

Each function here RE-DERIVES its quantity from the working tree. They are
written as separate traversals from the scanners rather than imported from
them: importing the detector's own counter would make the probe agree with the
detector by construction, which is the failure mode this layer exists to
prevent. Where a measurement necessarily shares the detector's *definition*
(the law says "no `print()` in production code", so both count `print()`), the
independence is in the traversal, the scope and the exclusions -- which is
where the real defects have been: patterns matching across lines, tests
included in production counts, directories double-counted.

Every measurement returns ``(count, description)``. The count is the number of
occurrences of the *defect*; the probe holds while it is non-zero.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

# --------------------------------------------------------------------------- #
# scope
# --------------------------------------------------------------------------- #

BACKEND_CORE = ("domains", "modules", "rbac", "kernel", "infrastructure",
                "providers", "jobs", "middleware")

#: Excluded from every production count. Mirrors the walker in `zz_core.util`,
#: restated so these measurements do not depend on scanner internals.
_SKIP_DIRS = {".git", ".kilo", "node_modules", "__pycache__", ".pytest_cache",
              ".next", "dist", "build", "venv", ".venv", "logs", "var",
              "test-results", "playwright-report", "_extra_files"}


class Ctx:
    """Root plus the two traversals every measurement needs."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self._cache: dict[str, str | None] = {}

    def text(self, rel: str) -> str:
        rel = rel.replace("\\", "/")
        if rel not in self._cache:
            p = self.root / rel
            try:
                self._cache[rel] = p.read_text(encoding="utf-8-sig",
                                               errors="replace")
            except Exception:
                self._cache[rel] = None
        return self._cache[rel] or ""

    def py(self, dirs=BACKEND_CORE):
        """Backend Python source, tests and caches excluded."""
        for d in dirs:
            base = self.root / "backend" / d
            if not base.is_dir():
                continue
            for dirpath, dirnames, files in __import__("os").walk(base):
                dirnames[:] = [x for x in dirnames
                               if x not in _SKIP_DIRS and not x.startswith(".")]
                for fn in files:
                    if fn.endswith(".py"):
                        yield (Path(dirpath) / fn).relative_to(self.root).as_posix()

    def ts(self, sub: str = "frontend/web_app/src"):
        """Web-app TS/TSX/JS source."""
        base = self.root / sub
        if not base.is_dir():
            return
        for dirpath, dirnames, files in __import__("os").walk(base):
            dirnames[:] = [x for x in dirnames
                           if x not in _SKIP_DIRS and not x.startswith(".")]
            for fn in files:
                if fn.endswith((".ts", ".tsx", ".js", ".jsx")):
                    yield (Path(dirpath) / fn).relative_to(self.root).as_posix()

    def parse(self, rel: str):
        src = self.text(rel)
        if not src:
            return None
        try:
            return ast.parse(src)
        except SyntaxError:
            return None


def _count_over(ctx: Ctx, pattern: re.Pattern, rels, per_file=True) -> int:
    n = 0
    for rel in rels:
        n += len(pattern.findall(ctx.text(rel)))
    return n


# --------------------------------------------------------------------------- #
# backend: architecture / root discipline
# --------------------------------------------------------------------------- #

def m_root_temp_scripts(c: Ctx):
    """FILE-001 / Law 27: temp and debug scripts at backend root."""
    backend = c.root / "backend"
    hits = []
    for pat in ("_tmp_*.py", "health_test_*.py", "fix_*.py", "debug_*.py",
                "_audit_boot_check.py"):
        hits += [p.name for p in backend.glob(pat)]
    return len(hits), f"temp/debug script(s) at backend root ({len(hits)})"


def m_select_star(c: Ctx):
    """DB-011: `SELECT *` in backend core."""
    pat = re.compile(r"SELECT\s+\*\s+FROM", re.IGNORECASE)
    n = _count_over(c, pat, list(c.py(("domains", "modules"))) )
    n += _count_over(c, pat, [p.relative_to(c.root).as_posix()
                              for p in (c.root / "backend").glob("*.py")])
    return n, f"SELECT * usage(s) ({n})"


def m_offset_pagination(c: Ctx):
    """DB-012 / Law 222: OFFSET pagination in backend core."""
    n = _count_over(c, re.compile(r"\.offset\("), list(c.py()))
    return n, f"OFFSET pagination usage(s) ({n})"


def m_count_queries(c: Ctx):
    """PERF-003: `.count()` calls, expensive on large tables."""
    n = _count_over(c, re.compile(r"\.count\("), list(c.py()))
    return n, f".count() call(s) ({n})"


def m_leading_wildcard_ilike(c: Ctx):
    """DB-013: `ilike("%...")` cannot use a B-tree index."""
    pat = re.compile(r"ilike\(\s*[\"']%")
    n = _count_over(c, pat, list(c.py(("domains",))))
    return n, f"leading-wildcard ilike search(es) ({n})"


def m_relationship_without_lazy(c: Ctx):
    """DB-010 / DB-relationship-loading / Law 45: `relationship()` with no lazy=."""
    total = missing = 0
    for rel in c.py(("domains", "modules", "infrastructure")):
        tree = c.parse(rel)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            nm = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if nm != "relationship":
                continue
            total += 1
            if not any(k.arg == "lazy" for k in node.keywords):
                missing += 1
    return missing, f"relationship() without lazy= ({missing}/{total})"


def m_unguarded_global_mutation(c: Ctx):
    """Laws 74/214: test functions that mutate a global and never undo it."""
    cleanup = re.compile(r"monkeypatch|delenv|os\.environ\.pop|undo|restore|"
                         r"@pytest\.fixture|addfinalizer", re.M)
    mutate = re.compile(r"os\.environ\s*\[[^\]]+\]\s*=|os\.environ\.update\(")
    tests = c.root / "backend" / "tests"
    if not tests.is_dir():
        return 0, "test(s) leaking a global mutation (no tests dir)"
    n = 0
    for rel in sorted(p.relative_to(c.root).as_posix()
                      for p in tests.rglob("test_*.py")):
        tree = c.parse(rel)
        if tree is None:
            continue
        src = c.text(rel)
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            seg = ast.get_source_segment(src, fn) or ""
            if mutate.search(seg) and not cleanup.search(seg):
                n += 1
    return n, f"test function(s) leaking a global mutation ({n})"


def m_uncancelled_import(c: Ctx):
    """Rule hygiene: `import x` whose name is never referenced in the file."""
    n = 0
    for rel in c.py():
        tree = c.parse(rel)
        if tree is None:
            continue
        src = c.text(rel)
        names: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                names += [(a.asname or a.name.split(".")[0]) for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
                names += [(a.asname or a.name) for a in node.names]
        body_after = "\n".join(l for l in src.splitlines()
                               if not re.match(r"\s*(import|from)\s", l))
        for nm in names:
            if nm == "*":
                continue
            if not re.search(rf"\b{re.escape(nm)}\b", body_after):
                n += 1
    return n, f"uncancelled import(s) ({n})"


def m_deep_nesting(c: Ctx):
    """LOGIC-295: functions nested deeper than 4 blocks."""
    limit = 4
    worst = 0
    over = 0
    branch = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With,
              ast.AsyncWith, ast.Try)
    for rel in c.py():
        tree = c.parse(rel)
        if tree is None:
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            def depth(node, d=0):
                best = d
                for ch in ast.iter_child_nodes(node):
                    nd = d + 1 if isinstance(ch, branch) else d
                    best = max(best, depth(ch, nd))
                return best

            d = depth(fn)
            worst = max(worst, d)
            if d > limit:
                over += 1
    return over, f"function(s) nested deeper than {limit} (max {worst})"


# --------------------------------------------------------------------------- #
# backend: logging / config
# --------------------------------------------------------------------------- #

def m_print_in_production(c: Ctx):
    """OBS-004 / Law 58: `print()` outside tests."""
    pat = re.compile(r"(?<![\w.])print\(")
    n = 0
    for rel in c.py():
        tree = c.parse(rel)
        if tree is None:
            continue
        for node in ast.walk(tree):
            # `print` used as a name, not `self.print(...)`
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id == "print":
                n += 1
                break
    return n, f"print() call site(s) in backend core ({n} file(s))"


def m_raw_getenv(c: Ctx):
    """OPS-016 / Law 84: raw `os.getenv` reads in production paths."""
    pat = re.compile(r"os\.(?:getenv|environ\.get)\(")
    n = _count_over(c, pat, list(c.py()))
    return n, f"raw os.getenv read(s) ({n})"


def m_pii_logs(c: Ctx):
    """OBS-005: log calls whose arguments can carry PII or a secret."""
    risky = re.compile(r"password|secret|token|email|phone|card|pan|ssn|"
                        r"api_key|credential", re.I)
    n = 0
    for rel in c.py():
        tree = c.parse(rel)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            nm = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if nm not in ("debug", "info", "warning", "error", "critical",
                          "exception", "log"):
                continue
            if any(risky.search(ast.unparse(a)) for a in node.args):
                n += 1
    return n, f"log call(s) whose arguments may carry PII/secrets ({n})"


# --------------------------------------------------------------------------- #
# backend: anti-patterns (AP-*)
# --------------------------------------------------------------------------- #

def m_notimplementederror(c: Ctx):
    """AP-001: a function whose only body raises NotImplementedError."""
    n = 0
    for rel in c.py():
        tree = c.parse(rel)
        if tree is None:
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = [s for s in fn.body
                    if not (isinstance(s, ast.Expr)
                            and isinstance(s.value, ast.Constant))]
            if not body:
                continue
            if len(body) == 1 and isinstance(body[0], ast.Raise):
                exc = body[0].exc
                name = ""
                if isinstance(exc, ast.Call):
                    name = ast.unparse(exc.func)
                elif exc is not None:
                    name = ast.unparse(exc)
                if "NotImplementedError" in name:
                    n += 1
    return n, f"NotImplementedError stub function(s) ({n})"


def m_empty_handler_pass(c: Ctx):
    """AP-004: a handler whose entire body is `pass`."""
    n = 0
    for rel in c.py():
        tree = c.parse(rel)
        if tree is None:
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = [s for s in fn.body
                    if not (isinstance(s, ast.Expr)
                            and isinstance(s.value, ast.Constant))]
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                n += 1
    return n, f"function(s) whose whole body is `pass` ({n})"


def m_todo_only(c: Ctx):
    """AP-003 / AP-005: a function whose body is only comments and `pass`."""
    n = 0
    for rel in c.py():
        tree = c.parse(rel)
        if tree is None:
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = [s for s in fn.body
                    if not (isinstance(s, ast.Expr)
                            and isinstance(s.value, ast.Constant))]
            if not body:
                n += 1
            elif all(isinstance(s, ast.Pass) for s in body):
                n += 1
    return n, f"function(s) with no executable body ({n})"


def m_placeholder_marker(c: Ctx):
    """AP-002: `raise NotImplementedError` / `TODO` response scaffolding."""
    pat = re.compile(r"(not\s+yet\s+implemented|not\s+yet\s+wired|"
                     r"placeholder\s+response|TODO:\s*implement)", re.I)
    n = 0
    for rel in c.py():
        tree = c.parse(rel)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and pat.search(node.value):
                n += 1
    return n, f"placeholder string literal(s) in backend core ({n})"


def m_intent_placeholder(c: Ctx):
    """INTENT-002/003: a router returning a 'not yet wired' placeholder."""
    pat = re.compile(r"not\s+yet\s+(wired|implemented)", re.I)
    n = 0
    for rel in c.py(("modules",)):
        if pat.search(c.text(rel)):
            n += 1
    return n, f"router file(s) returning a placeholder response ({n})"


# --------------------------------------------------------------------------- #
# backend: database / pool
# --------------------------------------------------------------------------- #

def m_db_pool_size(c: Ctx):
    """DB-005: the engine factory configures no pool size."""
    src = ""
    for rel in c.py(("infrastructure",)):
        if "database" in rel:
            src = c.text(rel)
            break
    if not src:
        return 1, "no engine factory found (pool_size unconfigured)"
    for key in ("pool_size", "max_overflow", "pool_size_"):
        if re.search(rf"\b{key}\s*=", src):
            return 0, f"engine factory configures {key} — fixed"
    return 1, "engine factory sets no pool_size / max_overflow"


def m_asyncpg_statement_cache(c: Ctx):
    """DB-006: asyncpg `statement_cache_size=0` is not set."""
    for rel in c.py(("infrastructure",)):
        src = c.text(rel)
        if "statement_cache_size" in src:
            return 0, "statement_cache_size is configured — fixed"
    return 1, "asyncpg statement_cache_size is not configured"


def m_read_replica_unused(c: Ctx):
    """DB-007: a read-replica engine that nothing reads through."""
    uses = 0
    for rel in c.py(("domains",)):
        if "get_read_db" in c.text(rel):
            uses += 1
    defined = any("get_read_db" in c.text(rel) for rel in c.py(("infrastructure",)))
    if defined and uses == 0:
        return 1, f"get_read_db is defined but used by {uses} domain file(s)"
    return 0, f"get_read_db used by {uses} domain file(s) — fixed"


def m_unindexed_hot_columns(c: Ctx):
    """DB-unindexed-hot-column: a column filtered or sorted on with no index.

    A column counts as indexed when an `index=True` or a `Index(...)` entry in
    `__table_args__` names it, or when a migration creates an index over it.
    """
    indexed: set[str] = set()
    declared: set[tuple[str, str]] = set()
    for rel in c.py(("domains",)):
        tree = c.parse(rel)
        if tree is None:
            continue
        src = c.text(rel)
        table = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                table = None
                for st in node.body:
                    if isinstance(st, ast.Assign) and len(st.targets) == 1 \
                            and isinstance(st.targets[0], ast.Name) \
                            and st.targets[0].id == "__tablename__":
                        try:
                            table = ast.literal_eval(st.value)
                        except Exception:
                            table = None
                    elif isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name) \
                            and table:
                        col = st.target.id
                        declared.add((table, col))
                        if "index=True" in ast.unparse(st):
                            indexed.add(f"{table}.{col}")
                    elif isinstance(st, ast.Assign) and len(st.targets) == 1 \
                            and isinstance(st.targets[0], ast.Name) and table:
                        col = st.targets[0].id
                        declared.add((table, col))
                        if "index=True" in ast.unparse(st):
                            indexed.add(f"{table}.{col}")
        for m in re.finditer(r"Index\(\s*[\"']([\w]+)[\"']\s*,\s*([^)]+)\)", src):
            name = m.group(1)
            for col in re.findall(r"[\"'`]?(\w+)[\"'`]?", m.group(2)):
                indexed.add(f"{table}.{col}" if table else col)
    hot = re.compile(r"\.filter\(\s*\w*\.?(\w+)\s*==|\.order_by\(\s*\w*\.?(\w+)")
    pairs = set()
    for rel in c.py(("domains",)):
        for m in hot.finditer(c.text(rel)):
            col = m.group(1) or m.group(2)
            if col:
                pairs.add(col)
    unindexed = sorted(
        f"{t}.{c2}" for (t, c2) in declared
        if c2 in pairs and f"{t}.{c2}" not in indexed)
    return (1 if unindexed else 0), \
        f"(table, column) pair(s) filtered/sorted with no declared index ({len(unindexed)})"


def m_taxonomy_depth_used(c: Ctx):
    """CAT-depth-underused: the seeded hierarchy is shallower than the schema allows."""
    depths = set()
    for pat in (r"\"depth\"\s*:\s*(\d+)", r"'depth'\s*:\s*(\d+)"):
        for p in (c.root / "backend" / "domains" / "catalog").rglob("*.json"):
            for m in re.finditer(pat, c.text(p.relative_to(c.root).as_posix())):
                depths.add(int(m.group(1)))
    for rel in c.py(("domains",)):
        if "/catalog/" not in rel:
            continue
        for m in re.finditer(r"[\"']depth[\"']\s*[=:]\s*(\d+)", c.text(rel)):
            depths.add(int(m.group(1)))
    if not depths:
        return 0, "seeded taxonomy reaches every depth the schema allows (no depth data found)"
    return (1 if max(depths) < 3 else 0), \
        f"seeded taxonomy reaches depth {max(depths)} (schema supports a 4-level hierarchy)"


def m_mobile_undeclared_deps(c: Ctx):
    """MOB-001: a bare module required at runtime but absent from package.json."""
    import json as _json
    mobile = c.root / "frontend" / "mobile_app"
    pkg = mobile / "package.json"
    if not pkg.is_dir() and not pkg.exists():
        return 0, "undeclared mobile dependency (no mobile_app)"
    try:
        data = _json.loads(pkg.read_text(encoding="utf-8-sig"))
    except Exception:
        return 1, "mobile package.json unreadable"
    declared = set()
    for k in ("dependencies", "devDependencies", "peerDependencies"):
        declared |= set((data.get(k) or {}).keys())
    if not declared:
        return 1, "mobile package.json declares no dependencies"
    base = c.root / "frontend" / "mobile_app" / "src"
    if not base.is_dir():
        base = mobile
    used: set[str] = set()
    for dirpath, dirnames, files in __import__("os").walk(base):
        dirnames[:] = [x for x in dirnames
                       if x not in _SKIP_DIRS and not x.startswith(".")]
        for fn in files:
            if not fn.endswith((".ts", ".tsx", ".js", ".jsx")):
                continue
            src = (Path(dirpath) / fn).read_text(encoding="utf-8-sig",
                                                 errors="replace")
            for m in re.finditer(r"""(?:from\s+|require\(\s*)['"]([^'"]+)['"]""", src):
                spec = m.group(1)
                if spec.startswith(".") or spec.startswith("@/"):
                    continue
                pkgname = "/".join(spec.split("/")[:2] if spec.startswith("@")
                                   else spec.split("/")[:1])
                used.add(pkgname)
    missing = sorted(u for u in used if u and u not in declared)
    return len(missing), \
        f"package(s) imported but not declared ({', '.join(missing[:5]) or 'none'})"


def m_rls_policy_coverage(c: Ctx):
    """DB-009: no RLS policy is installed for the country-scoped tables."""
    n = 0
    sql = c.root / "backend" / "infrastructure" / "database" / "sql"
    if sql.is_dir():
        for p in sql.rglob("*.sql"):
            n += len(re.findall(r"CREATE\s+POLICY", c.text(
                p.relative_to(c.root).as_posix()), re.I))
    return (1 if n == 0 else 0), f"RLS policy declaration(s) found ({n})"


def m_schema_drift(c: Ctx):
    """DB-schema-drift: a schema named in migrations that no model declares."""
    declared: set[str] = set()
    for rel in c.py(("domains", "modules")):
        for m in re.finditer(r"[\"']schema[\"']\s*:\s*[\"'](\w+)[\"']", c.text(rel)):
            declared.add(m.group(1))
    referenced: dict[str, int] = {}
    versions = c.root / "backend" / "alembic" / "versions"
    if versions.is_dir():
        for p in versions.glob("*.py"):
            for m in re.finditer(r"[\"']?schema[\"']?\s*[=:]\s*[\"'](\w+)[\"']",
                                 c.text(p.relative_to(c.root).as_posix())):
                s = m.group(1)
                if s not in ("public", "information_schema"):
                    referenced[s] = referenced.get(s, 0) + 1
    drift = sorted(set(referenced) - declared)
    return len(drift), \
        f"schema(s) in migrations but in no model: {', '.join(drift) or 'none'}"


def m_governance_columns_complete(c: Ctx):
    """DB-missing-governance-columns: models missing ANY of the four columns.

    Law 23 requires `created_at`, `updated_at`, `country_code` and `is_deleted`
    on every table, but `m_audit_governance_columns` counted only the two audit
    timestamps. The finding says "0 table(s) lack audit timestamps and 2 lack
    soft delete"; the measurement answered the timestamp half with 0 and the
    verifier called the whole finding disproved. Re-derived over
    `backend/domains/**`: 0 tables lack timestamps, 2 lack `is_deleted`
    (`logistics/models/read_models`), 9 lack `country_code` -- so the finding
    was true. This measurement covers every column the claim names.
    """
    need = ("created_at", "updated_at", "country_code", "is_deleted")
    missing = {k: [] for k in need}
    for rel in c.py(("domains",)):
        tree = c.parse(rel)
        if tree is None:
            continue
        for cls in [x for x in ast.walk(tree) if isinstance(x, ast.ClassDef)]:
            names: set[str] = set()
            has_table = False
            for st in cls.body:
                target = st.target if isinstance(st, ast.AnnAssign) else (
                    st.targets[0] if isinstance(st, ast.Assign) and st.targets else None)
                if isinstance(target, ast.Name):
                    names.add(target.id)
                    if target.id == "__tablename__":
                        has_table = True
            if not has_table:
                continue
            for key in need:
                if key not in names:
                    missing[key].append(f"{rel}:{cls.lineno}:{cls.name}")
    total = sum(len(v) for v in missing.values())
    detail = ", ".join(f"{len(v)} lack {k}" for k, v in missing.items() if v) or "none"
    return total, f"table(s) missing a mandated governance column: {detail}"


def m_audit_governance_columns(c: Ctx):
    """DB-missing-governance-columns: models lacking audit timestamps."""
    need = {"created_at", "updated_at"}
    n = 0
    for rel in c.py(("domains",)):
        tree = c.parse(rel)
        if tree is None:
            continue
        for cls in [x for x in ast.walk(tree) if isinstance(x, ast.ClassDef)]:
            names = set()
            has_table = False
            for st in cls.body:
                if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
                    names.add(st.target.id)
                    if st.target.id == "__tablename__":
                        has_table = True
                elif isinstance(st, ast.Assign) and len(st.targets) == 1 \
                        and isinstance(st.targets[0], ast.Name):
                    names.add(st.targets[0].id)
                    if st.targets[0].id == "__tablename__":
                        has_table = True
            if has_table and not need <= names:
                n += 1
    return n, f"model(s) missing audit timestamps ({n})"


# --------------------------------------------------------------------------- #
# backend: providers / operations
# --------------------------------------------------------------------------- #

def _provider_modules(c: Ctx):
    base = c.root / "backend" / "providers"
    if not base.is_dir():
        return []
    out = []
    for dirpath, dirnames, files in __import__("os").walk(base):
        dirnames[:] = [x for x in dirnames
                       if x not in _SKIP_DIRS and not x.startswith(".")]
        for fn in files:
            if fn.endswith(".py") and fn not in ("__init__.py", "_base.py"):
                out.append((Path(dirpath) / fn).relative_to(c.root).as_posix())
    return sorted(out)


def m_provider_health_check(c: Ctx):
    """PROV-005: providers exposing no `health_check()`."""
    mods = _provider_modules(c)
    if not mods:
        return 0, "provider module(s) missing health_check() (none found)"
    missing = [m for m in mods if "def health_check" not in c.text(m)]
    return len(missing), \
        f"provider module(s) without health_check() ({len(missing)}/{len(mods)})"


def m_provider_timeout(c: Ctx):
    """PROV-007: provider modules declaring no HTTP/SDK timeout."""
    mods = _provider_modules(c)
    missing = [m for m in mods
               if not re.search(r"timeout\s*=", c.text(m))]
    return len(missing), \
        f"provider module(s) with no timeout ({len(missing)}/{len(mods)})"


def m_provider_circuit_breaker(c: Ctx):
    """OBS-001: provider modules with no circuit breaker."""
    mods = _provider_modules(c)
    missing = [m for m in mods
               if not re.search(r"circuit_breaker|CircuitBreaker|pybreaker", c.text(m))]
    return len(missing), \
        f"provider module(s) with no circuit breaker ({len(missing)}/{len(mods)})"


def m_provider_retry_policy(c: Ctx):
    """OBS-002: provider modules with no bounded retry."""
    mods = _provider_modules(c)
    missing = [m for m in mods
               if not re.search(r"retry|backoff|max_attempts", c.text(m), re.I)]
    return len(missing), \
        f"provider module(s) with no retry policy ({len(missing)}/{len(mods)})"


def m_provider_raw_getenv(c: Ctx):
    """PROV-006: provider modules reading secrets via raw `os.getenv`."""
    pat = re.compile(r"os\.(?:getenv|environ\.get)\(")
    hits = [m for m in _provider_modules(c) if pat.search(c.text(m))]
    return len(hits), f"provider module(s) using raw os.getenv ({len(hits)})"


def m_provider_extra_packages(c: Ctx):
    """PROV-004: provider packages outside the canonical tree."""
    from .constants import CANONICAL_DOMAINS  # noqa: F401  (scope anchor)
    base = c.root / "backend" / "providers"
    if not base.is_dir():
        return 0, "provider package(s) outside the canonical tree (none)"
    allowed = {"payments", "email", "sms", "storage", "ai", "maps"}
    extras = sorted({p.name for p in base.iterdir()
                     if p.is_dir() and p.name != "__pycache__"
                     and p.name not in allowed})
    return len(extras), \
        f"provider package(s) outside the canonical tree: {', '.join(extras) or 'none'}"


def m_provider_orphan(c: Ctx):
    """PROV-008: provider modules no domain file ever references."""
    mods = [Path(m).stem for m in _provider_modules(c)]
    if not mods:
        return 0, "orphan provider module(s) (none found)"
    blob = "\n".join(c.text(rel) for rel in c.py(("domains", "modules")))
    orphans = sorted({m for m in mods
                      if not re.search(rf"\b{re.escape(m)}\b", blob)})
    return len(orphans), \
        f"provider module(s) never referenced by a domain ({len(orphans)})"


def m_payment_webhook_signature(c: Ctx):
    """PROV-001..003: a payment module referencing webhooks with no verification."""
    base = c.root / "backend" / "providers" / "payments"
    if not base.is_dir():
        return 0, "payment module(s) missing webhook verification (none found)"
    hits = []
    for p in sorted(base.rglob("*.py")):
        rel = p.relative_to(c.root).as_posix()
        src = c.text(rel)
        if not re.search(r"webhook", src, re.I):
            continue
        if not re.search(r"verify|signature|hmac|sign_webhook|compare_digest",
                         src, re.I):
            hits.append(rel)
    return len(hits), \
        f"payment module(s) with no webhook signature verification ({len(hits)})"


def m_orphan_job_module(c: Ctx):
    """OPS-015: a Celery task module celery_app never imports."""
    app = c.text("backend/jobs/celery_app.py")
    if not app:
        return 0, "orphan job module(s) (no celery_app.py)"
    jobs = c.root / "backend" / "jobs"
    orphans = []
    for p in sorted(jobs.glob("*.py")):
        if p.name in ("__init__.py", "celery_app.py", "periodic_tasks.py"):
            continue
        stem = p.stem
        if not re.search(rf"\b{re.escape(stem)}\b", app):
            orphans.append(stem)
    return len(orphans), \
        f"task module(s) never referenced by celery_app: {', '.join(orphans) or 'none'}"


def m_event_spine(c: Ctx):
    """WIRE-004: events defined in a domain that nothing publishes."""
    domains = c.root / "backend" / "domains"
    if not domains.is_dir():
        return 0, "unpublished event(s) (no domains dir)"
    published: set[str] = set()
    orphans: list[str] = []
    for ev in sorted(domains.glob("*/events.py")):
        rel_ev = ev.relative_to(c.root).as_posix()
        names = set(re.findall(r'^EVENT_[A-Z_]+\s*=\s*["\']([^"\']+)["\']',
                               c.text(rel_ev), re.MULTILINE))
        for name in names:
            hit = False
            for p in sorted(ev.parent.rglob("*.py")):
                rel = p.relative_to(c.root).as_posix()
                if rel == rel_ev:
                    continue
                if name in c.text(rel):
                    hit = True
                    break
            (published.add(name) if hit else orphans.append(name))
    return len(orphans), \
        f"event(s) defined but never published ({len(orphans)})"


def m_stub_subscribers(c: Ctx):
    """WF-stub-subscribers: a handler that logs and returns without the write."""
    n = 0
    for sub in sorted((c.root / "backend" / "domains").glob("*/subscribers.py")):
        rel = sub.relative_to(c.root).as_posix()
        tree = c.parse(rel)
        if tree is None:
            continue
        src = c.text(rel)
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef) or not fn.name.startswith("_on_"):
                continue
            body = [s for s in fn.body
                    if not (isinstance(s, ast.Expr)
                            and isinstance(s.value, ast.Constant))]
            if not body:
                continue
            writes = any(
                isinstance(x, (ast.Assign, ast.AugAssign, ast.Delete,
                               ast.Call, ast.Return))
                and not (isinstance(x, ast.Call)
                         and isinstance(x.func, ast.Attribute)
                         and x.func.attr in ("info", "debug", "warning", "error",
                                             "critical", "exception", "log"))
                for s in body for x in ast.walk(s))
            if not writes:
                n += 1
    return n, f"event handler(s) that log and return without the write ({n})"


def m_handover_unguarded(c: Ctx):
    """WF-handover-unguarded: a transfer function missing a safety guarantee."""
    guarantees = ("permission", "audit", "emit", "publish", "require_",
                  "assert", "forbidden")
    n = 0
    for rel in c.py():
        tree = c.parse(rel)
        if tree is None:
            continue
        src = c.text(rel)
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not re.search(r"handover|takeover|transfer", fn.name, re.I):
                continue
            seg = (ast.get_source_segment(src, fn) or "").lower()
            if not any(g in seg for g in guarantees):
                n += 1
    return n, f"handover function(s) with no safety guarantee ({n})"


def m_ssrf_unguarded(c: Ctx):
    """SEC-006: an outbound call whose URL comes from a caller."""
    clients = ("httpx", "requests", "aiohttp", "urlopen", "urlretrieve")
    guarded = ("require_safe_url", "allowlist", "allowed_host", "is_safe_url",
               "validate_url", "same_origin")
    n = 0
    for rel in c.py():
        tree = c.parse(rel)
        if tree is None:
            continue
        src = c.text(rel)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = ast.unparse(node.func)
            if not any(f"{cl}." in fn for cl in clients):
                continue
            if any(g in src for g in guarded):
                continue
            if node.args and isinstance(node.args[0], ast.Name):
                n += 1
    return n, f"caller-influenced outbound call(s) with no URL guard ({n})"


def m_router_db_access(c: Ctx):
    """ARCH-159/163: a router issuing a real session call."""
    pat = re.compile(r"(session\.execute|db\.commit\(|db\.query\(|\.execute\(\s*text)")
    n = 0
    for rel in c.py(("modules",)):
        if "/routers/" not in rel:
            continue
        if pat.search(c.text(rel)):
            n += 1
    return n, f"router file(s) issuing a DB call directly ({n})"


def m_public_endpoint_unregistered(c: Ctx):
    """WIRE-012: an unauthenticated endpoint absent from `public_routers`.

    File-level by design: "this module has no auth at all".
    """
    n = 0
    for mod in sorted((c.root / "backend" / "modules").glob("*/routers/*.py")):
        rel = mod.relative_to(c.root).as_posix()
        if mod.name == "__init__.py":
            continue
        src = c.text(rel)
        if "# public:" in src:
            continue
        if re.search(r"@router\.(get|post|put|patch|delete)", src) \
                and not re.search(r"Depends\(|require_|verify_", src):
            n += 1
    return n, f"router file(s) with unauthenticated endpoints and no exemption ({n})"


def m_public_endpoint_undeclared(c: Ctx):
    """WIRE-012 as the finding states it: an *endpoint* that is unauthenticated
    and not recorded as public.

    `m_public_endpoint_unregistered` answers a different, much narrower
    question -- "does this whole file have no auth anywhere?" -- which is 0 in
    any module where a single route uses `Depends(...)`. The verifier used it to
    disprove WIRE-012 (9 intentionally-public endpoints, sample
    `customer/routers/accounts.py:219 logout`), and `logout` is unauthenticated
    with no `# public:` marker and no `public_routers` entry, so the finding was
    true and got deleted. This measures the claim at the granularity the finding
    cites: per route function, using the AST for auth and the source span for the
    exemption marker.
    """
    declared_public: set[str] = set()
    for init in sorted((c.root / "backend" / "modules").glob("*/routers/__init__.py")):
        src = c.text(init.relative_to(c.root).as_posix())
        m = re.search(r"public_routers\s*=\s*\[(.*?)\]", src, re.S)
        if m:
            declared_public |= set(re.findall(r"[\"']([\w.]+)[\"']", m.group(1)))

    offenders: list[str] = []
    for mod in sorted((c.root / "backend" / "modules").glob("*/routers/*.py")):
        if mod.name == "__init__.py":
            continue
        rel = mod.relative_to(c.root).as_posix()
        src = c.text(rel)
        tree = c.parse(rel)
        if tree is None:
            continue
        lines = src.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            is_route = any(
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Attribute)
                and isinstance(d.func.value, ast.Name)
                and d.func.value.id == "router"
                and d.func.attr in ("get", "post", "put", "patch", "delete")
                for d in node.decorator_list)
            if not is_route:
                continue
            if "Depends" in ast.unparse(node.args):
                continue  # authenticated or gated
            body_lines = lines[node.lineno - 1: node.body[0].lineno - 1]
            span = "\n".join(lines[max(0, node.lineno - 3): node.lineno]) + "\n" + "\n".join(body_lines)
            if "# public:" in span or node.name in declared_public:
                continue
            offenders.append(f"{rel}:{node.lineno} {node.name}")
    return len(offenders), \
        f"unauthenticated endpoint(s) with no recorded exemption ({len(offenders)})"


def m_ci_missing_step(c: Ctx, step: str = ""):
    """D2P-001/002: the pipeline lacks a named scanning step."""
    wf = c.root / ".github" / "workflows"
    if not wf.is_dir():
        return 1, f"no CI workflow declares {step or 'the step'}"
    blob = "\n".join(c.text(p.relative_to(c.root).as_posix())
                     for p in sorted(wf.glob("*.y*ml")))
    if step and re.search(step, blob, re.I):
        return 0, f"pipeline declares {step} — fixed"
    return 1, f"pipeline lacks {step or 'the required step'}"


def m_ci_secret_scanning(c: Ctx):
    return m_ci_missing_step(c, "secret.?scan|gitleaks|trufflehog")


def m_ci_dependency_scanning(c: Ctx):
    return m_ci_missing_step(c, "dependency.?scan|dependabot|renovate|snyk|"
                                r"pip-audit|npm audit|osv")


def m_todo_hygiene(c: Ctx):
    """LOGIC-296 / Law 62: TODO/FIXME with no ticket and no expiry."""
    pat = re.compile(
        r"#\s*(?:TODO|FIXME)(?!.*(?:#\d+|[A-Z]+-\d+|\d{4}-\d{2}-\d{2}))",
        re.IGNORECASE)
    n = 0
    for rel in c.py():
        n += len(pat.findall(c.text(rel)))
    return n, f"TODO/FIXME without a ticket or expiry ({n})"


def m_ungated_pages(c: Ctx):
    """WEB-001 / Law 178: a route with no loading.tsx or error.tsx sibling."""
    app = c.root / "frontend" / "web_app" / "src" / "app"
    if not app.is_dir():
        return 0, "route(s) missing loading/error siblings (no app dir)"
    pages = [p for p in app.rglob("page.tsx")]
    missing = []
    for p in pages:
        d = p.parent
        if not (d / "loading.tsx").exists() and not (d / "error.tsx").exists():
            missing.append(p)
    return (1 if missing else 0), \
        f"route group(s) with neither loading nor error boundary ({len(missing)}/{len(pages)})"


def m_duplicate_route_trees(c: Ctx):
    """WEB-002 / Law 177: two route directories differing only by a plural."""
    app = c.root / "frontend" / "web_app" / "src" / "app"
    if not app.is_dir():
        return 0, "duplicate route tree(s) (no app dir)"
    names: dict[str, str] = {}
    for p in app.iterdir():
        if not p.is_dir():
            continue
        key = p.name.rstrip("s")
        names.setdefault(key, []).append(p.name)
    dups = [v for v in names.values() if len(v) > 1]
    return len(dups), f"duplicate route tree(s): {', '.join('/'.join(v) for v in dups) or 'none'}"


def m_kernel_third_party_import(c: Ctx):
    """DECLLAW-014: kernel importing an external SDK instead of providers."""
    third = re.compile(r"^\s*(?:from|import)\s+(sqlalchemy|alembic|fastapi|"
                       r"starlette|pydantic|httpx|aiohttp|redis|celery|boto3|"
                       r"stripe|paypal|stripe\b|numpy|pandas|jwt|jose)\b")
    hits = []
    for rel in c.py(("kernel",)):
        for i, line in enumerate(c.text(rel).splitlines(), 1):
            if third.search(line):
                hits.append(f"{rel}:{i}")
    return len(hits), f"kernel module(s) importing a third-party SDK ({len(hits)})"


def m_middleware_order(c: Ctx):
    """WIRE-001: middleware registration deviates from the canonical pipeline."""
    src = c.text("backend/middleware/orchestrator.py")
    if not src:
        return 1, "middleware orchestrator not found"
    m = re.search(r"\[([^\]]*?)\]", src, re.S)
    if not m:
        return 1, "middleware pipeline declaration not found"
    stages = re.findall(r"[\"'](\w+)[\"']", m.group(1))
    canonical = ["foundation", "auth", "rate", "security", "geo", "compliance",
                 "webhook", "observe"]
    ok = stages == canonical
    return (0 if ok else 1), \
        f"middleware order {'matches' if ok else 'deviates from'} the canonical pipeline"


def m_migration_heads(c: Ctx):
    """MIG-001 / Law 49: divergent Alembic heads."""
    versions = c.root / "backend" / "alembic" / "versions"
    if not versions.is_dir():
        return 0, "divergent migration head(s) (no versions dir)"
    revs: dict[str, str | None] = {}
    for p in versions.glob("*.py"):
        tree = c.parse(p.relative_to(c.root).as_posix())
        if tree is None:
            continue
        up = down = None
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for t in node.targets:
                if not isinstance(t, ast.Name):
                    continue
                try:
                    if t.id == "revision":
                        up = ast.literal_eval(node.value)
                    elif t.id == "down_revision":
                        down = ast.literal_eval(node.value)
                except Exception:
                    pass
        if up:
            revs[up] = down if isinstance(down, str) else None
    if not revs:
        return 0, "divergent migration head(s) (none parsed)"
    parents = {d for d in revs.values() if d}
    heads = [r for r in revs if r not in parents]
    extra = max(0, len(heads) - 1)
    return extra, f"migration head(s) beyond the first ({len(heads)} heads)"


def m_middleware_order(c: Ctx):
    """WIRE-001: registration order deviates from the canonical pipeline."""
    src = c.text("backend/middleware/orchestrator.py")
    if not src:
        return 1, "middleware orchestrator not found"
    m = re.search(r"\[([^\]]*?)\]", src, re.S)
    if not m:
        return 1, "middleware pipeline declaration not found"
    stages = re.findall(r"[\"'](\w+)[\"']", m.group(1))
    canonical = ["foundation", "auth", "rate", "security", "geo", "compliance",
                 "webhook", "observe"]
    return (1 if stages != canonical else 0), \
        f"middleware order {'matches' if stages == canonical else 'deviates from'} the canonical pipeline"


def m_placeholder_capability(c: Ctx, name: str = ""):
    """FIN/QA: a named capability with no implementation anywhere."""
    if not name:
        return 0, "capability implemented (no name given)"
    for rel in c.py():
        if re.search(rf"\b{re.escape(name)}\b", c.text(rel)):
            return 0, f"`{name}` is implemented — fixed"
    return 1, f"no implementation of `{name}` anywhere in backend"


def m_missing_setup_doc(c: Ctx):
    """D2P-008: SETUP.md is absent."""
    return (0 if (c.root / "SETUP.md").exists() else 1), \
        "SETUP.md is present — fixed" if (c.root / "SETUP.md").exists() \
        else "SETUP.md is missing"


def m_noncanonical_lockfile(c: Ctx):
    """TECH-013: a lockfile beside the canonical one."""
    hits = [p.name for p in (c.root / "frontend" / "web_app").glob("*lock*")
            if p.name != "pnpm-lock.yaml"]
    return len(hits), f"non-canonical lockfile(s): {', '.join(hits) or 'none'}"


def m_base_image_drift(c: Ctx):
    """TECH-001: the compose database image differs from the documented one."""
    src = c.text("docker-compose.yml")
    if not src:
        return 1, "docker-compose.yml not found"
    m = re.search(r"image:\s*[\"']?postgres:([\w.-]+)", src)
    if not m:
        return 1, "no postgres image pinned in docker-compose.yml"
    return (1 if m.group(1).startswith("18") else 0), \
        f"compose pins postgres:{m.group(1)}"


# --------------------------------------------------------------------------- #
# frontend: design system and interaction
# --------------------------------------------------------------------------- #

def m_raw_palette_classes(c: Ctx):
    """DS-palette-drift: raw Tailwind palette classes outside the token layer."""
    pat = re.compile(
        r"\b(?:bg|text|border|fill|stroke|ring|from|via|to|outline|shadow|"
        r"decoration|divide|placeholder|caret|accent)-"
        r"(?:red|blue|green|yellow|purple|orange|pink|indigo|teal|cyan|slate|"
        r"gray|grey|zinc|neutral|stone|amber|lime|emerald|sky|violet|fuchsia|"
        r"rose|white|black)\b")
    owners = ("tokens.css", "theme.ts", "tailwind.config", "globals.css")
    n = files = 0
    for rel in c.ts():
        if any(o in rel for o in owners):
            continue
        hits = pat.findall(c.text(rel))
        if hits:
            files += 1
            n += len(hits)
    return (1 if n else 0), \
        f"raw palette class(es) bypassing the token scale ({n} in {files} file(s))"


def m_hex_drift(c: Ctx):
    """DS-hex-drift: literal hex colours outside the token layer."""
    pat = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")
    owners = ("tokens.css", "theme.ts", "tailwind.config", "globals.css")
    assets = (".svg", "logo", "chart")
    n = files = 0
    for rel in c.ts():
        low = rel.lower()
        if any(o in low for o in owners) or any(a in low for a in assets):
            continue
        hits = pat.findall(c.text(rel))
        if hits:
            files += 1
            n += len(hits)
    return (1 if n else 0), \
        f"hardcoded hex colour(s) outside the token layer ({n} in {files} file(s))"


def m_inline_style(c: Ctx):
    """DS-inline-style: `style={{...}}` that cannot be themed."""
    n = files = 0
    for rel in c.ts():
        src = c.text(rel)
        hits = re.findall(r"style\s*=\s*\{\{", src)
        if hits:
            files += 1
            n += len(hits)
    return (1 if n else 0), f"inline style prop(s) ({n} in {files} file(s))"


def m_no_variant_system(c: Ctx):
    """DS-no-variant-system: primitives with raw variant maps, not `cva`."""
    ui = c.root / "frontend" / "web_app" / "src" / "components" / "ui"
    if not ui.is_dir():
        return 0, "primitive(s) without a variant system (no ui dir)"
    prims = sorted(p for p in ui.rglob("*.tsx") if p.is_file())
    if not prims:
        return 0, "primitive(s) without a variant system (none found)"
    with_cva = [p for p in prims if "cva(" in c.text(
        p.relative_to(c.root).as_posix())]
    missing = [p for p in prims if p not in with_cva]
    return len(missing), \
        f"primitive(s) with no class-variance-authority ({len(missing)}/{len(prims)})"


def m_primitive_no_ref(c: Ctx):
    """DS-primitive-ref: a primitive that neither forwards a ref nor names itself."""
    ui = c.root / "frontend" / "web_app" / "src" / "components" / "ui"
    if not ui.is_dir():
        return 0, "primitive(s) not forwarding a ref (no ui dir)"
    prims = sorted(p for p in ui.rglob("*.tsx") if p.is_file())
    missing = []
    for p in prims:
        src = c.text(p.relative_to(c.root).as_posix())
        if "forwardRef" not in src and "displayName" not in src:
            missing.append(p.name)
    return len(missing), \
        f"primitive(s) with no ref forwarding or displayName ({len(missing)}/{len(prims)})"


def m_duplicate_primitive_markup(c: Ctx):
    """DS-duplicate-markup: a hand-rolled class string duplicating a primitive."""
    pat = re.compile(r"className\s*=\s*[\"{][^\"}]*(rounded-lg border)[^\"}]*[\"}]")
    n = files = 0
    for rel in c.ts():
        hits = pat.findall(c.text(rel))
        if hits:
            files += 1
            n += len(hits)
    return (1 if n else 0), \
        f"hand-rolled card/input class string(s) ({n} in {files} file(s))"


def m_button_missing_type(c: Ctx):
    """IX-button-type: a <button> with no explicit `type`."""
    total = missing = 0
    pat = re.compile(r"<button\b([^>]*)>", re.S)
    for rel in c.ts():
        for attrs in pat.findall(c.text(rel)):
            total += 1
            if not re.search(r"\btype\s*=", attrs):
                missing += 1
    return (1 if missing else 0), \
        f"button element(s) without an explicit type ({missing}/{total})"


def m_input_without_label(c: Ctx):
    """IX-input-label: an input with no label, aria-label or id."""
    total = missing = 0
    pat = re.compile(r"<input\b([^>]*)>", re.S)
    for rel in c.ts():
        for attrs in pat.findall(c.text(rel)):
            if re.search(r"\btype\s*=\s*[\"{](?:hidden|submit|button|checkbox|radio)", attrs):
                continue
            total += 1
            if not re.search(r"\b(aria-label|aria-labelledby|\bid)\s*=", attrs):
                missing += 1
    return (1 if missing else 0), \
        f"input(s) with no accessible name ({missing}/{total})"


def m_swallowed_error(c: Ctx):
    """IX-error-swallow: a catch handler that is empty or logs to console."""
    pat = re.compile(r"catch\s*(?:\([^)]*\))?\s*\{\s*(?:console\.\w+\([^)]*\)\s*;?\s*)?\}",
                     re.S)
    n = files = 0
    for rel in c.ts():
        hits = pat.findall(c.text(rel))
        if hits:
            files += 1
            n += len(hits)
    return (1 if n else 0), \
        f"empty or console-only catch handler(s) ({n} in {files} file(s))"


def m_modal_no_escape(c: Ctx):
    """IX-modal-escape: a dialog that cannot be dismissed with Escape."""
    mods = _modal_files(c)
    missing = [m for m in mods
               if not re.search(r"onEscapeKeyDown|onKeyDown|Escape|onOpenChange",
                                c.text(m))]
    return (1 if missing else 0), \
        f"modal(s) with no Escape dismissal ({len(missing)}/{len(mods)})"


def m_modal_no_focus(c: Ctx):
    """IX-modal-focus: a dialog with no focus management."""
    mods = _modal_files(c)
    missing = [m for m in mods
               if not re.search(r"onOpenAutoFocus|autoFocus|focus\(|initialFocus|"
                                r"FocusTrap|returnFocus", c.text(m))]
    return (1 if missing else 0), \
        f"modal(s) with no focus management ({len(missing)}/{len(mods)})"


def m_destructive_without_confirm(c: Ctx):
    """IX-destructive-confirm: a destructive control with no confirmation."""
    destructive = re.compile(r"\b(delete|remove|refund|revoke|cancel|terminate|"
                             r"deactivate|ban|purge)\w*\b", re.I)
    confirm = re.compile(r"confirm|AlertDialog|ConfirmDialog|are you sure|"
                         r"\?\s*window\.confirm", re.I)
    n = 0
    for rel in c.ts():
        src = c.text(rel)
        if destructive.search(src) and not confirm.search(src):
            n += 1
    return (1 if n else 0), f"modal file(s) with a destructive control and no confirm ({n})"


def m_icon_button_unnamed(c: Ctx):
    """IX-icon-button-name: an icon-only control with no accessible name."""
    n = 0
    for rel in c.ts():
        src = c.text(rel)
        for m in re.finditer(r"<button\b([^>]*)>([\s\S]{0,400}?)</button>", src):
            attrs, inner = m.group(1), m.group(2)
            if re.search(r"aria-label|aria-labelledby|title\s*=", attrs):
                continue
            # Visible or slotted text means the control is not icon-only.
            if re.sub(r"<[^>]*>", "", inner).strip():
                continue
            if re.search(r"children|label|title|text", inner):
                continue
            n += 1
    return (1 if n else 0), f"icon-only button(s) with no accessible name ({n})"


def m_mutation_error_swallowed(c: Ctx):
    """IX-mutation-error-swallowed: a mutation next to a swallowed catch."""
    mutating = re.compile(r"\b(delete|remove|update|create|post|put|patch|submit|"
                          r"save|refund|revoke|cancel)\w*\s*\(", re.I)
    swallow = re.compile(r"catch\s*(?:\([^)]*\))?\s*\{\s*(?:console\.\w+\([^)]*\)\s*;?\s*)?\}",
                         re.S)
    n = 0
    for rel in c.ts():
        src = c.text(rel)
        if mutating.search(src) and swallow.search(src):
            n += 1
    return (1 if n else 0), f"file(s) with a mutation beside a swallowed catch ({n})"


def m_orphan_feature_atom(c: Ctx):
    """FEAT-003 / FEAT-DEAD: a declared feature atom no gate ever references."""
    catalog, gates = _catalog_and_gates(c)
    if not catalog:
        return 0, "orphan feature atom(s) (no features.py found)"
    orphans = sorted(catalog - set(gates))
    return (1 if orphans else 0), \
        f"feature atom(s) declared but never gated ({len(orphans)}/{len(catalog)})"


def _catalog_and_gates(c: Ctx):
    """The declared feature atoms and the gate literals, one extractor.

    `_feature_catalog` reads `domains/*/features.py`; `feature_gate_literals`
    parses `modules/**` with the AST. Both the ghost-atom measurement and
    `s12_features.feat_catalog` call this, so the detector and its independent
    re-check cannot disagree about what a gate literal is (they did: a regex
    let prose produce a phantom atom, and the verifier deleted the finding).
    """
    from .util import feature_gate_literals

    catalog: set[str] = set()
    for fp in sorted((c.root / "backend" / "domains").glob("*/features.py")):
        catalog |= set(re.findall(
            r'"([a-z][a-z0-9_.]*\.[a-z0-9_.]+)"\s*:',
            c.text(fp.relative_to(c.root).as_posix())))
    gates = feature_gate_literals(
        [c.root / rel for rel in c.py(("modules",))])
    return catalog, gates


def m_dead_feature_gate(c: Ctx):
    """FEAT-DEAD: a gate literal no catalog defines ("ghost" atom)."""
    catalog, gates = _catalog_and_gates(c)
    unknown = sorted(set(gates) - catalog)
    return len(unknown), \
        f"gate literal(s) with no catalog entry ({', '.join(unknown[:5]) or 'none'})"


def m_orphaned_spec(c: Ctx):
    """FEAT-SPEC-ORPHAN: a spec navigating to a route the app no longer has."""
    tests = c.root / "_browser_test" / "tests"
    if not tests.is_dir():
        return 0, "orphaned spec file(s) (no browser tests)"
    app = c.root / "frontend" / "web_app" / "src" / "app"
    if not app.is_dir():
        return 0, "orphaned spec file(s) (no app router)"
    routes = set()
    for p in app.rglob("page.tsx"):
        parts = p.relative_to(app).parts[:-1]
        routes.add("/" + "/".join(parts) if parts else "/")
    n = 0
    for spec in sorted(tests.rglob("*.ts")):
        for m in re.finditer(r"[\"'`](/[\w\-/]*)[\"'`]", c.text(
                spec.relative_to(c.root).as_posix())):
            path = m.group(1).rstrip("/")
            if path and path not in routes and not path.startswith("/api"):
                n += 1
                break
    return n, f"spec file(s) pointing at a non-existent route ({n})"


def _modal_files(c: Ctx) -> list[str]:
    out = []
    for rel in c.ts():
        src = c.text(rel)
        if re.search(r"\b(Dialog|Modal|Drawer|Sheet)\b", src) \
                and re.search(r"open\s*=|isOpen|visible", src):
            out.append(rel)
    return out


def m_cache_coverage(c: Ctx):
    """PERF-002: list endpoints with no cache reference behind them."""
    list_eps = 0
    for rel in c.py():
        list_eps += len(re.findall(
            r"@router\.get\([^)]*\)", c.text(rel)))
    cached = 0
    for rel in c.py():
        cached += len(re.findall(r"\bcache\b|redis|Cache-Control", c.text(rel),
                                 re.I))
    return (1 if cached < list_eps else 0), \
        f"cache references ({cached}) vs list endpoints ({list_eps})"


def m_chain_gap(c: Ctx, chain_id: str = ""):
    """BLOCK-*: a critical chain whose events are never published.

    The chain SPEC (which steps and events a business flow requires) is data,
    not a measurement, so it is imported. The arithmetic -- how many of those
    events any service actually publishes -- is re-derived here.
    """
    try:
        from ..zz_scanners.s15_crosscut import CHAINS
    except Exception:
        try:
            from zz_scanners.s15_crosscut import CHAINS
        except Exception as exc:
            raise RuntimeError(f"chain spec unavailable: {exc}") from exc
    row = next((r for r in CHAINS if r[0] == chain_id), None)
    if row is None:
        return 0, f"{chain_id} is not a known chain"
    _cid, _name, _actors, domains, _entry, steps, events = row
    published: set[str] = set()
    for d in domains:
        base = c.root / "backend" / "domains" / d
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            src = c.text(p.relative_to(c.root).as_posix())
            for ev in events:
                if ev in src:
                    published.add(ev)
    steps_found = 0
    for d in domains:
        base = c.root / "backend" / "domains" / d
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            src = c.text(p.relative_to(c.root).as_posix())
            steps_found += sum(1 for s in steps if s in src)
    missing_ev = [e for e in events if e not in published]
    missing_steps = [s for s in steps if s not in published and not any(
        s in c.text(p.relative_to(c.root).as_posix())
        for d in domains if (c.root / "backend" / "domains" / d).is_dir()
        for p in (c.root / "backend" / "domains" / d).rglob("*.py"))]
    gap = len(missing_ev) + len(missing_steps)
    return gap, (f"{chain_id}: event(s) never published {missing_ev or 'none'}, "
                 f"step(s) absent {missing_steps or 'none'}")


def m_websocket_accept_unverified(c: Ctx):
    """WIRE-013 / SEC-005: a handler that accepts a socket before verifying a token."""
    verify = re.compile(r"decode|verify|jwt|token|get_user|authenticate|credentials",
                        re.I)
    n = 0
    for rel in c.py(("modules",)):
        tree = c.parse(rel)
        if tree is None:
            continue
        src = c.text(rel)
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            seg = ast.get_source_segment(src, fn) or ""
            if "accept()" not in seg:
                continue
            lines = [l for l in seg.splitlines() if l.strip()]
            for i, line in enumerate(lines):
                if "accept()" not in line:
                    continue
                before = "\n".join(lines[:i])
                if not verify.search(before):
                    n += 1
                break
    return n, f"WebSocket handler(s) calling accept() before token verification ({n})"


def m_browser_evidence_fresh(c: Ctx):
    """BROWSER-001: recorded browser results are older than the code they describe."""
    results = c.root / "_browser_test" / "reports" / "run" / "results.json"
    if not results.exists():
        return 1, "no browser evidence file exists"
    import time
    recorded = results.stat().st_mtime
    newest = 0.0
    for rel in list(c.ts()) + list(c.py()):
        try:
            newest = max(newest, (c.root / rel).stat().st_mtime)
        except OSError:
            continue
    if recorded >= newest:
        return 0, "browser evidence is newer than every source file — fresh"
    age_days = (newest - recorded) / 86400.0
    return 1, (f"browser evidence is {age_days:.1f} day(s) older than the newest "
               f"source file — stale")


# --------------------------------------------------------------------------- #
# doc/code contradictions and chain wiring (dimensions 21 / 27)
#
# These findings were emitted with an EMPTY probe, so nothing independent could
# settle them and the verifier could only ever answer UNVERIFIABLE. The claims
# are cheap to re-derive from the tree; each measurement below does exactly
# that, independently of the detector that raised the claim.
# --------------------------------------------------------------------------- #

def m_orphan_frontend_module_route(c: Ctx, arg: str = ""):
    """`arg` = module name. A frontend rewrite routes to a module that is not there.

    Counts 1 per offending rewrite while `frontend/web_app/next.config.ts`
    rewrites `/<mod>/*` while `backend/modules/<mod>` does not exist. Both
    halves matter: a rewrite with no backend route 404s, and a backend module
    with no rewrite is merely unused. An empty `arg` measures every rewrite whose
    module is missing.
    """
    nxt = c.text("frontend/web_app/next.config.ts")
    if not nxt:
        return 0, "frontend/web_app/next.config.ts unreadable"
    mods = {m.strip().strip("'\"") for m in re.findall(
        r"source:\s*['\"]/([A-Za-z0-9_-]+)/", nxt)}
    if arg:
        mods = {m for m in mods if m == arg}
    orphans = sorted(m for m in mods
                     if not (c.root / "backend" / "modules" / m).is_dir())
    return len(orphans), (f"frontend rewrite(s) to a module directory that does not "
                          f"exist: {', '.join(orphans)}" if orphans
                          else "no frontend rewrite targets a missing module")


def m_router_shadowed_by_package(c: Ctx, arg: str = ""):
    """`arg` = a `routers/` directory. A router file and a package of the same name.

    Python imports the package, never the sibling module, so `hr.py` beside an
    `hr/` package is unreachable code that still looks registered. Counted per
    colliding name.
    """
    base = (c.root / arg.replace("\\", "/").rstrip("/")) if arg \
        else (c.root / "backend" / "modules")
    if not base.is_dir():
        return 0, f"router directory {arg or 'backend/modules'} does not exist"
    hits = []
    for f in sorted(base.rglob("*.py")):
        if f.stem == "__init__" or f.parent.name != "routers":
            continue
        if (f.parent / f.stem).is_dir():
            hits.append(f"{f.parent.name}/{f.stem}")
    return len(hits), (f"router file(s) shadowed by a same-named package: "
                       f"{', '.join(hits)}" if hits
                       else "no router file is shadowed by a package")


def m_chain_event_unwired(c: Ctx, arg: str = ""):
    """`arg` = a chain event name. No domain declares it in its event spine.

    A chain whose steps all exist still has no integration seam if the event it
    publishes is declared nowhere: nothing can subscribe, so the write the step
    implies never happens. Counts 1 while the event is undeclared.
    """
    events = [arg] if arg else []
    if not events:
        return 0, "no chain event named"
    missing = []
    for ev in events:
        found = False
        for p in sorted((c.root / "backend" / "domains").glob("*/events.py")):
            if ev in c.text(p.relative_to(c.root).as_posix()):
                found = True
                break
        if not found:
            missing.append(ev)
    return len(missing), (f"chain event(s) declared in no backend/domains/*/events.py: "
                          f"{', '.join(missing)}" if missing
                          else "every named chain event is declared in the event spine")


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #

MEASUREMENTS = {
    "root_temp_scripts": m_root_temp_scripts,
    "select_star": m_select_star,
    "offset_pagination": m_offset_pagination,
    "count_queries": m_count_queries,
    "leading_wildcard_ilike": m_leading_wildcard_ilike,
    "relationship_without_lazy": m_relationship_without_lazy,
    "unguarded_global_mutation": m_unguarded_global_mutation,
    "uncancelled_import": m_uncancelled_import,
    "deep_nesting": m_deep_nesting,
    "print_in_production": m_print_in_production,
    "raw_getenv": m_raw_getenv,
    "pii_logs": m_pii_logs,
    "notimplementederror": m_notimplementederror,
    "empty_handler_pass": m_empty_handler_pass,
    "todo_only": m_todo_only,
    "placeholder_marker": m_placeholder_marker,
    "intent_placeholder": m_intent_placeholder,
    "db_pool_size": m_db_pool_size,
    "asyncpg_statement_cache": m_asyncpg_statement_cache,
    "read_replica_unused": m_read_replica_unused,
    "rls_policy_coverage": m_rls_policy_coverage,
    "schema_drift": m_schema_drift,
    "audit_governance_columns": m_audit_governance_columns,
    "governance_columns_complete": m_governance_columns_complete,
    "public_endpoint_undeclared": m_public_endpoint_undeclared,
    "provider_health_check": m_provider_health_check,
    "provider_timeout": m_provider_timeout,
    "provider_circuit_breaker": m_provider_circuit_breaker,
    "provider_retry_policy": m_provider_retry_policy,
    "provider_raw_getenv": m_provider_raw_getenv,
    "provider_extra_packages": m_provider_extra_packages,
    "provider_orphan": m_provider_orphan,
    "ci_secret_scanning": m_ci_secret_scanning,
    "ci_dependency_scanning": m_ci_dependency_scanning,
    "placeholder_capability": m_placeholder_capability,
    "payment_webhook_signature": m_payment_webhook_signature,
    "orphan_job_module": m_orphan_job_module,
    "event_spine": m_event_spine,
    "stub_subscribers": m_stub_subscribers,
    "handover_unguarded": m_handover_unguarded,
    "ssrf_unguarded": m_ssrf_unguarded,
    "router_db_access": m_router_db_access,
    "public_endpoint_unregistered": m_public_endpoint_unregistered,
    "migration_heads": m_migration_heads,
    "middleware_order": m_middleware_order,
    "missing_setup_doc": m_missing_setup_doc,
    "noncanonical_lockfile": m_noncanonical_lockfile,
    "base_image_drift": m_base_image_drift,
    "raw_palette_classes": m_raw_palette_classes,
    "hex_drift": m_hex_drift,
    "inline_style": m_inline_style,
    "no_variant_system": m_no_variant_system,
    "primitive_no_ref": m_primitive_no_ref,
    "duplicate_primitive_markup": m_duplicate_primitive_markup,
    "button_missing_type": m_button_missing_type,
    "input_without_label": m_input_without_label,
    "swallowed_error": m_swallowed_error,
    "modal_no_escape": m_modal_no_escape,
    "modal_no_focus": m_modal_no_focus,
    "destructive_without_confirm": m_destructive_without_confirm,
    "icon_button_unnamed": m_icon_button_unnamed,
    "mutation_error_swallowed": m_mutation_error_swallowed,
    "orphan_feature_atom": m_orphan_feature_atom,
    "dead_feature_gate": m_dead_feature_gate,
    "orphaned_spec": m_orphaned_spec,
    "cache_coverage": m_cache_coverage,
    "orphan_frontend_module_route": m_orphan_frontend_module_route,
    "router_shadowed_by_package": m_router_shadowed_by_package,
    "chain_event_unwired": m_chain_event_unwired,
}


def run(root: Path, name: str, arg: str = "") -> tuple[int, str]:
    """Execute a registered measurement. Raises on an unknown name."""
    fn = MEASUREMENTS.get(name)
    if fn is None:
        raise KeyError(f"no measurement {name!r}")
    if arg and fn.__code__.co_argcount > 1:
        return fn(Ctx(root), arg)
    return fn(Ctx(root))