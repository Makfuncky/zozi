# system_architecture_audit.py — Design Spec

**Goal:** Audit the ZOZI codebase against the **target architecture** defined in
`Architecture_Diagram.md` §10 (Canonical Architecture Contract). This spec replaces the current
naive pattern-matcher behaviour and fixes the known false-positive bugs (DBA06 FK parse, PERF4
no-limit heuristic, SEC5/SEC101 `text(...)` over-flagging, FEH402 skeleton keys).

The audit must be **evidence-based**: every finding carries `file:line`, the matched evidence, the
rule id, the §10 clause it violates, and a concrete fix. Severity is derived from the contract,
not from raw counts.

---

## 1. Architecture of the auditor

```
system_architecture_audit.py
├── CONTRACT            # hard-coded mirror of Architecture_Diagram.md §10
│   ├── LAYERS         # allow-list of layer names
│   ├── ALLOWED_EDGES  # the circuit matrix (§10.2)
│   ├── SCHEMA_POLICY  # §10.3
│   ├── SECURITY_POLICY# §10.4
│   ├── PERF_POLICY    # §10.5
│   ├── PROVIDER_POLICY# §10.6
│   ├── FRONTEND_POLICY# §10.7
│   └── SCALING_POLICY # §10.8
├── parsers/
│   ├── import_graph   # build module→module edges (for CIR1/DG2/MV/DOM)
│   ├── fk_parser      # FIXED: resolve real schema from ORM metadata (DBA06)
│   ├── query_parser   # FIXED: detect unparameterized SQL + OFFSET (PERF4/DBA32)
│   ├── security_parser# FIXED: untrusted concat only (SEC5/SEC101)
│   └── frontend_parser# FIXED: dynamic-list index keys + inline <style> (FEH402/DS02)
├── rules/             # one function per rule id, returns Finding[]
├── severity.py        # maps rule → 🔴/🟡/🔵 + debt weight
└── report.py          # emits SYSTEM_AUDIT_REPORT.md + JSON
```

The auditor is **read-only** over the codebase; it never mutates source.

---

## 2. Contract encoding (the single source of truth)

```python
LAYERS = {
    "main", "middleware", "dependencies", "routers", "controllers",
    "services", "providers", "db", "models", "utils", "data",
    "events", "jobs", "settings", "monitoring",
    # frontend
    "app", "components", "lib", "hooks", "services_f", "theme",
    "styles", "types", "utils_f",
}

# ALLOWED_EDGES[layer] = set of layers it may import (§10.2)
ALLOWED_EDGES = {
    "main":        {"middleware","dependencies","routers","db","utils","lifespan","data"},
    "routers":     {"controllers","schemas","auth_deps","db"},
    "controllers": {"services","models","db","auth_deps"},
    "services":    {"models","db","utils","providers","redis"},
    "providers":   {"providers_base","utils","settings"},
    "db":          {"db_base","settings"},
    "middleware":  {"utils","settings","db"},
    "events":      {"services","db","providers"},
    "jobs":        {"services","db","providers"},
    "lib":         {"backend_api"},   # frontend only talks to /api/v1/*
}
SHARED_REF_TARGETS = {  # exempt domain column-name FKs (§10.3)
    "customer.user", "admin.user", "country.country_configs",
    "user_id", "created_by", "updated_by", "deleted_by",
}
```

---

## 3. Parser fixes (critical)

### 3.1 FK parser — fix DBA06 (was 131 false 🔴)
Old (buggy): `schema, table = fk_target.split(".")[0], fk_target.split(".")[-1]`
assumes `ForeignKey("schema.table")`. SQLAlchemy syntax is `ForeignKey("table.column")`.

New:
```python
def resolve_fk_target(fk_target: str, metadata):
    table_name = fk_target.split(".")[0]          # "coupons"
    ref_table = metadata.tables.get(table_name)   # resolve from ORM
    if ref_table is None:
        return VIOLATION("DBA06", fk_target)       # genuine unknown ref
    ref_schema = ref_table.schema                 # REAL schema
    if ref_schema is None or ref_schema in SHARED_REF_TARGETS:
        return OK
    # cross-domain FK to a domain schema table (e.g. customer.user.id) is ALLOWED;
    # only a FK whose target schema is in DBA_FORBIDDEN_SCHEMAS (core/platform/identity) is a violation
    return OK
```
Effect: removes the 131 fabricated reds; only truly dangling FKs raise DBA06.

### 3.2 Query parser — fix PERF4 (was 200 false 🟡)
Only flag queries that can return unbounded **result sets**:
```python
UNBOUNDED_OK = {"first", "one", "scalar", "get", "count", "exists", "all"}  # caller-bounded
if has_limit_or_keyset(node): return OK
if method in {"get","first","scalar","count"}: return OK   # single-row / aggregate
if is_config_or_seed_fetch(node): return OK
return VIOLATION("PERF4")
```

