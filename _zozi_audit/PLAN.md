# ZOZI FORENSIC AUDIT — MASTER PLAN (`_zozi_audit/PLAN.md`)

> **Version 2 (2026-10-02).** Adds the extension dimensions (design/colour,
> interaction robustness, feature & taxonomy, workflow/QA/automation, data
> management), a **recommendation stream**, and **Phase B — the compilation
> step** that turns the audit into an ordered, executable remediation plan.
>
> **Deliverable:** one command — `python _zozi_audit/zozi_audit.py` — that produces
> **ONE consolidated file** `_zozi_audit/zozi_forensic_audit.md` covering all 28
> forensic-audit dimensions, cross-cutting passes, chains, completion blockers and the
> 18-condition production-readiness gate.
>
> **Two artifacts, two purposes — never merge them.**
> `zozi_forensic_audit.md` states *fact* about the repository.
> `zozi_remediation_plan.md` (produced by `zozi_compile.py`) states *intent*: what
> to do, in what order, how to prove it, and what it unblocks. A recommendation
> never becomes a blocker; a blocker never hides inside a recommendation.
>
> **Benchmarks:**
> - `_most_imp_docx/ARCHITECTURE_STACK.md` — 325 laws, modules, domains, package layout, wiring.
> - `_most_imp_docx/TECHNOLOGY_STACK.md` — pinned versions, forbidden packages, env vars.
> - `_most_imp_docx/PROMPT_FORENSIC_AUDIT.md` — dimension schema, finding schema, phases, gates.
> - `_most_imp_docx/FEATURE_STACK_LIST.md` (non-authoritative; used for feature candidate reconciliation only).
> - Prior run: `_audit/**` (compiled rollups; treated as *evidence to re-verify*, never as truth).
>
> **Rules inherited from the prompt:** cite `path:line`; no aggregate rows (`N+`);
> every finding carries the full mandatory schema; never infer behaviour from folder
> names; verify, then classify; contradictions are surfaced, never silently resolved.

---

## 0.1 · What version 2 adds, and why version 1 was not enough

Version 1 audited **code shape**. It had no design/colour axis, no feature- or
route-level coverage axis, no interaction-handling axis, and it emitted no
suggestions. It could tell you a `<button>` lacked a `type` attribute; it could
not tell you that the button swallows its own error, that no test ever clicks it,
or that the product taxonomy cannot hold five tiers.

Five extension scanner modules were added, mapped onto the **existing 28
dimensions** so the benchmark's dimension set is unchanged:

| Module | Dimension | What it now measures |
|---|---|---|
| `s16_design.py` | 14 frontend_web | token layer, colour drift, primitive layer, variant system, dark mode |
| `s17_interactions.py` | 14 frontend_web / 12 tests | buttons, modals/drawers, form labelling, toast channel, per-page loading/empty/error states |
| `s18_feature_matrix.py` | 16 features | feature-gate integrity (undefined/dead), route × test matrix, category hierarchy depth |
| `s19_workflow.py` | 04 operational | Celery runtime, event spine, state-machine centralisation, handover/takeover assurance, QA mechanisms, automation candidates, finance automation surface |
| `s20_db_advisor.py` | 07 tables_fields | table management posture, unindexed hot columns, relationship loading, migration ↔ ORM schema drift |
| `s21_http_layer.py` | 14 frontend_web / 18 security | **live** HTTP response contract (preflight status, header presence/consistency, cookie flags, CSP shape, startup errors) + static header-policy audit |
| `s09_environment.py` (added) | 11 environmental | `settings_contract` — every `settings.<attr>` read resolved against the fields `Settings` declares |

**Registered checks: 59 → 82.** A `Recommendation` model was added with its own
`logs/recommendations.jsonl`, its own report section (§7), and its own
non-gating track in the plan.

### 0.1.1 · Why the HTTP layer and settings contract are the same lesson

Both were found the same way: the audit produced a confident number that no
check had produced. v2 measured **6,604 ruff violations** and **119 TS errors**
without ever issuing an HTTP request, and never resolved a single
`settings.<attr>` read against the declared fields. The two defects that
surfaced only when a real server existed were:

- **CORS preflight returns `405`** — invisible to `curl` and to the in-process
  ASGI client, fatal to every cross-origin write in a browser.
- **`Settings has no attribute 'backup_verify_on_create'`** — invisible because
  no check ever read an attribute that only fails when that path executes. 31 such
  attributes exist, 12 of them P0.

The general rule this produced: **a check that cannot fail on a runtime defect
will not find one.** Static analysis has a ceiling; the probe exists to hit it.

### 0.2 · False-positive discipline (learned the hard way — do not revert)

The version-2 checks were verified by independent sub-agents before being
accepted, and **ten detection rules were wrong on first run.** They are now
enforced in code:

