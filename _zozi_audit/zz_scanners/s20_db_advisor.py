"""Dimension 07 (extension) — database and table management.

The prompt's dimension 07 asserts per-table defects. This module adds the
*management* view the codebase has no representation of at all: which tables
lack an index for a column they filter on, which models and migrations have
drifted apart, and what a table's management posture actually is. It also emits
the schema-side recommendations (indexes, constraints, mixin adoption) that the
compilation step turns into work items.
"""
from __future__ import annotations

import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, Observation, Recommendation, ScanContext
from zz_core.registry import check
from zz_core.util import parse_python, read_text

# Columns that are almost always filtered or sorted on. A table that carries
# one of these and declares no index on it is a measurable management gap.
HOT_COLUMNS = (
    "country_code", "status", "created_at", "updated_at", "user_id",
    "order_id", "supplier_id", "product_id", "tenant_id", "is_deleted",
    "email", "slug", "parent_id", "currency", "email",
)
MONEY_HINT = re.compile(
    r"\b(amount|total|price|balance|subtotal|tax|vat|commission|refund|payout|"
    r"cost|revenue|salary|fee|discount|shipping)_?\w*\b", re.I)
RATE_HINT = re.compile(r"(_rate|_percent|_ratio|_score|_weight|_weightage)$", re.I)


def _models(ctx: ScanContext) -> list[dict]:
    out: list[dict] = []
    for p in ctx.py_files:
        rel = ctx.rel(p).replace("\\", "/")
        if not re.match(r"backend/(domains|infrastructure)/.*models.*\.py$", rel) and \
                "/models/" not in rel:
            continue
        parsed = parse_python(p)
        if not parsed.tree:
            continue
        import ast
        for node in ast.walk(parsed.tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {b.id for b in node.bases if isinstance(b, ast.Name)} | \
                    {b.attr for b in node.bases if isinstance(b, ast.Attribute)}
            if not any("Base" in b or "Model" in b or "Mixin" in b for b in bases):
                continue
            table, schema = "", ""
            cols: dict[str, str] = {}
            indexed_inline: set[str] = set()
            indexes: list[str] = []
            rels_without_lazy = 0
            rels_total = 0
            floats: list[tuple[str, int]] = []

            def seg(node) -> str:
                """Exact source text of a node.

                Slicing the file by ``lineno`` is off by one for tuple targets
                and truncates multi-line calls; ``get_source_segment`` is exact.
                """
                try:
                    return ast.get_source_segment(parsed.text, node) or ""
                except Exception:
                    return ""

            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name) and t.id == "__tablename__":
                            table = stmt.value.value if isinstance(stmt.value, ast.Constant) else ""
                        if isinstance(t, ast.Name) and t.id == "__table_args__":
                            src = seg(stmt)
                            indexes = re.findall(r'["\']([a-z_]+_idx|[a-z_]+_pkey|'
                                                  r'ix_[a-z0-9_]+|idx_[a-z0-9_]+)', src)
                            # the codebase writes {"schema": "catalog"}
                            m = re.search(r'["\']schema["\']\s*[:,]\s*["\']([a-z_]+)["\']', src)
                            if m:
                                schema = m.group(1)
                # A SQLAlchemy column is either `x: M = Column(...)` (AnnAssign) or
                # the bare `x = Column(...)` style this codebase actually uses.
                col_stmt = None
                rel_call = None
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    col_stmt = (stmt.target.id, stmt.lineno, stmt)
                    if isinstance(stmt.value, ast.Call):
                        rel_call = (stmt.target.id, stmt.value)
                elif isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                    fn = getattr(stmt.value.func, "attr", getattr(stmt.value.func, "id", ""))
                    if stmt.targets and isinstance(stmt.targets[0], ast.Name):
                        name0 = stmt.targets[0].id
                        if fn in ("Column", "relationship", "Index", "mapped_column",
                                  "ForeignKey", "Computed"):
                            col_stmt = (name0, stmt.lineno, stmt)
                        if fn == "relationship":
                            rel_call = (name0, stmt.value)
                if col_stmt:
                    name, line, node_ = col_stmt
                    src = seg(node_)
                    cols[name] = src
                    if re.search(r"\bindex\s*=\s*True\b", src):
                        indexed_inline.add(name)
                    if "Float" in src and MONEY_HINT.search(name) and not RATE_HINT.search(name):
                        floats.append((name, line))
                if rel_call is not None:
                    rels_total += 1
                    if not any(kw.arg == "lazy" for kw in rel_call[1].keywords):
                        rels_without_lazy += 1
            if table:
                out.append({
                    "class": node.name, "file": rel,
                    "line": node.lineno, "table": table, "schema": schema,
                    "columns": cols, "indexes": indexes,
                    "indexed_inline": sorted(indexed_inline),
                    "rels_total": rels_total, "rels_no_lazy": rels_without_lazy,
                    "money_floats": floats,
                    "has_audit": all(c in cols for c in ("created_at", "updated_at")),
                    "has_soft_delete": "is_deleted" in cols or "deleted_at" in cols,
                    "has_version": "version" in cols,
                    "has_country": "country_code" in cols,
                })
    # `schema` is usually declared once per module, not on every class, so a
    # class without its own __table_args__ inherits the module-level one.
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not re.match(r"backend/(domains|infrastructure)/.*models.*\.py$", rel):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        m = re.search(r'__table_args__\s*=\s*\(?\s*\{[^}]*["\']schema["\']\s*,'
                      r'\s*["\']([a-z_]+)["\']', text, re.S)
        if not m:
            continue
        for entry in out:
            if entry["file"] == rel and not entry["schema"]:
                entry["schema"] = m.group(1)
    return out


