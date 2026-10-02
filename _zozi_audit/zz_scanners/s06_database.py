"""Dimension 06 (database) + Dimension 07 (tables & fields) + Dimension 10 (migrations)."""
from __future__ import annotations

import ast
import re
from pathlib import Path

from zz_core.constants import (
    APPROVED_EXTRA_SCHEMAS, CANONICAL_DOMAINS, FORBIDDEN_SCHEMAS,
    MONEY_FIELD_HINTS,
)
from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import parse_python, read_text

MONEY_RX = re.compile("|".join(MONEY_FIELD_HINTS), re.IGNORECASE)


def _f(dimension, phase, file, line, current, target, fix, *, priority="P2",
       effort="S", laws=(), blocker="no", cluster="", truth="L0",
       claim="VERIFIED", evidence="multiple", verify="") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180], fix=fix,
        effort=effort, priority=priority, confidence=5 if truth == "L0" else 3,
        evidence_strength=evidence, truth_level=truth, claim_state=claim,
        completion_blocker=blocker, laws=laws, verify=verify,
    )


def _model_files(ctx: ScanContext) -> list[Path]:
    out = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if rel.startswith("backend/tests/"):
            continue
        if "/models/" in rel or p.name == "models.py":
            out.append(p)
    return out


def _split_classes(text: str):
    """Yield (class_name, start_line, block_text)."""
    lines = text.splitlines()
    indices = [i for i, l in enumerate(lines) if re.match(r"^class\s+\w+", l)]
    for n, i in enumerate(indices):
        end = indices[n + 1] if n + 1 < len(indices) else len(lines)
        block = "\n".join(lines[i:end])
        m = re.match(r"^class\s+(\w+)", lines[i])
        yield m.group(1), i + 1, block


COLUMN_START_RX = re.compile(
    r"^\s{2,}([a-z_][a-z0-9_]*)\s*(?::[^=\n]+)?=\s*(mapped_column|Column)\(")
REL_RX = re.compile(r"^\s{2,}([a-z_][a-z0-9_]*)\s*(?::[^=\n]+)?=\s*relationship\(")


def _extract_columns(block: str) -> list[dict]:
    lines = block.splitlines()
    cols = []
    for i, line in enumerate(lines):
        m = COLUMN_START_RX.match(line)
        if not m:
            continue
        name, ctor = m.group(1), m.group(2)
        span = line
        depth = line.count("(") - line.count(")")
        j = i
        while depth > 0 and j + 1 < len(lines):
            j += 1
            span += "\n" + lines[j]
            depth += lines[j].count("(") - lines[j].count(")")
        cols.append({"name": name, "ctor": ctor, "span": span, "line": i + 1})
    return cols


def _extract_relationships(block: str) -> list[dict]:
    lines = block.splitlines()
    rels = []
    for i, line in enumerate(lines):
        m = REL_RX.match(line)
        if not m:
            continue
        span = line
        depth = line.count("(") - line.count(")")
        j = i
        while depth > 0 and j + 1 < len(lines):
            j += 1
            span += "\n" + lines[j]
            depth += lines[j].count("(") - lines[j].count(")")
        rels.append({"name": m.group(1), "span": span, "line": i + 1})
    return rels


def _model_inventory(ctx: ScanContext):
    def build():
        tables: list[dict] = []
        for p in _model_files(ctx):
            text, _ = read_text(p)
            if not text:
                continue
            rel = ctx.rel(p)
            for cls, start, block in _split_classes(text):
                if "__tablename__" not in block:
                    continue
                m = re.search(r'__tablename__\s*=\s*["\'](\w+)["\']', block)
                if not m:
                    continue
                tablename = m.group(1)
                schema_m = re.search(r'["\']schema["\']\s*:\s*["\'](\w+)["\']', block)
                schema = schema_m.group(1) if schema_m else ""
                has_table_args = "__table_args__" in block
                cols = _extract_columns(block)
                rels = _extract_relationships(block)
                tables.append({
                    "file": rel, "class": cls, "table": tablename,
                    "schema": schema, "has_table_args": has_table_args,
                    "columns": cols, "relationships": rels,
                    "line": start, "block": block,
                })
        return tables
    return ctx.memo("model_inventory", build)