1. **`ctx.rel()` returns forward slashes.** A Windows `\` separator silently
   defeats every `"frontend/web_app/src/" in rel` filter — the check reports zero
   instead of failing loudly.
2. **Filter repo-relative paths without a leading slash:** `"frontend/" in rel`.
3. **Web app only for design metrics.** React Native has no CSS cascade, so
   `style={{…}}` and hex literals under `mobile_app/` are idiomatic. Including
   them inflated inline styles 302 → 1953 and hex literals 165 → 1062.
4. **A hex literal in a brand SVG, chart series or palette file is correct.**
   Excluded by path *and* filename.
5. **`Column(…, index=True)` is an index.** Matching only index *names* in
   `__table_args__` inflated unindexed columns 224 → 871.
6. **Strip comments and docstrings before regexing Python.** A
   `require_feature("…")` inside a comment produced 8 phantom "undefined gates";
   7 survived the filter and match independent verification.
7. **A feature id is dot-separated lowercase snake_case, ≥2 segments, no
   wildcard, no whitespace.** `"x"`, `"foo.*"` and `"domain.action"` are samples.
8. **A capability is implemented only if a definition exists** — require
   `def compute_vat_remittance` or `class VATRemittance`, not the mere mention.
9. **Search for the Celery app recursively.** It is at
   `backend/jobs/celery_app.py`, not `backend/celery_app.py`.
10. **No law requires a `version` column on every table.** It is an
    optimisation, so it is a recommendation, never a defect.

**Rule 11 — an unverified claim is a verification task, not a fix task.** The
compiler refuses to emit "change the code" for any finding whose `claim_state` is
`UNKNOWN`/`INFERRED`/`CONTRADICTED`; those land in wave 4 to be confirmed or
dismissed first. A separate 10-agent verification pass over the original 98 P0
claims found **~40 % noise**, which is the reason this rule exists.

---

## 0 · Objectives

1. **100 % coverage of the auditable surface.** Every Python file in `backend/`
   (excluding generated/vendored dirs), every TS/TSX file in `frontend/`,
   every migration, every workflow, every model, every route, every provider,
   every env var, every test, every doc under `_most_imp_docx/`.
2. **Evidence-based findings.** Each check emits `path:line` + quoted snippet +
   the exact command that re-proves it. Static-only conclusions are labelled
   static; runtime conclusions require a tool run.
3. **One consolidated report** (`zozi_forensic_audit.md`) with the 28 dimension
   sections + rollups. Machine-readable logs alongside (`logs/*.jsonl`) are
   supporting artifacts, not the deliverable.
4. **Optional truth-seeking integrations**, each independently runnable and each
   degrading gracefully when unavailable:
   - **Browser** (`zz_integrations/browser_probe.py`) — Playwright against the
     real stack; consumes `_browser_test/` results if present.
   - **Ollama LLM** (`zz_integrations/ollama_probe.py`) — semantic review of
     hotspots (code-intent, AI drift, stub/TODO reality check).
   - **Live DB** (`zz_integrations/db_probe.py`) — SQLite/Postgres introspection
     for ORM↔DB drift (dimension 07) and RLS/policy verification (dimension 06).
   - **Load probe** (`zz_integrations/load_probe.py`) — optional p95 sampling.
5. **Parallel agent model.** The registry schedules **71 discrete check tasks**
    across a `ThreadPoolExecutor(max_workers=10)` — at most 10 in flight, per the
    operator's instruction; each task is a self-contained "sub-agent" with an
    explicit instruction (docstring + `INSTRUCTIONS` constant) and returns
    findings/observations only.

---

## 1 · Directory layout

```
_zozi_audit/
├── PLAN.md                        # this file — design + inventory + accuracy history
├── zozi_audit.py                  # PHASE A — the audit. -> zozi_forensic_audit.md
├── zozi_verify.py                 # PHASE B — the falsification gate. -> zozi_verification.md
├── zozi_compile.py                # PHASE C — the plan. -> zozi_remediation_plan.md
├── zz_core/
│   ├── __init__.py
│   ├── model.py                   # Finding / Observation / Recommendation / ScanContext / ToolResult / enums
│   ├── constants.py               # canonical laws, version pins, forbidden lists, schema sets, env contract
│   ├── util.py                    # file walking, AST helpers, markdown tables, hashing, snippet extraction
│   ├── tools.py                   # subprocess runner + tool probes (keeps untruncated stdout)
│   ├── registry.py                # check registry, dedupe, id assignment, parallel executor (max 10)
│   ├── logs.py                    # JSONL writer, checkpoint, run metadata, tool ledger
│   └── report.py                  # markdown renderer for the single output file
├── zz_scanners/                   # 82 registered checks + 10 pre-flight
│   ├── __init__.py                # imports all scanner modules -> auto-register
│   ├── preflight.py               # Phase 0 boot smoke + Phase 0.5 pre-flight (10 rows)
│   ├── s01_architecture.py        # dims 01, 17
│   ├── s02_technology.py          # dims 02, 28
│   ├── s03_logic.py               # dims 03, 22, 25 (static detectors)
│   ├── s04_operations.py          # dims 04, 13
│   ├── s05_wiring.py              # dims 05, 20
│   ├── s06_database.py            # dims 06, 07, 10
│   ├── s07_providers.py           # dim 08
│   ├── s08_laws.py                # dim 09 (all 325 laws -> PASS/FAIL/UNVERIFIABLE)
│   ├── s09_environment.py         # dim 11 (incl. settings_contract)
│   ├── s10_tests.py               # dim 12
│   ├── s11_frontend.py            # dims 14, 15, 26
│   ├── s12_features.py            # dims 16, 23 (feature health)
│   ├── s13_security.py            # dim 18
│   ├── s14_performance.py         # dim 19
│   ├── s15_crosscut.py            # dims 21, 24, 27 rollups
│   ├── s16_design.py              # dim 14  — tokens, colour drift, primitives, dark mode
│   ├── s17_interactions.py        # dim 14/12 — buttons, modals, forms, toasts, page states
│   ├── s18_feature_matrix.py      # dim 16  — gate integrity, route×test matrix, category depth
│   ├── s19_workflow.py            # dim 04  — celery runtime, event spine, handover, QA, automation
│   ├── s20_db_advisor.py          # dim 07  — table posture, index drift, schema drift
│   └── s21_http_layer.py          # dim 14/18 — live response contract + static header policy
├── zz_integrations/
│   ├── __init__.py
│   ├── http_probe.py              # live HTTP/1.1 probe (boots uvicorn, inspects real responses)
│   ├── browser_probe.py           # independently runnable Playwright audit
│   ├── ollama_probe.py            # independently runnable local-LLM semantic audit
│   ├── db_probe.py                # independently runnable DB introspection
│   └── load_probe.py              # independently runnable latency sampler
└── logs/                          # run.json, findings/observations/recommendations/verdicts .jsonl,
                                   # facts.json, tool_ledger.json, plan.json, plan_status.json
```

**Pipeline order is load-bearing:**

```
zozi_audit.py  ──► zozi_forensic_audit.md     (facts)
      │
      ▼
zozi_verify.py  ──► zozi_verification.md       (adjudicated claims)   + logs/verdicts.jsonl
      │
      ▼
zozi_compile.py ──► zozi_remediation_plan.md   (ordered, gated work)  + logs/plan.json
```

Running `zozi_compile.py` without `logs/verdicts.jsonl` still works but emits a
loud warning and produces **no fix instructions at all** — every step defaults to
UNVERIFIABLE. That is deliberate: an unverified plan must not look executable.

**Excluded from every walk** (non-negotiable, avoids the `.kilo` worktree trap):
`.git/`, `.kilo/`, `.freebuff/`, `node_modules/`, `__pycache__/`, `.pytest_cache/`,
`.hypothesis/`, `.next/`, `dist/`, `build/`, `venv/`, `.venv/`, `_extra_files/`,
`_legacy.bak/`, `test-results/`, `playwright-report/`, `_zozi_audit/`,
`*.min.js`, `*.map`, binary files. `ctx.rel()` always returns **forward slashes**,
because every scanner matches on `backend/...`-style strings and a Windows `\`
silently defeats those filters.

---

## 2 · Execution pipeline

```
Phase 0    boot smoke test      (preflight.py::boot_smoke)
Phase 0.5  pre-flight checks    (preflight.py::preflight — 10 checks)
Pass 1     inventory/observe    (util.walk + every scanner's observe_*)
Pass 2     diff/classify        (scanner check functions -> Findings)
Rollups    contradictions, anti-patterns, chains, feature health, alignment, mandatory checklist
Gate       27 blockers, 18-condition production readiness
Report     zz_core/report.py -> zozi_forensic_audit.md
Integrate  browser/ollama/db/load results merged when present (clearly labelled)
Update     _most_imp_docx/PRODUCTION_READINESS_CHECKLIST.md with current evidence-based status
```

Parallel execution: each registered check runs as a task in a 10-worker pool.
`--workers N` overrides (cap 10 enforced). `--fast` runs deterministic static
checks only; `--full` (default) also runs tool-backed checks (ruff/pytest/tsc/
alembic/pnpm/playwright/ollama) with per-command timeouts.

Exit codes: `0` report written; `2` fatal precondition (no repo root / no backend);
`3` report written but with pre-flight blockers (still success — audit continues by design).

---

## 3 · Canonical constants (`zz_core/constants.py`)

| Constant | Content / purpose |
|---|---|
| `CANONICAL_MODULES` | `{admin, customer, employee, logistics, supplier}` (Law 13) |
| `CANONICAL_DOMAINS` | 15 domains (Law 12) |
| `APPROVED_EXTRA_SCHEMAS` | `media, treasury, ai, configuration` |
| `FORBIDDEN_SCHEMAS` | `core, platform, identity` |
| `CANONICAL_TOPLEVEL` | allowed entries at `backend/` root |
| `FORBIDDEN_ROOT_DIRS` | `utils, routers, controllers, services, models, db` |
| `CANONICAL_PROVIDER_DIRS` | approved provider subpackages |
| `KNOWN_PROVIDER_EXTRAS` | observed non-canonical providers (news, automation, scanner, voice, analytics) |
| `PY_VERSION_PINS` | parsed from `TECHNOLOGY_STACK.md` table (runtime extraction, with embedded fallback map) |
| `JS_VERSION_PINS` | same, for web/mobile/shared |
| `FORBIDDEN_PY_PACKAGES` | psycopg/psycopg2, python-jose, pytz, tzlocal, python-magic, prometheus-client, paypal-payments-sdk (exact TECH string) |
| `UNAPPROVED_ALTERNATIVES` | slowapi, limits (not chosen; canonical limiter is fastapi-limiter-valkey) |
| `FORBIDDEN_JS_PACKAGES` | `@tanstack/react-query`, `swr`, Pages-Router usage, npm/yarn lockfiles |
| `MIDDLEWARE_ORDER` | canonical 8-layer order (Law 78) |
| `LAWS` | full structured 325-law table loader from `ARCHITECTURE_STACK.md` (parse at runtime; never hardcode drift) |
| `SCHEMA_REQUIRED_COLUMNS` | `created_at, updated_at, country_code, is_deleted` |
| `MONEY_FIELD_HINTS` | regex set: amount, price, total, subtotal, tax, vat, commission, fee, balance, payout, refund, discount, shipping_cost, rate, salary, wage |
| `ENV_CANONICAL` | env vars parsed from `TECHNOLOGY_STACK.md` §20 (name, secret, required, default) |
| `PHASES` | emergency..defer |

Constants are **derived from the benchmark docs at runtime** (parsers in
`s02_technology.py` / `s09_environment.py`) so the audit never goes stale if the
docs change; the embedded fallback is only used when parsing fails.

---

## 4 · Finding & observation schema (`zz_core/model.py`)

```python
@dataclass(slots=True)
class Finding:
    id: str                    # PREFIX-nnn, stable prefix map below
    dimension: str             # "01_architectural" ... "28_supply_chain"
    phase: str                 # emergency|boot|tech|db|logic|arch|security|payment|compliance|frontend|mobile|testing|infra|docs|defer
    status: str = "NEW"        # NEW (this run) — audit never compiles/resolves
    cluster: str = ""          # CLUSTER-<slug>
    file: str = ""             # repo-relative
    line: int = 0
    current: str = ""          # what is there now (quoted evidence)
    target: str = ""           # what should be there (law/doc citation)
    delta: str = ""            # one sentence
    fix: str = ""              # one verb + one target
    effort: str = "S"          # S<=1h | M 1-4h | L >4h
    priority: str = "P2"       # P0..P3 per §6.1 matrix
    confidence: int = 3        # 1..5
    evidence_strength: str = "single"   # single|multiple|triangulated
    truth_level: str = "L0"    # L0|L1|L2|L3
    claim_state: str = "VERIFIED"       # VERIFIED|INFERRED|UNKNOWN|CONTRADICTED
    sibling: str = ""          # same-layer file that does it right
    verify: str = ""           # exact shell command
    test: str = ""             # test path that must exist/pass
    rollback: str = "git revert <commit>"  # or flag|migration|irreversible
    blast_radius: str = ""
    depends_on: str = ""
    blocks: str = ""
    completion_blocker: str = "no"      # yes|partial|no
    laws: tuple[int, ...] = ()          # implicated law numbers
    snippet: str = ""                   # <= 400 chars quoted evidence
    notes: str = ""
    origin: str = "static"              # static|tool|browser|llm|db|prior-audit

@dataclass(slots=True)
class Observation:            # Pass 1 raw observation (drives 06-equivalent appendix)
    scope_type: str           # file|route|table|event|job|page|screen|package|env_var|migration|test|provider|feature|chain|build_step|preflight_check
    scope_id: str
    path: str; line: int
    dimension: str
    truth_level: str
    claim_state: str
    evidence: str
    note: str = ""
    cluster: str = ""

@dataclass
class ToolResult:
    name: str; cmd: str; exit_code: int|None; duration_s: float
    stdout_tail: str; stderr_tail: str; available: bool; skipped_reason: str = ""

@dataclass
class ScanContext:
    root: Path; backend: Path; frontend: Path; out_dir: Path
    py_files: list[Path]; ts_files: list[Path]; docs: list[Path]
    inventory: dict[str, Any]      # lazily-built shared facts (routes, models, tables, features, envs, imports)
    tools: dict[str, ToolResult]   # tool availability + outputs
    options: dict[str, Any]        # flags (fast/full/browser/llm/workers)
    def rel(self, p) -> str        # path relative to root
    def line_of(self, p, needle) -> int
```

**ID prefixes:** ARCH, TECH, LOGIC, OPS, WIRE, DB, TF, PROV, LAW, MIG, ENV,
TEST, D2P, WEB, MOB, FEAT, FILE, SEC, PERF, OBS, CONTRAD, AP, INTENT, BROWSER,
DRIFT, ALIGN, BLOCK, SC (supply chain).

---

## 5 · Function inventory — `zz_core`

### `zz_core/util.py`
| Function | Responsibility |
|---|---|
| `walk_files(root, include, exclude)` | bounded recursive walk, symlink-safe, ignore directories |
| `is_generated(path)` | detect minified/generated/pyc/binary |
| `read_text(path, max_bytes)` | tolerant UTF-8/UTF-16 read, returns `(text, truncated)` |
| `line_of(text, needle, start=0)` | 1-based line for a substring |
| `snippet(text, line, pad=2, width=400)` | quoted evidence window |
| `sha1_file(path)` / `sha1_text(text)` | duplicate detection, drift fingerprints |
| `iter_python(paths)` | yields `(path, text, ast_tree|None, parse_error)` |
| `ast_imports(tree)` | list of `(module, names, lineno, kind)` incl. relative imports |
| `ast_calls(tree, names)` | call-site extraction with line numbers |
| `module_of(path, root)` | canonical dotted module name |
| `is_async_function(node)` / `async_functions(tree)` | async detection |
| `iter_functions(tree)` | `(qualname, node, start, end, depth)` |
| `complexity_of(node)` | branch count approximation |
| `normalized_hash(node)` | AST-normalised body hash (DRY detection) |
| `grep_files(paths, pattern, flags)` | regex scan with line numbers, bounded results |
| `find_endpoints(paths)` | FastAPI decorator extraction (`@router.get/post/...`, `@app.*`) |
| `parse_requirements(path)` | PEP-508 tolerant requirement parser |
| `parse_package_json(path)` | tolerant JSON/JSONC read |
| `parse_yaml_lite(path)` | minimal YAML subset parser (workflows/docker-compose) — no PyYAML dependency |
| `parse_markdown_tables(text)` | benchmark-doc table extraction (versions/env vars/laws) |
| `percentile(values, p)` | load-probe stats |
| `fmt_seconds(s)` / `fmt_bytes(n)` | report formatting |

### `zz_core/tools.py`
| Function | Responsibility |
|---|---|
| `which(cmd)` | executable lookup (PATHEXT-aware on Windows) |
| `run(cmd, cwd, timeout, env)` | subprocess with timeout, capture, truncation, never raises |
| `probe_python()` / `probe_node()` / `probe_pnpm()` / `probe_ruff()` / `probe_pytest()` / `probe_alembic()` / `probe_playwright()` / `probe_ollama()` / `probe_git()` | availability + version |
| `boot_smoke(ctx)` | `python -c "from backend.main import app; print(len(app.routes))"` + adapted `cd backend; python -c "from main import app"` |
| `run_pytest_collect(ctx)` | `pytest --collect-only -q` with timeout, parse errors |
| `run_pytest_architecture(ctx)` | `pytest tests/architecture/` when present |
| `run_ruff(ctx)` | `ruff check . --output-format=concise` (counts parsed) |
| `run_tsc(ctx)` | `pnpm exec tsc --noEmit` (web) |
| `run_next_build(ctx, dry)` | build only in `--full`, parse errors + page count |
| `run_alembic_heads(ctx)` | `alembic heads` + fallback AST parse |
| `run_pnpm_install_check(ctx)` | frozen-lockfile check (offline tolerant) |
| `run_pip_audit(ctx)` / `run_trivy(ctx)` / `run_gitleaks(ctx)` | optional supply-chain tools |
| `run_playwright(ctx, spec)` | optional browser probe handoff |
| `ollama_chat(ctx, prompt, model)` | thin HTTP call to Ollama `/api/chat` (stdlib urllib) |
| `git_info(ctx)` | HEAD sha, branch, dirty count |

### `zz_core/registry.py`
| Function | Responsibility |
|---|---|
| `check(name, dimension, phase, instructions)` | decorator registering a check task |
| `all_checks()` | ordered registry |
| `run_checks(ctx, names=None, workers=10)` | ThreadPoolExecutor, per-check isolation (exceptions -> findings), progress to stderr |
| `CheckResult` | `(findings, observations, tool_results, facts)` |
| `group_by_dimension(results)` | feeds report + JSONL |
| `dedupe(findings)` | stable de-duplication by `(file,line,current,target)` keeping highest confidence |
| `cap_workers(n)` | enforce `1 <= n <= 10` |

### `zz_core/logs.py`
| Function | Responsibility |
|---|---|
| `RunLog` | JSONL per-dimension writers, checkpoint after each phase, `run.json` metadata |
| `write_jsonl(path, rows)` | append-safe |
| `checkpoint(phase, files, findings, next)` | resume state (§0.13 of the prompt) |
| `load_checkpoint()` | resume support for re-runs (statuses stay NEW/DEFERRED only) |

### `zz_core/report.py`
| Function | Responsibility |
|---|---|
| `render(ctx, results)` | build the complete markdown document |
| `render_header` | run metadata, commit, preconditions table, method, coverage |
| `render_exec_summary` | headline numbers + top-20 + completion blockers |
| `render_dimension(result)` | per-dimension: summary, findings table (full 23 columns), observations, problems/solutions/suggestions, corrections-prioritized |
| `render_chains` / `render_contradictions` / `render_anti_patterns` / `render_feature_health` / `render_alignment` / `render_ai_drift` / `render_browser` / `render_supply_chain` | cross-cutting sections |
| `render_readiness` | 18-condition gate with pass/fail/unverifiable + evidence |
| `render_remediation` | P0–P3, phases, clusters, KEEP/HARDEN candidates |
| `render_appendix` | observations sample, tool-run ledger, uncovered areas, self-audit report |
| `write(report_path)` | atomic write (tmp + replace) |

---

## 6 · Function inventory — `zz_scanners` (checks with IDs)

Each scanner module exports `register(reg)`; every check is registered via
    `@check(...)` with an instruction docstring. Counts below: **71 checks**.

### `preflight.py` — Phase 0 / 0.5 (build blockers, ID prefix `BLOCK`)
 1. `boot_smoke` — root import + adapted import; route count; skipped-router detection from stderr; writes `BLOCK-boot-*`.
 2. `preflight_env` — required env vars present in `.env.example` / typed settings; missing default; secret handling.
 3. `preflight_db` — `DATABASE_URL` resolvable + reachable (optional driver), else `unverifiable`.
 4. `preflight_valkey` — URL scheme + ping when driver present.
 5. `preflight_tests` — pytest collection errors parsed per file.
 6. `preflight_tsc` — TypeScript error count + first 20 errors.
 7. `preflight_lint` — ruff error count (top rules) or skip.
 8. `preflight_migrations` — `alembic heads` + AST fallback; head count; verify `alembic.ini` presence at `backend/alembic.ini` (or confirm env.py-based config is used).
 9. `preflight_lockfiles` — uv.lock/pnpm-lock vs requirements/package.json sync.

### `s01_architecture.py` — dims 01 + 17 (ID prefixes `ARCH`, `FILE`)
 10. `extra_modules_and_domains` — 6th module, 17th domains, approved extras, forbidden schemas-dirs.
 11. `root_discipline` — forbidden root dirs/files; temp/debug scripts (`_tmp_*`, `health_test_*`, `fix_*`, `debug_*`); run_tests.*; single canonical runner check.
 12. `import_direction` — full AST import graph; per-law checks (L1, L97–L106): domains→modules, infra→above, kernel isolation, providers purity, middleware scope, jobs scope, rbac scope; cycle detection (L98).
 13. `router_thinness` — router bodies: DB session usage, business-branch count, service-call count, unregistered routers (routers/__init__ lists), decorator-less router files.
 14. `cross_domain_channels` — direct cross-domain imports outside `events/subscribers/ports/read_models`; write bypass; wildcard ports; lazy service locators; allowlist audit (L7) with dated-removal check; `DOMAIN_ALLOWLIST.yaml` parse (must only shrink; entries without removal date are violations).
 15. `domain_structure_completeness` — per-domain required dirs/files (services/models/schemas/policies/events/subscribers/ports/features/read_models).
 16. `module_structure_completeness` — per-module auth/routers/serializers; router categories.
 17. `dead_code_and_duplicates` — unreferenced modules, duplicate file hashes, duplicate function bodies, orphan services/routes; large-file split candidates (>1000 lines).

### `s02_technology.py` — dims 02 + 28 (IDs `TECH`, `SC`)
18. `py_dependency_audit` — parse versions from TECHNOLOGY_STACK vs requirements*.txt/pyproject; per-package mismatch findings; forbidden packages (declared + imported); undeclared imports (`fastapi_limiter_valkey` class of bug); unused declared packages.
19. `js_dependency_audit` — web/mobile/shared package.json vs pins; forbidden JS packages (react-query/SWR); missing canonical packages; lockfile presence/pinning (exact vs caret); npm/yarn artifacts.
20. `runtime_versions` — Python/Node/Postgres/base-image drift (Dockerfiles, compose, CI, nvmrc).
21. `package_manager_policy` — uv vs pip in Docker/CI; pnpm vs npm; packageManager field.
22. `cve_and_licenses` — optional pip-audit/pnpm audit/Trivy parsing; else static advisory table + `unverifiable` notes.
23. `sbom_and_signing` — SBOM tooling in CI, cosign usage, artifact retention.

### `s03_logic.py` — dims 03 + 22 + 25 (IDs `LOGIC`, `AP`, `DRIFT`)
24. `money_type_audit` — AST: `Float` columns, `float()` casts near money terms, `float:` annotations, `round()` on money, Pydantic float money fields, serializer Decimal→float leaks; per-calculation precision/rounding tick-list (commission, tax, discount, totals, FX).
25. `silent_except_audit` — `except` blocks with no log/raise; finance-path escalation to P0; counts per domain.
26. `blocking_io_audit` — `time.sleep`, `requests.*`, `run_until_complete`, sync `open/read`, `subprocess.run` inside `async def`; loop-blocking patterns.
27. `idempotency_audit` — payment/order/refund/webhook handlers lacking Idempotency-Key enforcement; optional vs required key.
28. `transaction_and_state_audit` — autocommit, commit-in-router, multi-write without transaction; refund/cancel state transitions vs declared machines; illegal edges.
29. `magic_numbers_and_lengths` — magic numeric constants in money paths; functions >50 lines; nesting >4; TODO/FIXME without ticket/date (L62).
30. `unbounded_cache_audit` — module-level dict/list caches without TTL/size; `lru_cache(maxsize=None)`.
31. `default_masks_failure` — truthy-string config, defaults that hide misconfiguration (APP_ENV/VALKEY_URL/CELERY_BROKER_URL/FRONTEND_URL class), "not yet wired" strings, `pass`-only handlers, comment/code divergence, stub/NotImplemented counts (AP categories).
32. `duplicate_logic_and_drift` — copy-paste drift via normalized-AST hashes; phantom imports (import targets not resolvable in tree); docstring drift; unused parameters; naming drift; commented-out code blocks.

### `s04_operations.py` — dims 04 + 13 (IDs `OPS`, `D2P`)
33. `jobs_audit` — enumerate jobs/*; celery registration (include/beat schedule), retry/backoff, DLQ, timeouts, concurrency/rate limits, idempotency, orphan jobs.
34. `health_checks_audit` — `/health`, `/health/deps`, `/health/ready` definitions; fail-closed analysis (503 paths); dependency coverage (DB, Valkey, R2, email, payments); readiness flags.
35. `ci_cd_audit` — `.github/workflows/*`: pre-deploy migrations, health gate, rollback workflow, environment promotion, secret scanning, dependency scanning, artifact/cache config, permissions block (dim 28 overlap), pre-commit hooks (ruff/mypy/import-linter/arch tests).
36. `deployment_assets_audit` — Dockerfiles (multi-stage, base, non-root user, healthcheck), compose (services, limits, restart policies), Caddyfile, Makefile, runbooks under docs/, SETUP.md, rollback.
37. `feature_flags_and_config_profiles` — typed flags via pydantic-settings; env-specific profiles; raw os.getenv in providers/jobs; flag defaults that disable security (rate-limit/captcha).

### `s05_wiring.py` — dims 05 + 20 (IDs `WIRE`, `OBS`)
38. `middleware_pipeline_audit` — orchestrator order vs canonical 8 layers; duplicates/missing; registration of CSRF/security headers/rate-limit/device binding.
39. `auth_ws_audit` — every websocket route: JWT decode + expected_type + role checks; unauth broadcast patterns.
40. `feature_gate_coverage` — every non-public route: `get_current_user`/`require_*` presence; gates whose literal not in catalog (L4); public router classification.
41. `rls_wiring_audit` — `set_rls_context` body (SET LOCAL vs ContextVar); `current_setting` variable names vs middleware; double implementation; session-level SET forbidden.
42. `event_bus_audit` — publishers/subscribers: which events defined, which published, post-commit usage, consumer-group registration, DLQ, retry/backoff, sync-in-transaction, stub subscribers (count per domain).
43. `resilience_audit` — circuit breakers (pybreaker/registry), retries 1-2-4-8+jitter, timeouts on outbound, graceful degradation, bulkheads/semaphores.
44. `observability_audit` — structlog usage vs print, request-id propagation, metrics endpoint/instrumentator, error tracker DSN, tracing setup, PII in log statements, log retention enforcement, alert rules/monitoring assets.

### `s06_database.py` — dims 06 + 07 + 10 (IDs `DB`, `TF`, `MIG`)
 45. `engine_and_pool_audit` — pool_size/max_overflow/recycle/statement timeout vs L47; asyncpg `statement_cache_size=0`; read-replica wiring (`get_read_db` usage); replica URL.
 46. `orm_table_audit` — every model: `__tablename__`, schema declaration, forbidden schemas, required columns, naming lint, money Numeric-only, `country_code` String(2), FK ondelete, FK indexes, soft-delete, server-default timestamps, duplicate table names (L51), missing `__table_args__`.
 47. `live_db_drift` — optional DB probe: ORM vs actual tables/columns (missing tables, orphan columns, unmapped tables); SQLite local files or Postgres DSN.
 48. `n_plus_1_and_queries` — relationship() lacking lazy=selectin/joined; `text("SELECT *")`; `ilike('%…%')` search; OFFSET on hot lists; missing indexes on FK columns.
 49. `migration_history_audit` — AST parse every version: revision/down_revision graph; heads; cycles; orphan parents; duplicate revision ids; destructive ops; expand-contract; downgrade presence; `migration_helpers`-style phantom imports; DSN directness (MIG-).
 50. `rls_policy_sql_audit` — policies SQL files: per-table coverage, variable names, `WITH CHECK`, FORCE RLS; policy↔table match.
 51. `create_all_audit` — verify `create_all` is dev-only and not used in production migrations (Law 6/A-22); if present in production code, flag as `unverifiable` fallback.

### `s07_providers.py` — dim 08 (ID `PROV`)
51. `provider_inventory` — enumerate providers/*; category; docstring intent; HAS_ flags; `health_check()`; `async_workers` usage; secrets source; timeouts; retries; circuit breaker; error mapping; test presence; caller services mapping; provider↔domain matrix; missing health/no-timeout/no-retry counts.

### `s08_laws.py` — dim 09 (ID `LAW`)
52. `law_parser` — parse all 325 laws from `ARCHITECTURE_STACK.md` §12 into structured rows (id, category, rule, description, why).
53. `law_checker_engine` — map statically checkable laws to executable predicates (import graph, file placement, naming, schema, security regex, etc.); emit per-law PASS / FAIL / UNVERIFIABLE + evidence; CI/test presence per law (test file mapping, workflow step); exemptions documented?
54. `law_test_presence` — architecture test files (`test_import_laws.py`, `test_feature_catalog.py`, `test_schema_discipline.py`, `test_model_relocation.py`, gates) exist and collect.

### `s09_environment.py` — dim 11 (ID `ENV`)
55. `env_var_inventory` — every `os.getenv`/`os.environ`/Settings field: path:line, typed?, documented in TECHNOLOGY_STACK, in `.env.example`, default, secret, deprecated aliases (REDIS_URL/S3_*/ENCRYPTION_KEY), prod-required present; drift both directions; `.env` committed check.
56. `country_config_audit` — country-specific tax/commission/gateway/logistics/legal config; DEFAULT_COUNTRY drift; locale env vars.