@check("table_management_posture", "07_tables_fields", "db",
       "Per-table management posture: unindexed hot columns, money typed as "
       "Float, missing audit/version/country columns, and relationship "
       "loading strategy.")
def table_management_posture(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="table_management_posture", dimension="07_tables_fields")
    models = _models(ctx)
    unindexed: list[dict] = []
    money_float: list[dict] = []
    no_audit: list[str] = []
    no_soft: list[str] = []
    no_version: list[str] = []
    no_country: list[str] = []
    no_schema: list[str] = []
    rels_no_lazy = rels_total = 0
    for m in models:
        indexed = " ".join(m["indexes"]).lower()
        # `Column(..., index=True)` creates an index that produces no name in
        # __table_args__; ignoring it inflates the unindexed count by ~3x.
        inline = set(m.get("indexed_inline") or ())
        for col in HOT_COLUMNS:
            if col in m["columns"] and col not in indexed and col not in inline \
                    and col not in ("created_at", "updated_at"):
                unindexed.append({"table": f"{m['schema']}.{m['table']}" if m["schema"] else m["table"],
                                  "column": col, "file": m["file"], "line": m["line"]})
        if m["money_floats"]:
            money_float.append({"table": m["table"], "file": m["file"],
                                "line": m["money_floats"][0][1], "column": m["money_floats"][0][0]})
        if not m["has_audit"]:
            no_audit.append(f"{m['file']}:{m['line']} ({m['table']})")
        if not m["has_soft_delete"]:
            no_soft.append(f"{m['file']}:{m['line']} ({m['table']})")
        if not m["has_version"]:
            no_version.append(f"{m['file']}:{m['line']} ({m['table']})")
        if not m["has_country"]:
            no_country.append(f"{m['file']}:{m['line']} ({m['table']})")
        if not m["schema"]:
            no_schema.append(f"{m['file']}:{m['line']} ({m['table']})")
        rels_no_lazy += m["rels_no_lazy"]
        rels_total += m["rels_total"]

    res.facts["table_management"] = {
        "models": len(models),
        "tables_without_schema": len(no_schema),
        "relationships_total": rels_total,
        "relationships_without_lazy": rels_no_lazy,
        "unindexed_hot_columns": len(unindexed),
        "money_typed_float": len(money_float),
        "missing_audit_columns": len(no_audit),
        "missing_soft_delete": len(no_soft),
        "missing_version": len(no_version),
        "missing_country_code": len(no_country),
        "unindexed_sample": unindexed[:25],
    }
    for u in unindexed[:30]:
        res.observations.append(Observation(
            "table", u["file"], u["file"], u["line"], "07_tables_fields",
            evidence=f"table {u['table']} filters on `{u['column']}` with no index",
        ))
    for m in models[:60]:
        res.observations.append(Observation(
            "table", m["file"], m["file"], m["line"], "07_tables_fields",
            evidence=f"{(m['schema'] + '.') if m['schema'] else ''}{m['table']}: "
                     f"cols={len(m['columns'])} idx={len(m['indexes'])} "
                     f"rels={m['rels_total']}(no-lazy {m['rels_no_lazy']}) "
                     f"audit={m['has_audit']} soft={m['has_soft_delete']} "
                     f"ver={m['has_version']} cc={m['has_country']}",
        ))

    if unindexed:
        worst = "; ".join(f"{u['table']}.{u['column']}" for u in unindexed[:8])
        res.findings.append(Finding(
            id="DB-unindexed-hot-column", dimension="07_tables_fields", phase="db",
            cluster="CLUSTER-table-index", file="backend/domains",
            current=f"{len(unindexed)} (table, column) pair(s) are filtered or "
                    f"sorted on with no declared index",
            target="every hot filter/sort column is indexed, with a matching migration",
            delta=f"{len(unindexed)} sequential-scan paths; e.g. {worst}",
            fix="add composite indexes in the model __table_args__ AND the matching "
                "Alembic migration (order: tenant/country, status, created_at)",
            effort="L", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="python _zozi_audit/zozi_compile.py --report db",
            snippet=worst,
        ))
        res.recommendations.append(Recommendation(
            area="data", dimension="07_tables_fields",
            title="Add the missing indexes as model + migration pairs",
            rationale="Index gaps are silent: the app works, then degrades as volume "
                      "grows, and the first signal is a slow production query.",
            current=f"{len(unindexed)} unindexed hot (table, column) pairs.",
            proposal="generate the index list, add each to the model __table_args__ "
                     "and write one Alembic migration creating them CONCURRENTLY; add "
                     "a test asserting every HOT_COLUMN present in a model is indexed.",
            benefit="removes the sequential-scan path before it becomes an incident",
            effort="M", impact="high", category="schema",
            evidence=f"backend/domains/**/models/*.py ({worst})",
        ))
    if money_float:
        res.findings.append(Finding(
            id="DB-money-float", dimension="07_tables_fields", phase="db",
            cluster="CLUSTER-table-type", file="backend/domains",
            current=f"{len(money_float)} monetary column(s) are typed Float",
            target="every monetary column is Numeric with an explicit scale",
            delta="float storage accumulates rounding error in the ledger",
            fix="change the column to Numeric(precision, 2) and migrate; exclude "
                "rate/percent/ratio columns from this rule",
            effort="M", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rEn 'Column\\(Float.*(amount|total|price|balance)' backend/domains",
            snippet="; ".join(f"{m['table']}.{m['column']}@{m['file']}:{m['line']}"
                              for m in money_float[:6]),
        ))
    if no_audit or no_soft:
        # Law 23 requires created_at/updated_at, country_code and is_deleted.
        # `version` is NOT a universal requirement: it was added by a
        # performance migration for high-contention tables, so a missing
        # version column is an opportunity, not a defect.
        res.findings.append(Finding(
            id="DB-missing-governance-columns", dimension="07_tables_fields", phase="db",
            cluster="CLUSTER-table-governance", file="backend/domains",
            current=f"{len(no_audit)} table(s) lack audit timestamps and "
                    f"{len(no_soft)} lack soft delete",
            target="every table carries created_at, updated_at, country_code and "
                   "is_deleted (Law 23)",
            delta="rows cannot be attributed or restored, and tenant/RLS scoping "
                  "cannot be applied",
            fix="inherit the mixins (or set them on the declarative base) instead of "
                "declaring columns per model; add a compliance test over Base.metadata",
            effort="M", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="pytest backend/tests/architecture -k compliance",
            snippet="; ".join(no_audit[:5]),
        ))
    if no_version:
        res.recommendations.append(Recommendation(
            area="data", dimension="07_tables_fields",
            title="Add optimistic-locking `version` to high-contention tables",
            rationale="`version` is not required by the architecture rules, but "
                      "concurrent updates on these tables can silently overwrite each "
                      "other, which matters most in finance and orders.",
            current=f"{len(no_version)} of {len(models)} tables have no version column.",
            proposal="add `version` (with a SQLAlchemy version_id_col) to the tables "
                     "that are written from more than one process: ledger, payouts, "
                     "orders, inventory, KYC; leave reference tables alone.",
            benefit="prevents lost updates in exactly the places where a lost update "
                    "costs money",
            effort="M", impact="medium", category="schema",
            evidence=f"backend/domains/**/models/*.py ({len(no_version)} tables)",
        ))
    if rels_total and rels_no_lazy / rels_total > 0.3:
        res.findings.append(Finding(
            id="DB-relationship-loading", dimension="07_tables_fields", phase="db",
            cluster="CLUSTER-table-relation", file="backend/infrastructure/database",
            current=f"{rels_no_lazy} of {rels_total} relationship() calls omit lazy=",
            target="every relationship declares an explicit loading strategy",
            delta="implicit lazy loads issue hidden N+1 queries and, under asyncio, "
                  "can raise MissingGreenlet at runtime",
            fix="set lazy='raise' on the declarative base and annotate each "
                "relationship with 'selectin' or 'joined'",
            effort="L", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rEc 'relationship\\(' backend/domains --include=*.py | "
                   "awk -F: '$2>0' | wc -l",
        ))
    return res