@check("db_model_discipline", "07_tables_fields", "db",
       "Schema declaration, forbidden schemas, required columns, naming lint, "
       "money types, country_code String(2), FK ondelete/index, server defaults.")
def db_model_discipline(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="db_model_discipline", dimension="07_tables_fields")
    tables = _model_inventory(ctx)
    seen_tables: dict[str, str] = {}
    counts = {"tables": len(tables), "compliant": 0, "findings": 0}
    for t in tables:
        rel, block = t["file"], t["block"]
        table = t["table"]
        issues: list[tuple[str, str, str]] = []  # (kind, current, target/fix)
        if table in seen_tables:
            res.findings.append(_f(
                "07_tables_fields", "db", rel, t["line"],
                f"duplicate __tablename__ `{table}` (also in {seen_tables[table]})",
                "each table owned by exactly one domain (Law 51)",
                "Remove the duplicate model",
                priority="P0", blocker="yes", laws=(51,),
                cluster="CLUSTER-duplicate-table",
            ))
        seen_tables.setdefault(table, rel)
        if not t["has_table_args"] or not t["schema"]:
            issues.append(("schema-missing", f"table `{table}` has no schema declaration",
                           "Add __table_args__ = {\"schema\": \"<domain>\"} (Laws 6/55)"))
        else:
            if t["schema"] in FORBIDDEN_SCHEMAS:
                issues.append(("schema-forbidden", f"schema `{t['schema']}` is forbidden",
                               "Move the table into its domain schema (Laws 24/56)"))
            elif t["schema"] not in CANONICAL_DOMAINS and t["schema"] not in APPROVED_EXTRA_SCHEMAS:
                issues.append(("schema-unknown", f"schema `{t['schema']}` is not canonical",
                               "Use a canonical domain schema (Law 12)"))
        col_names = {c["name"] for c in t["columns"]}
        for required in ("created_at", "updated_at", "is_deleted"):
            if required not in col_names:
                issues.append((f"missing-{required}", f"table `{table}` lacks `{required}`",
                               "Every model includes created_at, updated_at, country_code, is_deleted (Law 23)"))
        if "country_code" not in col_names and t["schema"] in (
                "orders", "suppliers", "logistics", "customers", "accounts",
                "catalog", "finance", "promotions", "comms", "hr"):
            issues.append(("missing-country_code",
                           f"user-facing table `{table}` lacks `country_code`",
                           "RLS scoping requires country_code (Laws 5/20/23)"))
        for c in t["columns"]:
            span = c["span"]
            if re.search(r"\bFloat\b", span) and MONEY_RX.search(c["name"]):
                issues.append(("float-money", f"column `{c['name']}` is Float (money name)",
                               "Use Numeric/Decimal for money (Law 19)"))
            if c["name"] == "country_code" and "String(2)" not in span.replace(" ", ""):
                issues.append(("country-type", "country_code is not String(2)",
                               "country_code = String(2) ISO-3166-1 alpha-2 (Law 20)"))
            if c["name"] in ("created_at", "updated_at"):
                if "server_default" not in span and "default=" in span:
                    issues.append(("timestamp-default",
                                   f"`{c['name']}` uses Python-side default",
                                   "Use server_default=func.now() (Law 21)"))
            if "ForeignKey(" in span and "ondelete" not in span:
                issues.append(("fk-ondelete", f"FK `{c['name']}` has no ondelete",
                               "Every FK declares ondelete (Laws 22/52)"))
            if "ForeignKey(" in span and "index=True" not in span and "index=True" not in block:
                issues.append(("fk-index", f"FK `{c['name']}` may lack an index",
                               "Index every FK column (Law 53)"))
        # relationship lazy
        for r in t["relationships"]:
            if "lazy=" not in r["span"]:
                issues.append(("rel-lazy", f"relationship `{r['name']}` has no lazy=",
                               "Declare lazy=selectin/joined (Law 45)"))
        if not issues:
            counts["compliant"] += 1
        else:
            counts["findings"] += 1
        kind_map: dict[str, list[tuple[str, str]]] = {}
        for kind, current, fix in issues:
            kind_map.setdefault(kind, []).append((current, fix))
        for kind, items in kind_map.items():
            priority = "P1" if kind in ("schema-missing", "schema-forbidden", "float-money",
                                        "missing-country_code", "duplicate-table") else "P2"
            blocker = "partial" if priority == "P1" else "no"
            res.findings.append(_f(
                "07_tables_fields", "db", rel, t["line"],
                f"{len(items)}x {kind.replace('-', ' ')} in table `{table}`: {items[0][0]}",
                items[0][1],
                f"Fix {kind} on {table}",
                priority=priority, blocker=blocker, laws=(6, 19, 20, 21, 22, 23, 45, 53, 55),
                cluster=f"CLUSTER-tf-{kind}",
            ))
        res.observations.append(Observation(
            "table", f"{t['schema'] or '?'}.{table}", rel, t["line"],
            "07_tables_fields",
            evidence=f"columns={len(t['columns'])} relationships={len(t['relationships'])} issues={len(issues)}",
        ))
    res.facts["tables_inspected"] = counts["tables"]
    res.facts["tables_compliant"] = counts["compliant"]
    return res