### `s10_tests.py` — dim 12 (ID `TEST`)
57. `test_inventory_audit` — per test file: type (unit/integration/arch/e2e), imports resolvable, collected?, assertions, skips/xfails, external SDK mocks (respx/monkeypatch), flake risk, isolation (transactions), orphan tests, per-domain smoke presence, coverage per dimension (money/security/browser), test-to-fix pairing candidates.
58. `architecture_test_audit` — forbidden-import tests, feature catalog test, schema discipline test, model-relocation test, Law 70 mapping.

### `s11_frontend.py` — dims 14 + 15 + 26 (IDs `WEB`, `MOB`, `ALIGN`)
59. `web_route_tree_audit` — pages/layouts/loading/error per route; client vs server; dynamic imports; orphan pages; duplicate route trees (`logistics-partner` vs `-partners`); rewrites (`/hr/*`) vs backend presence.
60. `web_component_a11y_audit` — modals (aria-modal/role/focus trap/escape/backdrop), buttons (aria-label/loading/disabled/touch target), forms (RHF+Zod, error display, success), images (`next/image`, AVIF, blur), videos (lazy/poster), any-types/console.log/TODO.
61. `web_api_alignment` — frontend API call sites vs backend routes (method+path normalization), orphan calls, orphan routes, permission strings vs catalog, error-shape and pagination-shape alignment.
62. `mobile_audit` — Expo config/router groups, OTA (`expo-updates`, manifest ENABLED), secure storage usage, offline handling, push config, native permissions/rationale, payment strategy, dynamic requires of undeclared SDKs, Detox specs, parity with web (screens/stores/api client).