### 3.3 Security parser — fix SEC5/SEC101 (was 30 false 🔴)
Flag only when an **untrusted value** is concatenated into SQL:
```python
if node.is_text_or_raw and not node.has_bound_params:
    if any(arg is request_input or arg is f-string_from_request):
        return VIOLATION("SEC5")
# bound params (text(q, params=...)) => OK
```
Parameterized `text(...)` (e.g. `analytics_service.py`, `controllers/admin/database.py`) → OK.

### 3.4 Frontend parser — fix FEH402 / DS02
- FEH402: flag `key={i}` **only** when the list is dynamic/mutable (mapped from API data), not on
  static loading skeletons (`LoadingSkeleton`).
- DS02: flag inline `<style>` in components (e.g. `hud.tsx`) — real token-policy violation.
- FEH201: flag `console.log` in non-error paths; `console.warn` in error handlers is OK.

---

## 4. Rule catalog (mapped to §10)

| Rule | §10 | What it checks | Severity |
|---|---|---|---|
| CIR1 | 10.2 | import edge outside ALLOWED_EDGES | 🔴 (P0 if upward) |
| DG2 | 10.2 | circular dependency in import graph | 🟡 |
| DOM3 | 10.1/10.2 | file in wrong layer folder (surface vs domain) | 🔴 |
| MV1 / MV2 | 10.2 | mis-housed / wrong-folder module | 🟡 |
| FT1 | 10.2 | surface×domain flow violation | 🟡 |
| RN1 | 10.2 | router prefix ≠ contract | 🟡 (verify) |
| W1 | 10.5 | `db.add/commit` in routers | 🔴 |
| LC1 | 10.5 | forbidden op in layer | 🔴 |
| Q1 | 10.5 | read logic in router (advisory) | 🟡 |
| DBA02 | 10.3 | `create_all` unguarded in prod | 🟡 (verify guard) |
| DBA03 | 10.3 | audit columns/mixin missing | 🟡 |
| DBA06 | 10.3 | dangling FK (FIXED parser) | 🔴 |
| DBA13 | 10.3 | ORM↔migration drift | 🔴 (verify) |
| DBA27 | 10.3 | broken migration file | 🔴 (verify) |
| DBA32 | 10.5 | OFFSET pagination on hot list | 🟡 |
| SEC2 | 10.4 | hardcoded secret | 🟡 (verify) |
| SEC5 / SEC101 | 10.4 | unparameterized SQL (FIXED) | 🔴 |
| API101 | 10.2 | endpoint missing `response_model` | 🟡 |
| PERF4 | 10.5 | unbounded result set (FIXED) | 🟡 |
| SC101 | 10.5 | list endpoint missing pagination | 🟡 |
| HL302 / QUAL1 | 10.5 | swallowed exceptions | 🟡 |
| MET5 | 10.1 | god module (named file) | 🔴 |
| DS02 | 10.7 | inline `<style>` in component | 🔴 |
| FEH402 | 10.7 | index key on dynamic list (FIXED) | 🟡 |
| FEH201 | 10.7 | stray `console` (FIXED) | 🟡 |
| FEH802 | 10.7 | raw `<img>` not next/image | 🟡 |
| FEH301 | 10.7 | missing error boundary | 🟡 |
| PV1 | 10.6 | provider not subclassing base / no `health_check` | 🟡 |
| PV2 | 10.6 | router calls provider directly | 🔴 |
| SCALE1 | 10.8 | missing PgBouncer/ replica/ Redis-cache at scale | 🟡 (warn) |

---

## 5. Finding & report model

```python
@dataclass
class Finding:
    rule_id: str
    severity: str          # "red" | "yellow" | "blue"
    file: str
    line: int
    evidence: str
    contract_clause: str   # e.g. "Architecture_Diagram.md §10.2"
    fix: str
    verified: bool         # True if engine proved it (not heuristic)
```

- **Verified** findings cite exact `file:line` + the violating token.
- **Heuristic** findings (DBA13/DBA27/SEC2/RN1) are marked `verified=False` and must be triaged
  manually before counting toward 🔴 totals.
- Debt score = Σ(weight[severity] × count[rule]); weights exclude unverified heuristics.
- Report leads with **real** high-severity items (W1, DBA32, API101, DS02, PV2), not parser
  artifacts.

---

## 6. Implementation notes

- Build the import graph once (`parsers/import_graph.py`) and reuse for CIR1/DG2/DOM3/MV/FT/RN.
- Load `Base.metadata` to resolve FK schemas (fixes DBA06) and to diff against Alembic (DBA13).
- Run parsers in parallel per file; aggregate into `Finding[]`.
- Emit both `SYSTEM_AUDIT_REPORT.md` and `schema-audit-report.json` (machine-readable).
- The auditor must stay **read-only**; it never edits `scripts/`, source, or the report.

---

## 7. Open items before coding

1. Confirm `Base` metadata import path for FK resolution (currently `db/base.py`).
2. Confirm Alembic vs ORM diff strategy for DBA13 (table inventory compare).
3. Decide `SCALE1` trigger (only when `APP_ENV=production` + high traffic expected).
4. The existing engine (13,488 lines) should be **refactored** to this spec; the four parser
   fixes (§3) are the minimal correctiveness patch if a full rewrite is deferred.