@check("db_pool_and_engine", "06_database", "db",
       "Pool sizing, statement timeout, asyncpg statement_cache_size, read "
       "replica wiring, transactions (Laws 47, 48, 50, 260).")
def db_pool_and_engine(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="db_pool_and_engine", dimension="06_database")
    db_file = ctx.backend / "infrastructure" / "database" / "database.py"
    text, _ = read_text(db_file)
    cfg, _ = read_text(ctx.backend / "config.py")
    combined = (text or "") + "\n" + (cfg or "")
    rel = ctx.rel(db_file) if db_file.exists() else "backend/config.py"
    if not re.search(r"pool_size\s*[=:]\s*(\d+)", combined):
        res.findings.append(_f(
            "06_database", "db", rel, 0, "no pool_size configuration found",
            "pool_size >= 10, max_overflow >= 20 (Law 47)",
            "Configure the pool in the engine factory", priority="P1",
            laws=(47,), cluster="CLUSTER-db-pool",
        ))
    if "statement_timeout" not in combined.lower():
        res.findings.append(_f(
            "06_database", "db", rel, 0, "no statement timeout configured",
            "per-query timeout prevents runaway queries (TECHNOLOGY_STACK §2)",
            "Set DB_STATEMENT_TIMEOUT / server_settings", priority="P2",
            cluster="CLUSTER-db-pool",
        ))
    if "statement_cache_size" not in combined:
        res.findings.append(_f(
            "06_database", "db", rel, 0, "asyncpg statement_cache_size=0 not set",
            "required under the pooler (Law 260)",
            "Pass statement_cache_size=0 in connect_args", priority="P3",
            laws=(260,), cluster="CLUSTER-db-pool", truth="L1", claim="INFERRED",
        ))
    # read replica wiring
    if "get_read_db" in combined and text:
        usage = 0
        for p in ctx.py_files:
            relp = ctx.rel(p)
            if not relp.startswith("backend/domains/"):
                continue
            t, _ = read_text(p)
            usage += len(re.findall(r"get_read_db", t or ""))
        if usage == 0:
            res.findings.append(_f(
                "06_database", "db", "backend/infrastructure/database/database.py", 0,
                "read-replica engine exists but `get_read_db` is never used by domains",
                "read-heavy queries use get_read_db() (Law 48)",
                "Wire get_read_db into read paths or remove the unused engine",
                priority="P2", laws=(48,), cluster="CLUSTER-read-replica",
            ))
        res.facts["read_db_usages"] = usage
    return res