### `s12_features.py` — dims 16 + 23 (IDs `FEAT`, `INTENT`)
 63. `feature_catalog_audit` — parse `domains/*/features.py` FEATURES dicts; orphans (defined-not-gated) and ghosts (gated-not-defined); per-module/domain/actor grouping; launch-critical tagging; feature tests presence; feature health score (10-component formula) — outcome/invariant/error/security/tests/browser/P0/P1/contradiction/drift signals.
 64. `feature_stack_list_diff` — reconcile `FEATURE_STACK_LIST.md` against `domains/*/features.py`, registered routes, and tests; flag ~330 features enumerated in the list that lack a matching service/test (FEAT-001..040 class).
 65. `code_intent_audit` — intent-vs-behaviour heuristics (docstring/name vs body): stub bodies behind live routes, handlers that log-only, "not yet wired" responses, TODO-only services, empty `__init__`, docstring promises without implementation; feeds LLM review queue.

### `s13_security.py` — dim 18 (ID `SEC`)
65. `security_static_audit` — OWASP A01–A10 checks: hardcoded secrets regexes, JWT type claim, CSRF active, headers, rate-limit fail-closed, password 72-byte, field-encryption coverage (EncryptedString on secret columns), SQL injection (f-string into text()/execute), SSRF (outbound URL validation), auth/access control gaps, logging failures, PII masking, MFA enforcement, CAPTCHA fail-open, WORM mutation, CORS/debug/cookies, payment credential storage, webhook signature verification, PCI-DSS minimization, GDPR/retention/key-rotation presence.
66. `security_config_audit` — prod-only flags, insecure defaults, secret files tracked in git, `.env` exposure, gitleaks allowlist.