@check("schema_migration_drift", "07_tables_fields", "db",
       "Migrations must reference the schemas the ORM actually declares; a "
       "mismatch means the index/constraint is created somewhere else, or nowhere.")
def schema_migration_drift(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="schema_migration_drift", dimension="07_tables_fields")
    models = _models(ctx)
    orm_schemas = sorted({m["schema"] for m in models if m["schema"]})
    legacy_schemas: dict[str, list[str]] = {}
    versions = ctx.backend / "alembic" / "versions"
    files = sorted(versions.glob("*.py")) if versions.exists() else []
    # Index migrations in this codebase declare their targets as Python list
    # literals (SINGLE_COUNTRY_INDEXES / COMPOSITE_INDEXES = [(schema, table, ...)]).
    # Reading the raw text for any quoted pair would match index *names* and
    # report them as schemas, so only those assignments are parsed.
    LISTS = ("SINGLE_COUNTRY_INDEXES", "COMPOSITE_INDEXES", "TABLES",
             "TABLE_LIST", "INDEX_TABLES")
    for p in files:
        text, _ = read_text(p)
        if not text:
            continue
        for list_name in LISTS:
            lm = re.search(rf"^\s*{list_name}\s*(?::[^=]+)?=\s*\[(.*?)\]",
                           text, re.S | re.M)
            if not lm:
                continue
            for tm in re.finditer(r'[(,]\s*["\']([a-z_]+)["\']\s*,\s*["\']([a-z_]+)["\']',
                                  lm.group(1)):
                schema, table = tm.group(1), tm.group(2)
                if schema in orm_schemas or schema in ("pg_catalog", "information_schema"):
                    continue
                legacy_schemas.setdefault(schema, []).append(f"{p.name}:{table}")
    res.facts["schema_drift"] = {
        "migration_files": len(files),
        "orm_schemas": orm_schemas,
        "legacy_schemas_in_migrations": {k: len(v) for k, v in legacy_schemas.items()},
        "samples": {k: v[:5] for k, v in legacy_schemas.items()},
    }
    for schema, sites in sorted(legacy_schemas.items(), key=lambda t: -len(t[1])):
        res.observations.append(Observation(
            "migration", f"backend/alembic/versions/{sites[0].split(':')[0]}",
            "backend/alembic/versions", 0, "07_tables_fields",
            evidence=f"{len(sites)} reference(s) to schema `{schema}`, which no ORM "
                     f"model declares",
        ))
    if legacy_schemas:
        detail = ", ".join(f"{k}({len(v)})" for k, v in
                           sorted(legacy_schemas.items(), key=lambda t: -len(t[1])))
        res.findings.append(Finding(
            id="DB-schema-drift", dimension="07_tables_fields", phase="db",
            cluster="CLUSTER-table-drift", file="backend/alembic/versions",
            current=f"migrations reference schemas no ORM model declares: {detail}",
            target="migration schema names match the ORM metadata exactly",
            delta="these references point at schemas that were renamed/split by an "
                  "earlier migration, so the migration fails on a fresh database "
                  "and the index/constraint is never created",
            fix="rename the schema references in the affected migrations to the ORM "
                "schema, and add a test that every schema literal in a migration "
                "exists in Base.metadata",
            effort="M", priority="P0", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="yes",
            verify="pytest backend/tests/architecture -k schema",
            snippet="; ".join(f"{k}: {v[0]}" for k, v in legacy_schemas.items()),
        ))
        res.recommendations.append(Recommendation(
            area="data", dimension="07_tables_fields",
            title="Reconcile migration schema names with ORM metadata",
            rationale="Schema drift means database objects the app does not know "
                      "about. It is invisible until a query or constraint fails.",
            current=f"drifted schemas: {detail}",
            proposal="1) diff every schema literal in migrations against "
                     "Base.metadata.schemas; 2) write corrective migrations; "
                     "3) add a CI test asserting the two sets are equal.",
            benefit="removes an entire class of production-only database failure",
            effort="M", impact="high", category="schema",
            evidence="backend/alembic/versions vs backend/domains/**/models",
        ))
    return res