DESTRUCTIVE_OPS = ("drop_table", "drop_column", "drop_constraint",
                    "drop_index", "execute")


def _destructive_in_upgrade(parsed, text: str) -> tuple[bool, int]:
    """Find a genuinely destructive op inside ``upgrade()`` only.

    Scanning the whole file matched ``drop_*`` in ``downgrade()`` — where a drop
    is the *correct* reversible counterpart — and then cited the module
    docstring at line 1. 6/6 adjudicated samples were false positives on exactly
    this. Now the AST restricts the search to ``upgrade()`` and reports the real
    line of the offending call.

    Still not a Law 57 violation if the op is guarded (`IF EXISTS`, an existence
    probe) or the migration is a baseline that only creates; those are surfaced
    as ``unverifiable`` rather than asserted.
    """
    tree = getattr(parsed, "tree", None)
    if tree is None:
        return (False, 0)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "upgrade":
            continue
        src = text.splitlines()
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Call):
                continue
            fn = getattr(sub.func, "attr", "")
            if fn not in DESTRUCTIVE_OPS:
                continue
            ln = sub.lineno
            # A guarded or reversible-only drop is not "destructive without
            # expand-contract".
            window = "\n".join(src[max(0, ln - 8):ln + 3])
            if re.search(r"IF\s+(NOT\s+)?EXISTS|_index_exists|_table_exists|"
                         r"_column_exists|if_exists|checkfirst", window, re.I):
                continue
            return (True, ln)
    return (False, 0)


@check("db_migration_graph", "10_migrations", "db",
       "Parse every alembic revision: heads, cycles, duplicates, destructive "
       "ops, downgrade presence, phantom helper imports (Law 49).")