### `s14_performance.py` — dim 19 (ID `PERF`)
67. `static_performance_audit` — N+1, OFFSET, full scans, missing indexes, cache usage/TTL/invalidation, CDN/image config, bundle config, blocking IO, pool sizing, pagination shape on list endpoints; runtime load probe handoff (p95) when available.

### `s15_crosscut.py` — dims 21 + 24 + 27 (IDs `CONTRAD`, `BROWSER`, `BLOCK`)
 68. `contradiction_harvest` — systematic doc-vs-code comparisons across 11 categories (code_vs_migration, code_vs_config, target_vs_code, tech_target_vs_lockfile, api_contract_vs_implementation, frontend_vs_backend, doc_vs_code, package_vs_import, feature_flag_vs_gate, browser_vs_static, mobile_vs_web); each with Source A/Source B; user-decision flag; severity.
 69. `chain_audit` — 7 minimum chains (order placement, payout, return/refund, logistics pickup→delivery, admin ledger→reconciliation, customer registration/KYC, supplier onboarding/listing) plus discovered chains: entry point, happy path, failure paths, rollback, event flow, tests; verdict COMPLETE/PARTIAL/BROKEN/MISSING; project-critical flag.
 70. `browser_bridge` — split into two outputs: `browser_dim24_historical` (from `_browser_test/BROWSER_TEST_LOG.md` + `COVERAGE_GAPS.md`) and `browser_dim24_fresh` (from `browser_probe` if enabled). If `_browser_test/` is absent, write `phase_precondition_unmet — browser_audit_absent` in dimension 24 and do NOT invent findings. Mark `claim_state=VERIFIED` only for the historical set; fresh findings are `claim_state=INFERRED`.
 71. `blocker_rollup` — consolidate every `completion_blocker ∈ {yes,partial}`; dependency ordering; pre-flight/boot/security/payment/compliance/test/infra groupings; readiness-condition feed.
 72. `mandatory_checklist_audit` — verify every item in `PROMPT_FORENSIC_AUDIT.md` §10.5 checklist has at least one finding or `compliant` observation; emit one finding per unchecked box with `project_completion_blocker=yes`.