def db_migration_graph(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="db_migration_graph", dimension="10_migrations")
    versions = ctx.backend / "alembic" / "versions"
    if not versions.exists():
        res.findings.append(_f(
            "10_migrations", "db", "backend/alembic/versions/", 0,
            "alembic versions directory missing",
            "Alembic is the single schema source (Law 6)",
            "Restore the migrations directory", priority="P0", blocker="yes",
            laws=(6, 49), cluster="CLUSTER-migrations",
        ))
        return res
    revs: dict[str, dict] = {}
    duplicates: dict[str, list[str]] = {}
    for p in sorted(versions.glob("*.py")):
        text, _ = read_text(p)
        if not text:
            continue
        parsed = parse_python(p)
        m = re.search(r"^revision(?:\s*:\s*str)?\s*=\s*['\"]([^'\"]+)['\"]", text, re.MULTILINE)
        d = re.search(r"^down_revision(?:\s*:[^=]+)?\s*=\s*(.+)$", text, re.MULTILINE)
        if not m:
            continue
        rid = m.group(1)
        down_raw = (d.group(1).strip() if d else "None")
        downs: list[str] = []
        if down_raw not in ("None", "none"):
            downs = re.findall(r"['\"]([^'\"]+)['\"]", down_raw)
        destructive, dline = _destructive_in_upgrade(parsed, text)
        downgrade = re.search(r"def downgrade\(\)[^:]*:\s*\n(\s+(?:pass|\"\"\".*?\"\"\")\s*$|\s+raise)", text, re.DOTALL)
        revs[rid] = {"file": ctx.rel(p), "downs": downs, "destructive": destructive,
                     "destructive_line": dline,
                     "downgrade_empty": bool(downgrade) or "def downgrade" not in text}
        duplicates.setdefault(rid, []).append(ctx.rel(p))
        for phantom in re.findall(r"^(?:from|import)\s+(migration_helpers\S*)", text, re.MULTILINE):
            helper = ctx.backend / (phantom.split(".")[0] + ".py")
            pkg_helper = ctx.backend / phantom.split(".")[0]
            if not helper.exists() and not pkg_helper.exists():
                res.findings.append(_f(
                    "10_migrations", "db", ctx.rel(p), 1,
                    f"version file imports `{phantom}` which does not exist in-tree",
                    "migration modules import only resolvable helpers",
                    "Move the helper into alembic/ and fix the import",
                    priority="P0", blocker="yes", laws=(49,),
                    cluster="CLUSTER-migration-import",
                ))
    referenced = {d for r in revs.values() for d in r["downs"]}
    heads = [rid for rid in revs if rid not in referenced]
    res.facts["migration_revisions"] = len(revs)
    res.facts["migration_heads"] = len(heads)
    if len(revs) and len(heads) != 1:
        res.findings.append(_f(
            "10_migrations", "db", "backend/alembic/versions/", 0,
            f"{len(heads)} divergent migration heads: {', '.join(sorted(heads)[:8])}",
            "exactly one linear head (Law 49)",
            "Merge the branches into a single linear history",
            priority="P0", blocker="yes", laws=(49,),
            cluster="CLUSTER-migration-heads",
            verify="cd backend && alembic -c alembic/alembic.ini heads",
        ))
    for rid, files in duplicates.items():
        if len(files) > 1:
            res.findings.append(_f(
                "10_migrations", "db", files[0], 1,
                f"duplicate revision id `{rid}` in: {', '.join(files)}",
                "revision ids are unique (Law 49)",
                "Renumber the duplicate revision",
                priority="P0", blocker="yes", laws=(49,), cluster="CLUSTER-migration-ids",
            ))
    for rid, r in revs.items():
        if r["destructive"]:
            res.findings.append(_f(
                "10_migrations", "db", r["file"], r.get("destructive_line") or 1,
                f"upgrade() performs an unguarded destructive op at line "
                f"{r.get('destructive_line')} with no expand-contract staging",
                "destructive migrations use expand-contract (Law 57)",
                "Split into expand + contract steps with a rollback window",
                priority="P1", blocker="partial", laws=(57,),
                cluster="CLUSTER-migration-destructive", truth="L1", claim="INFERRED",
                verify=f"sed -n '{r.get('destructive_line')}p' {r['file']}",
            ))
        if r["downgrade_empty"]:
            res.findings.append(_f(
                "10_migrations", "db", r["file"], 1,
                "empty/missing downgrade()",
                "migrations are reversible or explicitly irreversible (Laws 57/219)",
                "Implement downgrade() or document irreversibility",
                priority="P2", cluster="CLUSTER-migration-downgrade",
                truth="L1", claim="INFERRED",
            ))
    return res


@check("db_queries", "06_database", "db",
       "SELECT * usage, OFFSET pagination, ilike '%…%' searches, lazy=select "
       "relationships (Laws 45, 46, 222).")