---

## 7 · Integrations

### `zz_integrations/http_probe.py` — the live HTTP layer (v3)

**Why it exists.** Until v3 the audit had **no HTTP dimension at all**: every check
was static, CLI-based, or in-process ASGI, so nothing ever looked at a real
response. A CORS preflight answering `405` — which breaks every cross-origin
write in a browser while looking perfectly healthy to curl and `TestClient` — was
invisible to the entire suite.

- Boots `main:app` under a real uvicorn on a free port, waits for a **successful
  HTTP exchange** (not a log line), probes, then terminates the child and drains
  its output to `logs/http_probe.log`.
- Speaks HTTP/1.1 over a raw socket via `http.client`, deliberately: a client
  library would normalise or reject a malformed response before the audit sees it.
- Issues only `GET`, `OPTIONS` and `HEAD` — it never mutates data.
- Emits 12 checks: `HTTP-HEADERS` (presence + consistency across a real route and
  an unknown route), `HTTP-CORS-PREFLIGHT` (status **and** headers),
  `HTTP-CORS-ORIGIN` (no `*` with credentials), `HTTP-COOKIE-FLAGS`,
  `HTTP-CSP-SHAPE` (directive names, localhost leakage, deprecated directives).
- Parses the child's stdout for `level=error` records and reports each as a
  `HTTP-startup-error` finding with the `AttributeError` name and the
  `file:line` from the deepest traceback frame. A subsystem that fails at startup
  and logs "non-critical" is otherwise invisible.
- `timeout` defaults to 900 s: a 300 s default produced a false "unavailable"
  verdict while the 10-worker sweep was competing for the same machine.

### `zz_integrations/browser_probe.py` (independently runnable)
- CLI: `python -m zz_integrations.browser_probe --base-url http://localhost:3000 --api-url http://localhost:8000 --specs all --out browser_results.json`.
- Detects Playwright (`npx playwright --version`), reuses `_browser_test` config when present; runs preflight/auth/money-path/security-path specs; captures screenshots on failure; records console/network errors; emits per-step `browser_step` observations; coverage-gap list.
- Degrades to "skipped: playwright/stack unavailable" — never fails the main audit.
- Main audit merges its `browser_results.json` into dimension 24.

### `zz_integrations/ollama_probe.py` (independently runnable)
- CLI: `python -m zz_integrations.ollama_probe --url http://localhost:11434 --model phi3:mini --limit 40 --out llm_results.json`.
- Selects hotspots deterministically: top-N largest/stubbiest/highest-risk files (payment, money, auth, RLS, events) + intent samples.
- Prompts demand strict JSON: `{verdict, intent, actual, drift, completion_impact, evidence_lines, confidence}`; temperature 0; retries; per-file cache; results merged as `origin=llm`, `truth_level=L2`, `claim_state=INFERRED` and clearly labelled in the report.
- Never fabricates: unreachable Ollama = skip note.

### `zz_integrations/db_probe.py`
- CLI: `python -m zz_integrations.db_probe --dsn "$DATABASE_URL" --sqlite zozi.db`.
- Introspects `information_schema` (Postgres) or `sqlite_master` (SQLite): tables per schema, columns/types, PK/FK/index/RLS status; diffs against ORM inventory; produces `db_drift.json` merged into dims 06/07.
- Also verifies payment-credential column types and RLS policy presence.

### `zz_integrations/load_probe.py`
- CLI: `python -m zz_integrations.load_probe --url http://localhost:8000 --paths /health,/rbac/catalog --rps 5 --seconds 20`.
- Measures p50/p95/p99, error rate; feeds dimension 19 condition 11 (`p95 < 500 ms`); skipped without a live server.

---

## 8 · Report layout (`zozi_forensic_audit.md`)

1. **Header + verdict + preconditions** (boot smoke, DB, Valkey, tests, builds, browser, LLM, DB probe).
2. **Headline numbers** (files inspected, findings, P0–P3, blockers yes/partial/no, clusters, contradictions, anti-patterns, drift, alignment, coverage %, effort, **recommendation count**).
3. **Completion blockers** (all yes-first).
4. **Top 20 findings** + **top 10 clusters**.
5. **Dimensions 01–28** — each: Summary block, Findings table (23 mandatory columns), Observations, Problems/Solutions/Suggestions, Corrections-required (prioritized table). A dimension with observations but no findings renders **"NOT VERIFIED"**, never a clean PASS; a dimension that produced neither renders **"NO EVIDENCE"**.
6. **Cross-cutting:** Contradictions (with Source A/B and user-decision flags, **also emitted as dimension-21 findings**), Anti-patterns, Chains (7+ with step evidence), Feature health, Code intent, AI drift, Code alignment, Browser behavior (consumes `_browser_test/`; a Playwright run that collected **zero** tests is a P0 finding, not a PASS), Supply chain, Mandatory checklist audit.
7. **Production readiness** — 18 conditions, pass/fail/unverifiable + evidence + unverifiable explanations.
8. **Design, interaction, taxonomy, workflow & data measurements (§8)** — every number measured in-run, grouped by area. This is the section that answers "what does the UI look like, what can the user click, what is tested, how deep is the taxonomy, what waits for a human, what is automated".
9. **Recommendations & automation opportunities (§7)** — grouped by area, each with why-now / current state / proposal / benefit / effort / prerequisites / evidence. Explicitly labelled **not** completion blockers.
10. **Remediation index** — clusters, KEEP/HARDEN candidates, dependency graph, effort totals.
11. **Appendix A:** tool-run ledger (cmd, exit, duration, tail — head **and** tail kept, because a summary line lives at the end).
12. **Appendix B:** coverage map & exclusions; what could not be verified and why.
13. **Appendix C:** auditor self-check — each check's run status, files touched, findings produced.

---

## 8.5 · Phase B — the compilation step (`zozi_compile.py`)

```
python _zozi_audit/zozi_audit.py     # → zozi_forensic_audit.md   (fact)
python _zozi_audit/zozi_compile.py   # → zozi_remediation_plan.md (intent)
```

The audit alone leaves the reader with 1,800 findings and no order. The compiler
turns them into a plan an agent or a person can follow.

**Inputs:** `logs/findings.jsonl`, `logs/recommendations.jsonl`, `logs/facts.json`,
`logs/run.json`. **Outputs:** `zozi_remediation_plan.md` and `logs/plan.json`.

**Classification rules**

| Step kind | When | Wave |
|---|---|---|
| `gate` | the check is in a gate cluster (boot, test-collection, migrations, lockfile) **or** a pre-flight row is FAIL | 0 |
| `fix` | `truth_level=L0` **and** `claim_state ∉ {UNKNOWN, INFERRED, CONTRADICTED}` | 1–3 |
| `verify` | any untrusted claim | 4 |
| `improve` | sourced from a recommendation; never release-gating | 5 |

Waves 1–3 are then split by priority: `completion_blocker=yes` or `P0` → 1,
`P1` → 2, `P2`/`P3` → 3.

**Work packages.** A flat list of 1,800 steps is not a plan. Steps are grouped by
cluster; a cluster with more than 25 steps is split by its dominant file. Each
package reports: step count, files touched, blocker count, verification count,
estimated hours, and a one-line focus. Packages are the unit of assignment.

**Waves**

| Wave | Title | Why it is there |
|---|---|---|
| 0 | Restore the ability to verify anything | A static audit on a project that does not boot, does not migrate, or does not collect its tests produces numbers without meaning |
| 1 | Hard blockers preventing correct behaviour | |
| 2 | Correctness and security defects | |
| 3 | Coverage, quality and performance defects | |
| 4 | Verification of untrusted claims | Never instruct a code change on a hunch |
| 5 | Improvement track | Recommendations, non-gating, ordered by workload removed |

**Every step carries** `id`, `kind`, `wave`, `fix`, `verify`, `rollback`, `effort`,
`priority`, `files`, `depends_on`, `truth_level`, `claim_state`. A step that
cannot be verified is a wish, not a step.

**Progress round-trip:** `--status <ID>=in_progress|done|dismissed` writes
`logs/plan_status.json`; the next compile renders the recorded state. Step ids
are derived from stable strings (never `hash()`, which varies with
`PYTHONHASHSEED`).

**Other modes:** `--list` (ids and titles), `--check <cluster-substring>` (every
step for one cluster, with do/verify), `--wave N` (one wave), `--json` (machine).

**Measurement gaps are stated explicitly** at the end of the plan: runtime
behaviour, load/latency, third-party gateway sandboxes, mobile runtime and
LLM-intent agreement are *not* closable by a static plan, and silence about them
must not be read as a pass.

---

## 9 · Accuracy strategy — the falsification gate (`zozi_verify.py`)

**The problem this solves.** The audit makes *claims*. Nothing in the pipeline
tries to prove them wrong. This project measured the cost of that gap in its own
data: the prior run adjudicated 1,359 findings and found

| Verdict | Count | Share |
|---|---|---|
| REAL | 910 | 66.9% |
| ALREADY_FIXED | 265 | 19.5% |
| FALSE_POSITIVE | 160 | 11.8% |
| BLOCKED_BY_CONTRADICTION | 23 | 1.7% |

**31% of what a raw audit emits is not actionable as stated.** A remediation plan
that inherits that noise cannot be followed by an AI without re-deriving every
step. `zozi_verify.py` is the missing phase between audit and plan.

### Method — refutation-first, not confirmation-first

| Basis | Rule | May conclude |
|---|---|---|
| `cluster_recheck` | A **second, independent implementation** of the same question, written against a different mechanism (AST vs regex; declared-field set vs mention scan; live wire bytes vs source text) | `CONFIRMED` or `FALSE_POSITIVE` |
| `token_consistency` | Compares the claim's tokens with the cited line / file / directory tree | **Refutation only.** `ALREADY_FIXED`, `WRONG_LOCATION`, `UNVERIFIABLE` — **never** `CONFIRMED` |

Re-checks are implemented for the clusters that carry the P0 mass:
`CLUSTER-float-money` (AST; a rate/score/ratio is explicitly not money),
`CLUSTER-idempotency` (AST annotation + prose detection),
`CLUSTER-tf-rel-lazy` (AST keyword presence),
`CLUSTER-settings-contract` (re-parse `Settings` today),
`CLUSTER-env-undeclared` (`.env.example` + `config.py` today),
`CLUSTER-http-cors` (does the OPTIONS branch now return without `call_next`),
`CLUSTER-http-headers` (is `X-XSS-Protection` still emitted),
`CLUSTER-db-schema-drift` (does the schema appear in ORM metadata today).

### The three rules that keep the gate itself honest

1. **A line drift is not a refutation.** If the cited line carries none of the
   claim's tokens but the tokens exist elsewhere in the file, the verdict is
   `UNVERIFIABLE` with the drift flagged — not `WRONG_LOCATION`. Token matching
   on prose cannot prove a finding wrong; claiming so would reproduce the very
   false-positive class this project keeps fighting.
2. **A directory is not a missing file.** Cluster-level findings legitimately
   cite a directory (`backend/modules/finance`). Those are adjudicated by scanning
   the tree. Reporting them as `WRONG_LOCATION` produced 311 spurious
   mislocations on the first run of the gate.
3. **Absence may be the claim.** When a finding asserts that something is missing
   and the path is absent, that is *consistent*, so it is `UNVERIFIABLE` with an
   explicit note, never `WRONG_LOCATION`.

### Compiler gating — the gate is not decorative

`zozi_compile.py` reads `logs/verdicts.jsonl` and:

- **drops** any finding adjudicated `FALSE_POSITIVE` or `ALREADY_FIXED` from
  every wave, and lists it in a **Rejected findings** appendix with its
  counter-evidence, so the exclusion is auditable rather than silent;
- **downgrades** anything not `CONFIRMED` to a `verify` step in **wave 4**,
  regardless of the priority the audit assigned it;
- **emits a `fix` step only for a `CONFIRMED` verdict**;
- prints a loud gate banner, and a warning when `verdicts.jsonl` is absent.

### Current measured state

| Metric | Value |
|---|---|
| Findings adjudicated | 1,695 |
| Independently confirmed | 235 (13.9%) |
| False positives + wrong locations | 6.1% |
| Not actionable as stated | 8.9% |
| P0 noise | 6.3% |
| Confirmed fix steps in the plan | 235 |
| Verification tasks (wave 4) | 1,390 |

**A 13.9% confirmed share is the honest result, not a defect.** Most clusters
have no independent re-check, so the default verdict is UNVERIFIABLE rather than
a guess. The consequence is stated plainly: **the current plan is not safe to
execute blindly.** Wave 1–3 is small (235 steps); the rest must be adjudicated
cluster by cluster before an AI is pointed at it.

### Scaling the gate (the work still to do)

| Priority | Clusters | Why |
|---|---|---|
| 1 | `float-money` (35 P0), `settings-contract` (12 P0), `silent-except` (219), `tf-rel-lazy` (174), `module-imports-infrastructure` (156) | highest P0 and volume density |
| 2 | `router-db-access` (96), `cross-domain-direct` (92), `tf-timestamp-default` (79), `long-function` (60) | volume; each needs an AST re-check, not tokens |
| 3 | everything else | one-line fallback is honest but not confirming |

Target: `confirmed_pct` above 60% **before** wave 2 is released for autonomous
execution. Until then the plan's own gate banner is the instruction.

### Older rules retained from v2

1. **Two-source rule:** a finding needs (a) two independent static signals, or
   (b) one static signal + one tool run, or (c) it is downgraded to
   `claim_state=INFERRED` / `evidence_strength=single` and capped at P1 unless
   money/security.
2. **Line-number truth:** every `file:line` comes from the scanner at scan time
   from a single AST snapshot per file, via `ast.get_source_segment()` +
   `node.lineno`. Line numbers are never re-read from a second file open.
3. **Prior-audit reconciliation:** key is
   `(dimension, finding_prefix, normalized(file_basename), semantic_snippet_hash)`.

1. **Two-source rule:** a finding needs either (a) two independent static signals, or
    (b) one static signal + one tool run, or (c) it is downgraded to
    `claim_state=INFERRED` / `evidence_strength=single` and capped at P1 unless
    money/security (per §6.3).
2. **Line-number truth:** every `file:line` is produced by the scanner at scan
    time from a single AST snapshot per file, using `ast.get_source_segment()` +
    `node.lineno` from the cached tree. Line numbers are never re-read from a
    second file open, which can race under a worker pool.
3. **Allowlist file:** `zz_core/allowlist.yaml` (dated expiry per entry) lists
   test-context exceptions (e.g., `float` in tests); any other false-positive
   control requires an explicit dated entry.
4. **False-positive controls:** generated/vendored exclusions; test-context
   allowance via the allowlist; syntax-error files reported as parse failures,
   not as findings about their content.
5. **Baseline comparison:** the prior `_audit/**` corpus is parsed and each known
   finding class is explicitly re-tested; the report carries a prior-audit
   reconciliation column (`confirmed` / `fixed` / `not-found` / `changed`) so we
   never regress to trusting old numbers.
6. **Self-audit appendix:** each check reports its run status, files touched and
   findings produced in Appendix C, so a check that silently returned nothing is
   visible rather than indistinguishable from a clean dimension.

---

## 9.5 · Measured accuracy history — every correction, recorded

Kept because it is the evidence for §9. Each row is a real measurement, not an
estimate. Every one of these was a defect in the audit's own detection logic.