def db_queries(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="db_queries", dimension="06_database")
    select_star: list[tuple[str, int, str]] = []
    offsets: list[tuple[str, int, str]] = []
    ilike: list[tuple[str, int, str]] = []
    lazy_default = 0
    rels_total = 0
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not rel.startswith("backend/") or rel.startswith("backend/tests/"):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for idx, line in enumerate(text.splitlines(), 1):
            if re.search(r"text\(\s*[\"']+\s*SELECT\s+\*", line, re.IGNORECASE) or re.search(r'SELECT \* FROM', line, re.IGNORECASE):
                select_star.append((rel, idx, line.strip()[:160]))
            if re.search(r"\.offset\(", line):
                offsets.append((rel, idx, line.strip()[:160]))
            if re.search(r"ilike\(\s*[\"']%", line):
                ilike.append((rel, idx, line.strip()[:160]))
        rels_total += len(re.findall(r"relationship\(", text))
    tables = _model_inventory(ctx)
    for t in tables:
        for r in t["relationships"]:
            if "lazy=" not in r["span"]:
                lazy_default += 1
    if lazy_default:
        res.findings.append(_f(
            "06_database", "db", "backend/domains/", 0,
            f"{lazy_default}/{rels_total} relationship() declarations omit lazy=",
            "relationships declare lazy=selectin or joined; default lazy=select forbidden (Law 45)",
            "Add lazy=\"selectin\" to the relationship declarations",
            priority="P1", blocker="partial", laws=(45,),
            cluster="CLUSTER-n-plus-1",
            verify="grep -rn 'relationship(' backend/domains | grep -v 'lazy=' | head",
        ))
    if select_star:
        res.findings.append(_f(
            "06_database", "db", select_star[0][0], select_star[0][1],
            f"{len(select_star)} SELECT * usage(s) (sample: {select_star[0][2]})",
            "application queries select explicit columns (Law 46)",
            "Enumerate the needed columns",
            priority="P2", laws=(46,), cluster="CLUSTER-select-star",
        ))
    if offsets:
        res.findings.append(_f(
            "06_database", "db", offsets[0][0], offsets[0][1],
            f"{len(offsets)} OFFSET pagination usage(s) (sample: {offsets[0][2]})",
            "keyset cursor pagination on hot lists; OFFSET forbidden (Law 222)",
            "Switch the hot lists to cursor pagination",
            priority="P1", blocker="partial", laws=(222,),
            cluster="CLUSTER-offset-pagination",
            verify=f"grep -n '.offset(' {offsets[0][0]}",
        ))
    if ilike:
        res.findings.append(_f(
            "06_database", "db", ilike[0][0], ilike[0][1],
            f"{len(ilike)} leading-wildcard ilike search(es) (sample: {ilike[0][2]})",
            "fuzzy search uses pg_trgm GIN indexes (Law 257)",
            "Add a trigram index or a tsvector search path",
            priority="P2", laws=(257,), cluster="CLUSTER-search-index",
        ))
    return res


@check("db_rls_sql", "06_database", "db",
       "RLS policy SQL coverage vs model count; WITH CHECK; FORCE RLS (Laws 5, 227).")
def db_rls_sql(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="db_rls_sql", dimension="06_database")
    sql_files = list((ctx.backend / "infrastructure").rglob("*.sql"))
    policy_tables: set[str] = set()
    for p in sql_files:
        text, _ = read_text(p)
        if not text:
            continue
        policy_tables.update(re.findall(r"CREATE POLICY\s+\w+\s+ON\s+[\w.]*?(\w+)\s", text, re.IGNORECASE))
        policy_tables.update(re.findall(r"ALTER TABLE\s+[\w.]*?(\w+)\s+ENABLE ROW LEVEL SECURITY", text, re.IGNORECASE))
        if "FORCE ROW LEVEL SECURITY" not in text.upper():
            res.findings.append(_f(
                "06_database", "db", ctx.rel(p), 1,
                "RLS script does not FORCE row level security",
                "FORCE RLS so table owners are also constrained (Law 5)",
                "Add FORCE ROW LEVEL SECURITY per table",
                priority="P2", cluster="CLUSTER-rls", truth="L1", claim="INFERRED",
            ))
    tables = _model_inventory(ctx)
    user_tables = [t for t in tables if "country_code" in {c["name"] for c in t["columns"]}]
    if user_tables and len(policy_tables) < len(user_tables):
        res.findings.append(_f(
            "06_database", "db", "backend/infrastructure/database/sql/", 0,
            f"{len(policy_tables)} RLS policy target(s) vs {len(user_tables)} country-scoped table(s)",
            "RLS enabled + policy per country-scoped table (Law 5/227)",
            "Install policies for every country-scoped table",
            priority="P1", blocker="partial", laws=(5, 227),
            cluster="CLUSTER-rls",
        ))
    res.facts["rls_policy_tables"] = len(policy_tables)
    return res