| Pass | Measurement | Before | After | Cause of the error |
|---|---|---|---|---|
| v2 ext. | `inline_style_props` | 1,953 | **302** | React Native has no CSS cascade, so mobile `style={{}}` was counted as web drift |
| v2 ext. | `unindexed_hot_columns` | 871 | **224** | `Column(..., index=True)` is an index but produces no name in `__table_args__` |
| v2 ext. | `hardcoded_hex` | 1,062 | **165** | mobile RN literals plus brand SVG / chart palette files, where a literal is correct |
| v2 ext. | undefined feature gates | 15 | **7** | `require_feature` matched inside comments and docstrings |
| v2 ext. | celery app | "does not exist" | **found** | searched `backend/` root; it lives at `backend/jobs/celery_app.py` |
| v2 ext. | toast ratio | 133 success / 15 error | **187 / 780** | counted the words anywhere instead of the `addToast()` call shape |
| v2 ext. | missing `version` column | 178 "defects" | **0 defects** | no law requires it; demoted to a recommendation |
| v3 | TS errors | 0 (next to a FAIL) | **119 in 29 files** | `pnpm exec` ran the supply-chain hook instead of tsc |
| v3 | TS errors (truncation) | 25 | **119** | counts parsed from an elided `stdout_tail` |
| v3 | arch test summary | `Press Ctrl-Break to quit` | **INCOMPLETE** | the run is killed before pytest prints a summary |
| v3 | `missing_from_middleware` | 4 "missing" | **0** | headers are applied from a dict in a loop; literal matching cannot see it |
| v3 | CSP directive gap | "missing" | **none** | broken regex; `object-src`/`base-uri` are present |
| v3 | CORS attribution | `webhook_verification.py` | **`security_headers.py:78`** | stale duplicate assignment overwrote the correct value |
| v3 gate | `WRONG_LOCATION` | 340 | **79** | directories were treated as missing files, and a line drift was claimed as a refutation |
| v3 gate | gate verdicts | — | **1,695 adjudicated** | first run of `zozi_verify.py` |

Rule of thumb this produced: **whenever a count is surprising, re-derive it with
a different mechanism before believing it.** Every "after" figure above was
produced that way.

---

## 10 · CLI contract

```
python _zozi_audit/zozi_audit.py [--root .] [--out _zozi_audit/zozi_forensic_audit.md]
    [--workers 10] [--fast|--full] [--no-tools]
    [--browser] [--browser-base URL] [--llm] [--ollama-url URL] [--ollama-model M]
    [--db] [--dsn DSN] [--load] [--load-url URL]
    [--dimensions 01,02,...] [--resume] [--jsonl]
    [--include-zones node_modules,.kilo]  (default exclusions always apply)

python _zozi_audit/zozi_verify.py [--root .] [--logs _zozi_audit/logs]
    [--out _zozi_audit/zozi_verification.md] [--cluster CLUSTER-...]
    [--limit N] [--strict]

python _zozi_audit/zozi_compile.py [--root .] [--logs _zozi_audit/logs]
    [--out _zozi_audit/zozi_remediation_plan.md] [--json plan.json]
    [--wave N] [--list] [--check CLUSTER-...]
    [--status ID=pending|in_progress|done|dismissed]
```

- `--fast` skips subprocess tools (ruff/pytest/tsc/next/alembic/pnpm) and integrations.
- `--full` (default) runs everything available, each with timeouts and `ToolResult` ledger entries.
- Failures of optional integrations never abort the run.
- `--http-timeout N` on `zozi_audit.py` bounds the live probe (default 900 s).
- **The three phases are ordered and dependent.** `zozi_verify.py` reads
  `logs/findings.jsonl`; `zozi_compile.py` reads `logs/findings.jsonl` **and**
  `logs/verdicts.jsonl`. Compiling without verifying produces a plan with zero
  fix instructions and an explicit warning — that is the intended failure mode,
  not a bug.
- `zozi_verify.py --strict` exits non-zero when the false-positive rate exceeds
  20%, which makes "is this plan safe to execute" a CI-checkable question.
- Re-run behaviour: existing `_zozi_audit/logs/checkpoint.json` is read; statuses remain `NEW`
  unless `--resume` with a prior report, in which case prior findings are marked
  `COMPILED`/`RESOLVED`/`DEFERRED`/`INVALID` per rules and never silently dropped.
- Stale-log control: `check_errors.json` is **deleted** at the start of every run,
  because a previous run's error file otherwise reads as this run's result.

---

## 11 · Step-by-step execution plan (this project) — as built

| Step | Work | Status gate | Done |
|---|---|---|---|
| P1 | Write this plan file | ✅ | ✅ |
| P2 | Verify plan assumptions against the codebase with targeted greps/AST probes | before implementation | ✅ |
| P3 | Implement `zz_core` | syntax + import | ✅ (rebuilt; three files were truncated and had to be reconstructed) |
| P4 | Implement `preflight.py` + `s01`–`s15` | `--fast --dimensions 01` smoke | ✅ |
| P5 | Extension modules `s16`–`s21` + `http_probe` + `settings_contract` | `--fast` run, 0 crashed checks | ✅ |
| P6 | Run `--full`, reconcile every P0/P1 against source, kill false positives | accuracy pass #1 | ✅ (2 verification rounds, 10 wrong rules found and fixed) |
| P7 | Compare against `_audit/**` prior findings | accuracy pass #2 | ✅ (prior run measured 31% not-actionable — see §9) |
| P8 | **Build the falsification gate `zozi_verify.py`** | 1,695 findings adjudicated | ✅ |
| P9 | **Gate the compiler on verdicts** | rejected findings excluded; no fix step without CONFIRMED | ✅ |
| P10 | Keep `confirmed_pct` above 60% so waves 2–3 are safe for autonomous execution | gate banner turns green | **❌ outstanding — currently 13.9%** |

**The single outstanding gate is P10, and it is the answer to "can an AI follow
this plan".** Right now it can follow wave 0 and the 235 confirmed steps. The
other 1,390 steps are verification tasks, and that is stated in the plan itself
rather than hidden.

### Scaling P10 — the work that actually raises accuracy

Each cluster needs a *second implementation* (see §9). In priority order:

| Cluster | Findings | Re-check mechanism to implement |
|---|---|---|
| `CLUSTER-silent-except` | 219 | AST: `ExceptHandler` whose body is only `pass`/`continue`/`...`; exclude `except NotImplementedError` in ABCs and pytest `raises` blocks |
| `CLUSTER-tf-rel-lazy` | 174 | already implemented — extend to count inheritance from the declarative base |
| `CLUSTER-module-imports-infrastructure` | 156 | AST import graph: `modules/*` importing `infrastructure.*`; exclude module-local infrastructure |
| `CLUSTER-tf-timestamp-default` | 79 | AST: `Column(DateTime, default=datetime.now)` vs `server_default=text("now()")` |
| `CLUSTER-long-function` | 60 | AST: branch complexity; exclude generated and test files (already partly done) |
| `CLUSTER-router-db-access` | 96 | AST: `db.` / `session.` inside `backend/**/routers/**` |
| `CLUSTER-cross-domain-direct` | 92 | AST cross-domain import graph vs `DOMAIN_ALLOWLIST.yaml` |
| `CLUSTER-float-money` | 171 | already implemented |

---

## 12 · Explicit non-goals / honesty constraints

- The audit **does not resolve** findings and the compiler **does not edit
  source**. A plan is not a fix.
- The audit **never modifies source files** — only `_zozi_audit/**` and
    `_most_imp_docx/PRODUCTION_READINESS_CHECKLIST.md` (the latter is updated
    after each forensic audit completion with current evidence-based status
    for all checks, per `PROMPT_FORENSIC_AUDIT.md` completion criterion 26).
- The audit **cannot prove** runtime behaviour without a live stack; every such
  condition is marked `unverifiable` with the exact command that *would* verify it.
- The live HTTP probe **never mutates data** — GET, OPTIONS and HEAD only.
- LLM findings are labelled `L2/INFERRED` and can never be promoted to L0.
- No aggregate placeholders (`N+`, `~40`) anywhere; every count is produced by
  listing the underlying records.
- **A `CONFIRMED` verdict proves the claim, not the proposed fix.** Law, schema
  and security fixes still require engineering review before anyone edits code.
- **The verification gate is not a substitute for a reviewer.** At 13.9% confirmed
  it is a brake, not a green light. Its value today is that it prevents the plan
  from silently inheriting unmeasured noise.
