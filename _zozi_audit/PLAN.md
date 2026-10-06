# ZOZI FORENSIC AUDIT — MASTER PLAN (`_zozi_audit/PLAN.md`)

> **Amendment v4.1 (2026-10-06) — read this first.** The engine was audited and repaired;
> see [`AUDIT_OF_AUDIT.md`](AUDIT_OF_AUDIT.md) for the defect list and the evidence. What
> changed in the engine:
>
> - **The verifier no longer deletes true work.** `ALREADY_FIXED` was being inferred from
>   *token absence* even for claims that assert absence (`backend/Dockerfile` has no
>   HEALTHCHECK), and two cluster→measurement mappings probed the opposite claim. An
>   absence claim is now `UNVERIFIABLE`, and `claim_covers()` + `CLAIM_GAPS` refuse a
>   refutation whose instrument does not cover the claim.
> - **Two detectors were wrong and are fixed.** Law 37's predicate could not match the
>   limiter that does fail closed (a 429 is not a 5xx; `fail.?closed` does not match
>   “failing closed”), and the feature-gate literal regex read prose as code. Both findings
>   are gone.
> - **`logs/` can no longer lie by omission.** Every dimension file is rewritten each run and
>   previous ones are cleared, so an empty file means “evaluated, no findings”.
> - **Generated inventory.** `PLAN_FUNCTIONS.md` lists all 748 definitions with their
>   `@check` name and dimension; `python zz_core/inventory.py --check` fails when the registry
>   and the AST disagree. Regenerate it, never hand-edit it.
> - **Measured state (run `2026-10-06`, 92 detectors, `--full --no-tools`, 3823 files):**
>   1343 findings · 80 yes-blockers · verdicts **1307 CONFIRMED / 0 FALSE_POSITIVE /
>   0 WRONG_LOCATION / 1 ALREADY_FIXED / 35 UNVERIFIABLE** · plan 1326 steps
>   (1307 gating, 19 improvement) · regression gate **86 passed, 0 failed**.
>   The 164-unverifiable objective below is now 35; the remaining ones are clustered in
>   §5.1 of the audit-of-audit.

> **Version 4 (2026-10-05).** Complete source-of-truth document. Written by reading the
> `_zozi_audit/**` tree end-to-end and re-deriving every number from
> `zz_core/registry.py`, `zz_scanners/__init__.py`, `zz_core/measurements.py`, `zz_core/probe.py`,
> `logs/run.json`, `logs/checkpoint.json`, `logs/verdicts.jsonl`, `logs/facts.json`,
> `logs/plan.json`, `logs/verification_summary.json`, the 31 per-dimension JSONL logs, and the
> filesystem itself.
>
> Supersedes **PLAN.md v2 (2026-10-02)** — a design spec that is now stale
> (module list ends at `s21`; checks 82 vs actual 92; references `plan_status.json` and
> `zz_core/allowlist.yaml` that never existed).
>
> Supersedes **`AUDIT_SUITE_PLAN.md`**, which is listed in §11 for removal.
>
> **Deliverable (one command):** `python _zozi_audit/zozi_audit.py` produces one consolidated
> audit (`zozi_forensic_audit.md`) plus per-dimension JSONL in `logs/`. Stage two
> (`zozi_verify.py`) re-derives each claim independently; stage three (`zozi_compile.py`) turns
> only the surviving claims into an ordered remediation plan.
>
> **Two artifacts, two purposes — never merge them.** `zozi_forensic_audit.md` states *fact* about
> the repository. `zozi_remediation_plan.md` (produced by `zozi_compile.py`) states *intent*: what
> to do, in what order, how to prove it, and what it unblocks.
>
> **Benchmarks** (all present in `_most_imp_docx/`):
> - `ARCHITECTURE_STACK.md` — 325 laws, modules, domains, package layout, wiring.
> - `TECHNOLOGY_STACK.md` — pinned versions, forbidden packages, env vars.
> - `PROMPT_FORENSIC_AUDIT.md` — dimension schema, finding schema, phases, gates.
> - `FEATURE_STACK_LIST.md` / `FEATURE_STACK.md` — non-authoritative; used for feature-candidate
>   reconciliation only (separate diff pass, `s12_features.feature_stack_list_diff`).
>
> **Rules inherited from the prompt:** cite `path:line`; no aggregate rows (`N+`); every finding
> carries the full mandatory schema; never infer behaviour from folder names; verify, then
> classify; contradictions are surfaced, never silently resolved.

---

## 0 · What this suite is

One pass over the repository produces a list of **claims** about the code. A second stage
**re-derives each claim independently** and refuses to call it confirmed unless something other
than the detector agrees. A third stage turns only the surviving claims into an ordered fix plan.

The second stage is the point. A detector that reports a defect it cannot re-derive is a guess,
and a plan built from guesses wastes the reader's time.

```
python _zozi_audit/zozi_audit.py --full --no-tools   # scan   -> zozi_forensic_audit.md + logs/
python _zozi_audit/zozi_verify.py                     # adjudicate -> zozi_verification.md + verdicts
python _zozi_audit/zozi_compile.py                    # plan     -> zozi_remediation_plan.md + plan.json
python _zozi_audit/zozi_audit.py --self-test          # regression gate (delegates to tests/run_tests.py)
```

Each stage reads the previous stage's output from `_zozi_audit/logs/` and is safe to run on its
own. `--fast` = static checks only; `--browser --llm --db --load` adds runtime probes.

**Current measured state** (run `20261005T143848Z-2dbc4d`, commit
`3e0d1d818ebc08f1df17c5464543dd96aa7b0d94`, dirty 149 files, `--full --no-tools`, 10 workers,
3806 files walked):

| Metric | Value |
|---|---|
| Checks registered | **92** `@check`-decorated across `preflight`–`s24` + **10** pre-flight checks (not @check-decorated, registered in `preflight.CHECKS`) |
| Scanner modules | 24 `s*.py` + `preflight.py`; import failures: **0** |
| Tree scanned | **3806** files (2107 `.py`, 1216 `.ts`, 3806 all) |
| Findings emitted / verdicts | **1345 / 1345** |
| Verdicts | `CONFIRMED` 1174 · `UNVERIFIABLE` 164 · `ALREADY_FIXED` 7 |
| `FALSE_POSITIVE + WRONG_LOCATION` | **0** |
| `P0 / P1 / P2 / P3` findings | 100 / 359 / 689 / 197 |
| Hard completion blockers | 82 (yes) / 199 (partial) / 1064 (no) |
| Clusters | 135 |
| Files with findings | 659 |
| Verification basis | probe re-check 1163 · token_consistency 170 · cross-run disagreement 9 · cluster re-check 3 |
| Measurement functions | **76** `m_*` in `zz_core/measurements.py` |
| Probe kinds (`probe.py`) | **38** dispatch entries (37 distinct handlers) |
| Measured aggregates | **116** keys in `logs/facts.json` |

**Report verdict:** `NOT PRODUCTION READY` · 82 hard completion blocker(s).

**Remaining objectives:**
- `UNVERIFIABLE = 0` — in progress. 164 findings have no probe; they are `UNVERIFIABLE`, never
  guessed. Closing them means writing an independent re-check for each cluster.
- Runtime evidence (browser/load/DB/HTTP live probes) — deferred. The working tree is dirty (149
  files, in-flight refactor); a clean baseline is `HEAD` (`3e0d1d8`, 84 routes, 0 skipped).

## 1 · Directory layout (verified against disk)

```
_zozi_audit/
├── .gitignore                        # gitignore for reproducible outputs + bytecode (see §12.8)
├── PLAN.md                           # this file — source of truth (v4)
├── AUDIT_SUITE_PLAN.md               # ⚠ DEPRECATED — superseded by this file (see §11)
├── zozi_audit.py                     # PHASE C entry — scan -> zozi_forensic_audit.md
├── zozi_verify.py                    # adjudicate -> zozi_verification.md + logs/verdicts.jsonl
├── zozi_compile.py                   # compile -> zozi_remediation_plan.md + logs/plan.json
├── zz_core/
│   ├── __init__.py                   # __all__ = ["model", "constants", "util", "tools", "registry", "logs", "report"]
│   ├── constants.py                  # canonical modules/domains, router allowlist, env contract, ID prefixes
│   ├── lawmap.json                   # 325-law coverage table (benchmark_laws_total=325, enforced_by_check=126, candidate_unattributed=133 dims)
│   ├── logs.py                       # JSONL writers, checkpoint, run metadata, tool ledger
│   ├── measurements.py               # 76 independent re-derivation functions (m_*)
│   ├── model.py                      # Finding, Observation, CheckResult, ToolResult, ScanContext, enums
│   ├── probe.py                      # ProbeRunner: 38 probe kinds, SQL destructiveness helpers, utf-8-sig
│   ├── probes.py                     # LAW_MEASUREMENT_BY_LAW / CLUSTER_MEASUREMENT / FINDING_MEASUREMENT maps
│   ├── registry.py                   # @check() decorator, registry, bounded 10-worker executor
│   ├── report.py                     # single consolidated markdown renderer
│   ├── tools.py                      # subprocess runner + tool probes (keeps untruncated stdout)
│   └── util.py                       # walk_files (exclusions), read_text (BOM-tolerant), AST helpers, snippets
├── zz_integrations/
│   ├── __init__.py
│   ├── http_probe.py                 # live HTTP/1.1 probe (raw socket GET/OPTIONS/HEAD)
│   ├── browser_probe.py              # Playwright step capture (independent CLI)
│   ├── db_probe.py                   # ORM↔DB schema introspection (independent CLI)
│   ├── load_probe.py                 # latency sampling (independent CLI)
│   └── ollama_probe.py               # local-LLM semantic review (independent CLI)
├── zz_scanners/
│   ├── __init__.py                   # imports all s*.py + preflight at import time; collects import failures
│   ├── preflight.py                  # Phase 0 (boot smoke) + Phase 0.5 (pre-flight); blockers are emitted as dimension-27 findings
│   ├── s01_architecture.py           # dims 01/17 — layer purity, canonical modules/domains, router thinness
│   ├── s02_technology.py             # dims 02/28 — dependency pins, forbidden packages, versions
│   ├── s03_logic.py                  # dims 03/22/25 — money types, silent except, blocking IO, idempotency
│   ├── s04_operations.py             # dims 04/13 — jobs, health checks, CI/CD, deployment assets, feature flags
│   ├── s05_wiring.py                 # dims 05/20 — middleware order, auth/websocket, observability/resilience
│   ├── s06_database.py               # dims 06/07/10 — ORM model audit, migration history, live DB drift
│   ├── s07_providers.py              # dim 08 — provider inventory + resilience/health/timeouts
│   ├── s08_laws.py                   # dim 09 — parse 325 laws from ARCHITECTURE_STACK.md; law conformance (PASS/FAIL/UNVERIFIABLE)
│   ├── s09_environment.py            # dim 11 — env-var inventory + settings_contract (read vs declared)
│   ├── s10_tests.py                  # dim 12 — test inventory + architecture tests
│   ├── s11_frontend.py               # dims 14/15/26 — route tree, a11y, API alignment, mobile
│   ├── s12_features.py               # dims 16/23 — feature-catalog health, stack-list diff, code intent
│   ├── s13_security.py               # dim 18 — OWASP A01–A10 static checks + platform security laws
│   ├── s14_performance.py            # dim 19 — pagination, cache, index, N+1
│   ├── s15_crosscut.py               # dims 21/24/27 — contradictions, chains, browser bridge, blockers
│   ├── s16_design.py                 # dim 14 extension — tokens, colour drift, primitives, dark mode
│   ├── s17_interactions.py           # 14/12 extension — buttons, toasts, forms, modals, handover
│   ├── s18_feature_matrix.py         # dim 16 extension — feature matrix completeness, taxonomy depth
│   ├── s19_workflow.py               # 04/27 extension — celery runtime, event spine, QA, finance automation
│   ├── s20_db_advisor.py             # 07 extension — table posture, migration/ORM drift, advisory
│   ├── s21_http_layer.py             # 14/18 extension — live response contract + static header policy
│   ├── s22_frontend_contracts.py     # 14/26 extension — contract tests for frontend endpoints/routes (probe-verifiable)
│   ├── s23_law_coverage.py           # law-coverage accounting: what the suite does NOT check
│   └── s24_declared_laws.py          # laws decidable from source all along (harness, git, tsconfig, layer purity)
├── tests/
│   ├── __init__.py
│   ├── fixtures.py                   # known-positive / known-negative benchmark sources
│   ├── run_tests.py                  # regression gate: each detector's polarity vs fixtures
│   └── __pycache__/                  # ⚠ pyc bytecode (see §11 for removal)
├── logs/
│   ├── .gitkeep                      # keeps empty logs/ directory in git
│   ├── run.json                      # run metadata (run_id, commit, options, file_counts, dirty_files)
│   ├── checkpoint.json               # phase final, files_processed, findings_written, pass 2
│   ├── findings.jsonl                # 1345 emitted findings (all NEW this run)
│   ├── verdicts.jsonl                # 1345 adjudicated (1174 CONFIRMED, 164 UNVERIFIABLE, 7 ALREADY_FIXED)
│   ├── observations.jsonl
│   ├── plan.json                     # compiled plan (zozi_compile.py): 1193 steps, 1174 gating, 19 improvements
│   ├── facts.json                    # 116 measured aggregates
│   ├── tool_ledger.json              # tool runs (cmd, exit, duration, tail)
│   ├── recommendations.jsonl         # non-gating recommendations
│   ├── rec_*.jsonl                   # per-area dumps: automation, data, design, finance, frontend, ops, qa, workflow (8)
│   ├── 01_architectural.jsonl … 28_supply_chain_security.jsonl   # 28 primary dimension logs
│   ├── 23_law_coverage.jsonl + 29_law_coverage.jsonl              # law-coverage accounting (see §12)
│   ├── 30_declared_laws.jsonl                                    # declared-laws declarations
│   ├── browser_results.json, db_results.json, load_results.json, llm_results.json
│   ├── http_probe.log                                             # raw live-HTTP probe log (not in PLAN.md v3)
│   ├── llm_cache.json                                             # Ollama cache (not in PLAN.md v3)
│   └── verification_summary.json                                  # adjudication metrics (generated 2026-10-05T14:46:26)
├── __pycache__/                      # ⚠ root-level pyc bytecode (zozi_audit, zozi_compile, zozi_verify)
├── zz_core/__pycache__/              # ⚠ pyc + 6 DEAD files with no source
├── zz_scanners/__pycache__/
├── zz_integrations/__pycache__/
└── tests/__pycache__/
```

There are **31 per-dimension JSONL files** in `logs/`, not 30: the sequence `01`–`28` plus
`23_law_coverage.jsonl` (which **shares the `23` namespace** with `23_code_intent.jsonl`),
`29_law_coverage.jsonl`, and `30_declared_laws.jsonl`. See §12.

**Pipeline order is load-bearing:**

```
zozi_audit.py  ──► zozi_forensic_audit.md     (facts)
        │
        ▼
zozi_verify.py  ──► zozi_verification.md       (adjudicated claims) + logs/verdicts.jsonl
        │
        ▼
zozi_compile.py ──► zozi_remediation_plan.md   (ordered, gated work) + logs/plan.json
```

Running `zozi_compile.py` without `logs/verdicts.jsonl` still works but emits a loud warning
and produces **no fix instructions at all** — every step defaults to `UNVERIFIABLE`. That is
deliberate: an unverified plan must not look executable.

**Excluded from every walk** (non-negotiable; avoids the `.kilo` worktree trap):
`.git/`, `.kilo/`, `.freebuff/`, `node_modules/`, `__pycache__/`, `.pytest_cache/`,
`.hypothesis/`, `.next/`, `dist/`, `build/`, `venv/`, `.venv/`, `_extra_files/`,
`_legacy.bak/`, `test-results/`, `playwright-report/`, `_zozi_audit/`,
`*.min.js`, `*.map`, binary files. `ctx.rel()` always returns **forward slashes**, because every
scanner matches on `backend/...`-style strings and a Windows `\` silently defeats those filters.

## 2 · The 5 layers

### Layer 1 — `zz_core` (shared model, tooling, reporting)

- **`model.py`**: `Finding` (id, dimension, phase, status, cluster, file:line, current/target/delta, fix, effort, priority, confidence, evidence_strength, truth_level, claim_state, sibling, verify, test, rollback, blast_radius, depends_on, blocks, completion_blocker, laws, snippet), `Observation`, `CheckResult` (findings/observations/tool_results/facts), `ToolResult` (named tool runs: timeout, capped full output), `ScanContext`.
- **`constants.py`**: canonical sets (5 modules, 15 domains), `ROUTER_OK_INFRA` (routers may import only approved infra modules), `ID_PREFIX_BY_DIMENSION`, env contract. Shared between scanner and probe so they never diverge.
- **`util.py`**: `walk_files()` (symlink-safe, bounded walk), `read_text()` (tolerant `utf-8-sig` — repo files carry a BOM), AST helpers (`ast_imports`, `ast_calls`, `module_of`), `snippet()`/`line_of()`.
- **`tools.py`**: optional subprocess orchestration (npm/pnpm/npx shim on Windows, tsc, pytest/pytest-xdist, playwright, Ollama, db, load); timeouts from `--check-timeout` (default 900 s); `FULL_OUTPUT_CAP` 24 MB.
- **`registry.py`**: `@check(name, dimension, phase, instructions)` decorator registers self-contained sub-agents; bounded executor — never more than 10 checks concurrently; crash/timed-out checks emit auditor-defect findings instead of aborting.
- **`logs.py`**: `RunLog` writes JSONL streams, checkpoint state, `run.json` metadata (run_id, start, root, options, file_counts, commit, dirty_files).
- **`report.py`**: single consolidated markdown renderer; tables clipped at 300 chars; 18-condition production-readiness gate; anti-pattern aggregation; chain rollups.
- **`measurements.py`**: 76 `m_*` functions — re-derivations of aggregate count claims from **separate traversals** of the working tree (importing the detector's own counter would make the probe agree by construction). Every measurement returns `(count, description)`; the probe holds while the count is non-zero.
- **`probe.py`**: `ProbeRunner` — **38 probe kinds** in the dispatch map (`text_absent`, `text_present`, `text_matches`, `except_handler_silent`, `timestamp_default_is_python`, `law_unenforced`, `law_citation_drift`, `settings_field_absent`, `celery_task_unregistered`, `migration_downgrade_empty`, `destructive_op_unguarded`, `ci_step_absent`, `router_has_no_endpoints`, `duplicate_files_both_present`, `duplicated_bodies_present`, `ast_call_without_kwarg`, `ast_relationship_missing_kwarg`, `ast_model_missing_column`, `ast_annotation_contains`, `ast_attr_undeclared`, `attribute_absent_in_dict`, `path_absent`, `path_present`, `package_cycle_exists`, `filename_count_above`, `api_path_resolves`, `count_below`, `count_at_or_above`, `function_len_above`, `ast_forbidden_call_in_function`, `module_imports_above`, `law_measure`, `measure`, `test_global_mutation_unguarded`, `tsconfig_strict_off`, `file_line_count_above`, `symbol_occurrences` — note `measure` and `law_measure` alias the same handler), plus `utf-8-sig` reads. `resolvable=False` for probes that cannot be run against current source.
- **`probes.py`**: maps `LAW_MEASUREMENT_BY_LAW`, `CLUSTER_MEASUREMENT`, `FINDING_MEASUREMENT` + builder functions wiring probes to findings.
- **`lawmap.json`**: 325-law coverage table — `benchmark_laws_total = 325`; `enforced_by_check = 126` (law ID → declaring scanners); `candidate_unattributed` = 133 dimensions each mapping to law names that check briefs mention but that carry no formal law reference.

### Layer 2 — `zz_scanners` (92 @check-decorated checks + 10 pre-flight)

Each module registers its checks at import time (`zz_scanners/__init__.py` imports all 24 `s*` modules + `preflight` via `import_module`; import failures are collected, never fatal). Verified counts (from `@check(` decoration in each file, summed = 92):

| Module | @check | Dimension(s) |
|---|---|---|
| preflight | 10 (not @check-decorated) | Phase 0 boot / Phase 0.5 pre-flight (blockers emitted in dim 27) |
| s01 | 7 | 01, 17 |
| s02 | 4 | 02, 28 |
| s03 | 7 | 03, 22, 25 |
| s04 | 5 | 04, 13 |
| s05 | 7 | 05, 20 |
| s06 | 5 | 06, 07, 10 |
| s07 | 2 | 08 |
| s08 | 1 | 09 |
| s09 | 3 | 11 |
| s10 | 1 | 12 |
| s11 | 4 | 14, 15, 26 |
| s12 | 2 | 16, 23 |
| s13 | 4 | 18 |
| s14 | 3 | 19 |
| s15 | 5 | 21, 24, 27 |
| s16 | 3 | 14 extension (design/system colour drift, not the prompt's dim 14) |
| s17 | 5 | 14/12 extension (interaction robustness) |
| s18 | 3 | 16 extension (feature matrix) |
| s19 | 7 | 04/27 extension (workflow) |
| s20 | 2 | 07 extension (db advisor) |
| s21 | 2 | 14/18 extension (HTTP layer) |
| s22 | 4 | 14/26 extension (frontend contracts, probe-verifiable) |
| s23 | 1 | law-coverage accounting (dimension 29) |
| s24 | 5 | declared laws (dimension 30) |

**s22/s23/s24 are post-v2 additions** (written after PLAN.md v2 on 2026-10-02) and are absent from v2's module list. `preflight` is not `@check`-decorated; it registers 10 pre-flight checks in `preflight.CHECKS`.

### Layer 3 — `zz_integrations` (optional truth-seeking tools)

`http_probe.py`, `browser_probe.py`, `db_probe.py`, `ollama_probe.py`, `load_probe.py`. Every external command is optional: failures are captured as `ToolResult` and never abort the audit. These run only with `--browser --llm --db --load`; in `--fast`/`--no-tools` mode the report shows which integration evidence is missing rather than guessing.

### Layer 4 — `zz_core/probe.py` + `measurements.py` (re-verification)

**Why this exists.** A finding's `current` is prose. Prose cannot be verified without guessing, and guessing is what produced every `FALSE_POSITIVE` and `WRONG_LOCATION`. A probe is the machine-checkable form of the same claim: the verifier runs it against current source and gets a boolean.

**Probe semantics (learned rules):**
- A detector may not emit a probe it cannot itself run — otherwise the bug moves into the probe and the verdict becomes *confidently* wrong.
- A probe names a node, not a shape — `ast_relationship_missing_kwarg` pins the call name and line; a looser variant matched whichever relationship happened to be nearby and produced false positives.
- Absence probes must prove absence; a value supplied by a declarative base satisfies the requirement (probe resolves the base before reporting absence).
- `text_matches` / `text_absent` hold while the code is unchanged and fail the moment it changes; `resolvable=False` (file gone, scope unsupported) → `UNVERIFIABLE`, never a pass.
- Location proof is free: does the cited file exist, does the cited line exist? A finding whose `path:line` no longer resolves is a `WRONG_LOCATION`.
- BOM handling: `ProbeRunner.text()` uses `utf-8-sig` like the scanner side.
- Migration-destructive classification uses DROP / TRUNCATE / DELETE-without-WHERE / `ALTER…DROP` / `ALTER COLUMN TYPE` — bare `execute` is not destructive.

### Layer 5 — `logs/` (streaming state)

`run.json` / `checkpoint.json` (orchestration), `findings.jsonl` (emitted claims), `observations.jsonl`, `verdicts.jsonl` (adjudicated), `plan.json`, `facts.json` (116 aggregates), `tool_ledger.json`, `recommendations.jsonl` (+ `rec_*.jsonl` per-area dumps), 31 per-dimension raw logs, runtime probes (`browser_results.json`, `db_results.json`, `load_results.json`, `llm_results.json`, `http_probe.log`, `llm_cache.json`), `verification_summary.json`.

## 3 · CLI contract (verified against `main(argv=None)` in each entry point)

```
python _zozi_audit/zozi_audit.py
    [--root .]
    [--out _zozi_audit/zozi_forensic_audit.md]
    [--workers 10]                       # concurrent checks, max 10
    [--fast]                             # static checks only
    [--full]                             # run every available tool (default)
    [--no-tools]                         # never spawn subprocesses
    [--dimensions 01,06,18]
    [--browser] [--browser-base URL]
    [--llm] [--ollama-url URL] [--ollama-model M] [--ollama-limit 25]
    [--db] [--dsn DSN]
    [--load] [--load-url URL]
    [--quiet]
    [--check-timeout 900.0]
    [--self-test]                        # regression gate, delegates to tests/run_tests.py
```

```
python _zozi_audit/zozi_verify.py [--logs _zozi_audit/logs] [--out _zozi_audit/zozi_verification.md]
    [--cluster CLUSTER-...] [--limit N] [--strict]
```

```
python _zozi_audit/zozi_compile.py [--logs _zozi_audit/logs] [--out _zozi_audit/zozi_remediation_plan.md]
    [--json] [--wave N] [--status ID=pending|in_progress|done|dismissed]
    [--list] [--check CLUSTER-...]
```

- `--fast` skips subprocess tools (ruff/pytest/tsc/next/alembic/pnpm) and integrations.
- `--full` (default) runs everything available, each with timeouts and `ToolResult` ledger entries.
- Failures of optional integrations never abort the run.
- **The three phases are ordered and dependent.** `zozi_verify.py` reads `logs/findings.jsonl`;
  `zozi_compile.py` reads `logs/findings.jsonl` **and** `logs/verdicts.jsonl`. Compiling without
  verifying produces a plan with zero fix instructions and an explicit warning — the intended
  failure mode, not a bug.
- `zozi_verify.py --strict` exits non-zero when the false-positive rate exceeds 20%, making
  "is this plan safe to execute" a CI-checkable question.
- **No `plan_status.json` in the current code.** PLAN.md v2 listed `plan_status.json` in
  `logs/`; the current compiler does not write or read it (step-state round-trip is not
  implemented). `zz_core/allowlist.yaml` is also absent.
- **Phase naming:** the suite uses wave-numbered phases 0–5 with titles stored in
  `zozi_compile.PHASE_TITLES`, not "Phase A/B/C":
  - `0`: Restore the ability to verify anything (build / boot / test / migrate)
  - `1`: Fix the hard blockers that prevent correct behaviour
  - `2`: Close correctness and security defects
  - `3`: Close coverage, quality and performance defects
  - `4`: Verification tasks for untrusted claims
  - `5`: Improvement track — recommendations (not release-gating)
  The report labels its precondition table "Phase 0 / 0.5" and the compilation step "Phase 5".
  (PLAN.md v3's "PHASE A / B / C" labels appear in no code; they have been corrected here.)

## 4 · Report layout (`zozi_forensic_audit.md`)

The report has 11 numbered sections + 3 appendices (186 heading levels total), generated with run
metadata header:

1. **Header** (generated timestamp, run ID, commit, mode, workers, repo root, benchmark list,
   surface: 2107 Python / 1216 TS / 3806 total) + `## 0 · Pre-conditions (Phase 0 / 0.5)` — a
   10-row check table (boot smoke, env vars, DB, Valkey, tests, type-check, lint, alembic,
   lockfile, architecture) with verdict line: **NOT PRODUCTION READY · 82 hard completion
   blocker(s)**.
2. `## 1 · Headline numbers` — findings 1345; P0/1/2/3 = 100/359/689/197; blockers 82/199/1064;
   clusters 135; files with findings 659; contradictions 5; anti-pattern categories 7 (11 in
   `facts.json`); chains 7; browser steps 71; LLM hotspots 0; HTTP probed 0; recommendations 19;
   estimated P0+P1 effort ~1032h; coverage 28/28 dimensions.
3. `## 2 · Completion blockers (fix before anything else)` — grouped `yes` then `partial`.
4. `## 3 · Top findings (priority ranked)`.
5. `## 4 · Clusters (shared root causes)`.
6. `## 5 · Dimensions` — one subsection per dimension 01–30, each with Summary / Findings / "Over
   all"; dimension 09 includes a **Law matrix (1-325)**.
7. `## 6 · Cross-cutting passes` — 6.1 Chains (7 chains with step evidence), 6.2 Contradictions
   (5, never silently resolved), 6.3 Anti-patterns, 6.4 Feature health, 6.5 Code intent, 6.6 AI
   drift, 6.7 Code alignment (frontend << backend << mobile), 6.8 Browser behavior, 6.9 Supply
   chain security, 6.10 LLM semantic review (Ollama, L2 only), 6.11 Live database drift,
   6.12 Load / latency probe.
8. `## 7 · Production readiness · 18-condition gate` — pass/fail/unverifiable + evidence, plus
   Unverifiable conditions and Waivers.
9. `## 8 · Design, interaction, taxonomy, workflow & data measurements` — design system,
   interaction robustness, feature & taxonomy, HTTP layer (live responses), settings contract,
   workflow & automation, database management.
10. `## 7 · Recommendations & automation opportunities` — 8 area tabs (automation, data,
    workflow, design, qa, frontend, finance, ops). (Section numbering in the rendered report is
    0–8 plus appendices; PLAN.md v3's §4 described it as 13 sections — the current render has 11
    numbered sections.)
11. `## 8 · Remediation plan` — completion blockers first, phase execution order by package, P0
    table (100 findings), KEEP/HARDEN candidates.
12. **Appendix A · Tool-run ledger** (cmd, exit, duration, tail).
13. **Appendix B · Coverage & method** — exclusions, what could not be verified and why.
14. **Appendix C · Auditor self-check** — each check's run status, files touched, findings
    produced.

## 5 · The compile step (`zozi_compile.py`)

```
python _zozi_audit/zozi_audit.py     # → zozi_forensic_audit.md   (fact)
python _zozi_audit/zozi_verify.py     # → zozi_verification.md     (adjudicated)
python _zozi_audit/zozi_compile.py   # → zozi_remediation_plan.md (intent)
```

The audit alone leaves the reader with 1,345 findings and no order. The compiler turns them into
a plan an agent or a person can follow.

**Inputs:** `logs/findings.jsonl`, `logs/verdicts.jsonl`, `logs/facts.json`, `logs/run.json`.
**Outputs:** `zozi_remediation_plan.md` and `logs/plan.json`.

**Classification rules:**

| Step kind | When | Wave |
|---|---|---|
| `gate` | the check is in a gate cluster (boot, test-collection, migrations, lockfile) **or** a pre-flight row is FAIL | 0 |
| `fix` | `truth_level=L0` **and** `claim_state ∉ {UNKNOWN, INFERRED, CONTRADICTED}` | 1–3 |
| `verify` | any finding not `CONFIRMED` | 4 |
| `improve` | sourced from a recommendation; never release-gating | 5 |

Waves 1–3 are then split by priority: `completion_blocker=yes` or `P0` → 1, `P1` → 2,
`P2`/`P3` → 3. A flat list is not a plan: steps are grouped by cluster; a cluster with more than
25 steps is split by its dominant file. Each package reports step count, files touched, blocker
count, verification count, estimated hours, and a one-line focus.

| Wave | Title | Why it is there |
|---|---|---|
| 0 | Restore the ability to verify anything | A static audit on a project that does not boot, migrate or collect tests produces numbers without meaning |
| 1 | Hard blockers preventing correct behaviour | |
| 2 | Correctness and security defects | |
| 3 | Coverage, quality and performance defects | |
| 4 | Verification of untrusted claims | Never instruct a code change on a hunch |
| 5 | Improvement track | Recommendations, non-gating, ordered by workload removed |

Only verified evidence becomes a blocking step: a finding whose `claim_state` is `UNKNOWN`/`INFERRED`
at L0 is a **verification task**, never a fix task. Recommendations are a separate track: they
never gate release and are ordered after blockers unless they unlock one.

## 6 · Accuracy strategy — the falsification gate (`zozi_verify.py`)

**The problem this solves.** The audit makes *claims*. Nothing in the pipeline tries to prove
them wrong until `zozi_verify.py` runs.

**Method — refutation-first, not confirmation-first:**

| Basis | Rule | May conclude |
|---|---|---|
| `cluster_recheck` | A **second, independent implementation** of the same question (AST vs regex; declared-field set vs mention scan; live wire bytes vs source text) | `CONFIRMED` or `FALSE_POSITIVE` |
| `token_consistency` | Compares the claim's tokens with the cited line / file / directory tree | **Refutation only.** `ALREADY_FIXED`, `WRONG_LOCATION`, `UNVERIFIABLE` — **never** `CONFIRMED` |

**The three rules that keep the gate itself honest:**

1. **A line drift is not a refutation.** If the cited line carries none of the claim's tokens
   but the tokens exist elsewhere in the file, the verdict is `UNVERIFIABLE` with the drift
   flagged — not `WRONG_LOCATION`. Token matching on prose cannot prove a finding wrong.
2. **A directory is not a missing file.** Cluster-level findings legitimately cite a directory
   (`backend/modules/finance`). Those are adjudicated by scanning the tree. Reporting them as
   `WRONG_LOCATION` produced spurious mislocations on the first run.
3. **Absence may be the claim.** When a finding asserts that something is missing and the path
   is absent, that is *consistent*, so it is `UNVERIFIABLE` with an explicit note, never
   `WRONG_LOCATION`.

**Compiler gating:** `zozi_compile.py` reads `logs/verdicts.jsonl` and:
- **drops** any finding adjudicated `FALSE_POSITIVE` or `ALREADY_FIXED` from every wave, and
  lists it in a **Rejected findings** appendix with its counter-evidence, so the exclusion is
  auditable rather than silent;
- **downgrades** anything not `CONFIRMED` to a `verify` step in **wave 4**, regardless of the
  priority the audit assigned it;
- **emits a `fix` step only for a `CONFIRMED` verdict**;
- prints a loud gate banner, and warns when `verdicts.jsonl` is absent.

**Adjudication metrics** (`logs/verification_summary.json`, generated 2026-10-05T14:46:26):

| Metric | Value |
|---|---|
| Findings / verdicts | 1345 / 1345 |
| `CONFIRMED` | 1174 (87.3%) |
| `UNVERIFIABLE` | 164 (12.2%) |
| `ALREADY_FIXED` | 7 (0.5%) |
| `FALSE_POSITIVE` | 0 |
| `WRONG_LOCATION` | 0 |
| false_positive_rate_pct | 0.0% |
| not_actionable_pct | 0.5% |
| independently_confirmed_pct | 87.3% |
| `P0` total | 100 · confirmed 77 · false_or_wrong 0 · noise 0.0% |
| verification basis | probe 1163 · token_consistency 170 · probe_over_recheck_disagreement 9 · cluster_recheck 3 |
| cross-run disagreements | 9 |

**A ~12% unverifiable share is the honest result, not a defect.** Most clusters have no
independent re-check, so the default verdict is `UNVERIFIABLE` rather than a guess. The
consequence is stated plainly: **the current plan is not safe to execute blindly.** Wave 4 is
164 verification tasks.

**Compiled plan** (`logs/plan.json`, source run 20261005T143848Z-2dbc4d):

| Wave | Steps | Hours | Blockers |
|---|---|---|---|
| 1 | 77 | 164.0 | 65 |
| 2 | 286 | 674.5 | 0 |
| 3 | 811 | 1335.0 | 0 |
| 5 | 19 | 116.0 | 0 (19 improvements) |
| **total** | **1193** | **2173.5** | **65** |

`steps_out: 1193`, `release_gating_steps: 1174`, `improvement_steps: 19`, `confirmed_steps: 1174`,
`findings_rejected: 7`, `recommendations_in: 19`, `warnings: []`. Waves 0 and 4 have zero steps
this run (wave 0 blocked by the boot/test/migration skip in `--no-tools` mode; wave 4 only holds
unverified claims).

## 7 · Current measured state (from the last run)

Run `20261005T143848Z-2dbc4d` — commit `3e0d1d818ebc08f1df17c5464543dd96aa7b0d94`, dirty 149
files, `--full --no-tools`, workers 10, checkpoint `phase: final, pass: 2, files_processed: 3806,
findings_written: 1345`:

### 7.1 Aggregate facts (`logs/facts.json` — 116 keys)

| Measure | Value |
|---|---|
| `cross_domain_imports` | 812 |
| `package_cycles` | 82 |
| `silent_except_count` | 203 |
| `float_money_files` | 132 |
| `long_functions` | 408 |
| `deep_functions` | 90 |
| `untracked_todos` | 295 |
| `migration_revisions` | 90 · `migration_heads` 4 |
| `endpoints_total` | 1003 · unguarded 2 · public_by_design 9 |
| `gate_literals` | 147 |
| `catalog_atoms` | 371 |
| `env_vars_raw` | 103 · `env_vars_declared` 225 · `env_vars_documented` 259 |
| `anti_patterns` | 9 categories (Silent except 203, Stub function 48, Unimplemented placeholder 257, TODO-only 296, Empty handler 5, Not-wired event 4, Commented code 478) |
| `compat_shim_files` | 3 |
| `commitlint_configured` | False |
| `branch_policy_declared` | False |
| `blocking_async_count` | 0 |
| `conftest_files` | 15 |
| `drift` | 1141 items (list; not in report headline) |
| `provider_resilience` | 94 providers · 8 breakers · 7 retries · 29 timeouts |
| `events_defined` | 125 · `events_published` 6 (subscribers by module) |
| `middleware_order` | 8 items |
| `rls_policy_var` | `app.current_country_code` · `rls_middleware_var` `app.country_scope` |
| `contradictions` | 5 items |
| `chains` | 7 items |
| `browser_steps` | 71 items (evidence stale: True; observed = unknown, FAILED) |
| `supply_chain` | 4 items (no dep scanning, no secret scanning, and 2 more) |

### 7.2 Per-dimension finding counts (`logs/*.jsonl`)

| Dim | Log | Findings |
|---|---|---|
| 01 | architectural | 172 |
| 02 | technological | 21 |
| 03 | logical | 306 |
| 04 | operational | 30 |
| 05 | wiring | 13 |
| 06 | database | 9 |
| 07 | tables_fields | 266 |
| 08 | providers | 8 |
| 09 | laws | 26 |
| 10 | migrations | 15 |
| 11 | environmental | 15 |
| 12 | tests | 36 |
| 13 | dev_to_prod | 8 |
| 14 | frontend_web | 216 |
| 15 | frontend_mobile | 1 |
| 16 | features | 5 |
| 17 | code_file_management | 94 |
| 18 | security | 12 |
| 19 | performance | 3 |
| 20 | observability_resilience | 5 |
| 21 | contradictions | 5 |
| 22 | anti_patterns | 5 |
| 23 | code_intent | 3 |
| 24 | browser_behavior | 1 |
| 25 | ai_drift | 1 |
| 26 | code_alignment | 7 |
| 27 | project_completion_blockers | 4 |
| 28 | supply_chain_security | 7 |
| 30 | declared_laws | 14 |
| 29 | law_coverage | 45 |
| 23 (dup) | law_coverage | 46 |

Unique-dimension total: 1303 findings; the two `law_coverage` logs (23 and 29) together add
91 near-duplicate lines (see §12).

### 7.3 Law state (`zz_core/lawmap.json` + `logs/09_laws.jsonl`)

- `benchmark_laws_total = 325`.
- `enforced_by_check = 126` — law IDs with a declaring scanner.
- `candidate_unattributed = 133` dimensions mapping to 330 law names that check briefs mention
  but which carry no formal law reference.
- `logs/09_laws.jsonl` has **26 findings**, all `NEW` / `VERIFIED` / `L0`, classified
  PASS/FAIL/UNVERIFIABLE per the dimension-09 scanner. Violations cluster as:
  architecture 5 · structure 2 · code-quality 6 · migration 1 · security 3 · database 4 ·
  config 1 · provider 2 · performance 1 · docs 1.
- The `s24_declared_laws` docstring describes the coverage registry's partition: 114 laws
  enforced by the pre-s24 scanners, 127 enforced-but-unattributed, and 84 with no check. The
  current `enforced_by_check` count of 126 reconciles as 114 + 12 laws declared by `s24`
  itself. **Note:** the PLAN.md v3 line "fail 26 · pass 33 · unverifiable 266 · no check 66" is
  not supported by the logs — 26 violations are confirmed; "pass 33", "unverifiable 266", and
  "no check 66" have no source in the code (266 coincides with the dim-07 finding count;
  `325 − 126 = 199` laws are not enforced by check).

## 8 · Step-by-step execution plan (as built)

| Step | Work | Status gate |
|---|---|---|
| P1 | Write this plan file | ✅ |
| P2 | Verify plan assumptions against the codebase (this pass) | ✅ |
| P3 | `zz_core` — model, registry, logs, report, util, tools, constants | ✅ |
| P4 | `zz_scanners` — s01–s21 + preflight | ✅ |
| P5 | Extensions s22/s23/s24 + probe layer wiring | ✅ |
| P6 | Run `--full`, reconcile findings against source, kill false positives | ✅ (`FALSE_POSITIVE + WRONG_LOCATION = 0`) |
| P7 | Adjudicate every finding through `zozi_verify.py` | ✅ (1345 adjudicated) |
| P8 | Gate the compiler on verdicts | ✅ |
| P9 | Close the 164 UNVERIFIABLE with independent re-checks | ❌ outstanding |

**The single outstanding gate is P9.** Once all 164 are resolved, the entire plan is either
fix-tasks (verified) or explicitly labelled verification-tasks (wave 4) — never a code change
on a hunch.

## 9 · Accuracy history — defects found and fixed

| Pass | Measurement | Correction |
|---|---|---|
| v2 ext. | `inline_style_props` | React Native has no CSS cascade; mobile `style={{}}` excluded from web drift |
| v2 ext. | `unindexed_hot_columns` | `Column(..., index=True)` is an index but produces no name in `__table_args__` |
| v2 ext. | `hardcoded_hex` | mobile RN literals plus brand SVG / chart palette files, where a literal is correct |
| v2 ext. | undefined feature gates | `require_feature` matched inside comments and docstrings |
| v2 ext. | celery app | searched `backend/` root; it lives at `backend/jobs/celery_app.py` |
| v2 ext. | toast ratio | counted the words anywhere instead of the `addToast()` call shape |
| v2 ext. | missing `version` column | no law requires it; demoted to a recommendation |
| v3 | TS errors | `pnpm exec` ran the supply-chain hook instead of tsc; counts parsed from an elided `stdout_tail` |
| v3 | `missing_from_middleware` | headers applied from a dict in a loop; literal matching cannot see it |
| v3 | CSP directive gap | broken regex; `object-src`/`base-uri` are present |
| v3 gate | `WRONG_LOCATION` | directories treated as missing files; a line drift claimed as a refutation |
| v3 gate | verdicts | first run of `zozi_verify.py`: 1345 adjudicated, 0 false positives |

Rule of thumb: **whenever a count is surprising, re-derive it with a different mechanism before
believing it.** Every "after" figure above was produced that way.

## 10 · Explicit non-goals / honesty constraints

- The audit **does not resolve** findings and the compiler **does not edit source**. A plan is
  not a fix.
- The audit **never modifies source files** — only `_zozi_audit/**`.
- The audit **cannot prove** runtime behaviour without a live stack; every such condition is
  marked `unverifiable` with the exact command that *would* verify it.
- The live HTTP probe **never mutates data** — GET, OPTIONS and HEAD only.
- LLM findings are labelled `L2/INFERRED` and can never be promoted to L0.
- No aggregate placeholders (`N+`, `~40`) anywhere; every count is produced by listing the
  underlying records.
- **A `CONFIRMED` verdict proves the claim, not the proposed fix.** Law, schema and security
  fixes still require engineering review before anyone edits code.
- **The verification gate is not a substitute for a reviewer.** Its value is that it prevents
  the plan from silently inheriting unmeasured noise.
- `zozi_audit.py --self-test` is documented as the regression gate; the flag handler delegates
  to `tests/run_tests.py` (the flag's own implementation was never written — see §12).

---

## 11 · Unnecessary files — what to remove

All entries below are confirmed by reading the filesystem; sizes are from the current scan.

### 11.1 Stale bytecode — delete all `__pycache__/` directories

Every `__pycache__/*.cpython-313.pyc` is generated on import and is not needed to run the suite.
**Remove all 55 `.pyc` files** and add `__pycache__/` to `.gitignore` instead of committing them:

| Location | Count | Notes |
|---|---|---|
| `zz_core/__pycache__` | 17 | 11 have source; **6 are DEAD** (no `.py`) |
| `zz_scanners/__pycache__` | 26 | all correspond to existing `.py` |
| `zz_integrations/__pycache__` | 6 | all correspond to existing `.py` |
| `tests/__pycache__` | 3 | all correspond to existing `.py` |
| root `__pycache__` | 3 | `zozi_audit`, `zozi_compile`, `zozi_verify` bytecode |

**6 DEAD bytecode files in `zz_core/__pycache__/`** — these have **no source file**:
`checklist.cpython-313.pyc`, `emit.cpython-313.pyc`, `lawroute.cpython-313.pyc`,
`loop.cpython-313.pyc`, `rollup.cpython-313.pyc`, `summary.cpython-313.pyc`. They are remnants
of the v2-era single-file layout that was refactored into the current per-concern files;
`zz_core/__init__.py` (`__all__ = [model, constants, util, tools, registry, logs, report]`)
does not import them.

### 11.2 Superseded plan document — delete `AUDIT_SUITE_PLAN.md`

Its pipeline and content are fully captured by this `PLAN.md` (v4). It is a duplicate that
conflicts with the current code (module list ends at `s21`; check count 82 vs actual 92; it
mentions `plan_status.json` and `allowlist.yaml` which do not exist).

### 11.3 Near-duplicate law-coverage logs — delete `23_law_coverage.jsonl`

`logs/23_law_coverage.jsonl` (46 lines, FIND-001…046) is a near-duplicate of
`logs/29_law_coverage.jsonl` (45 lines, LAWCOV-001…045): both contain the same findings about
unenforced / unattributed laws from the law-coverage rework. Keep `29_law_coverage.jsonl`
(dimension 29, the canonical post-v2 position) and delete the stale `23_law_coverage.jsonl`.
Deleting it also removes the namespace collision with `23_code_intent.jsonl`.

### 11.4 Stale report outputs — optional (in sync with current run)

`zozi_forensic_audit.md` (1,573,014 bytes), `zozi_remediation_plan.md` (699,399 bytes),
`zozi_verification.md` (4,554 bytes) are produced outputs, not source. Their timestamps all
read `20261005T143848Z`, matching `logs/run.json`, `logs/checkpoint.json` (phase 38, pass 2,
1345 findings) — so they are consistent with the current scan. Regenerate first if you want a
clean slate:

```
python _zozi_audit/zozi_audit.py --full --no-tools
python _zozi_audit/zozi_verify.py
python _zozi_audit/zozi_compile.py
```

### 11.5 Runtime probe artifacts — optional (stale / unused)

`logs/browser_results.json`, `logs/db_results.json`, `logs/load_results.json`, `logs/llm_results.json`,
`logs/http_probe.log`, `logs/llm_cache.json` — results of optional runtime probes run with a
running stack. They are not generated in `--no-tools` mode and are stale for the current dirty
work tree. Keep only if the running-stack evidence is wanted.

### 11.6 Plan artifacts that do not exist (do not delete — they were never created)

`logs/plan_status.json` and `zz_core/allowlist.yaml` — PLAN.md v2's directory layout and
accuracy-history sections reference both. Neither exists in the current code; v2 is simply
out of date. Nothing to remove.

### 11.7 Temporary scratch files (if present in the repo root)

Delete if they exist and are not part of the project: `_tmp_audit_files.txt`,
`_tmp_files.txt`, `_tmp_inspect.py` (session scratch).

### Summary of deletions

1. All 55 `__pycache__/*.pyc` files (with 6 dead `zz_core` ones highlighted).
2. `AUDIT_SUITE_PLAN.md`.
3. `logs/23_law_coverage.jsonl` (near-duplicate of `29_law_coverage.jsonl`; resolves the `23` namespace collision).
4. Optionally regenerate and recommit the three output reports, or leave them (they are in sync).
5. Optionally drop runtime probe artifacts (`browser/db/load/llm_results.json`, `http_probe.log`, `llm_cache.json`).
6. Optionally delete repo-root session scratch files.
7. Optionally clean stale references in `.gitignore` (lines 7, 14-15 cite `zz_core/summary.py` and
   `AUDIT_RESULT.md`, neither of which exists). Recommended: remove those two lines from `.gitignore`.

---

## 12 · Known inconsistencies and stale artifacts (in the suite itself)

These are worth knowing about because they can mislead a reader of the suite's code:

1. **`zz_scanners/__init__.py` (lines 34–36) has a stale comment:**
   > `# s22 was written but never added here, so none of its checks ever registered...`
   The comment is false: `s22_frontend_contracts` **is** in the `_MODULES` list (line 33), so all
   4 of its checks register. This comment dates from before `s22` was wired in.

2. **`23_law_coverage.jsonl` vs `29_law_coverage.jsonl` near-duplicates** (see §11.3). Both logs
   were produced by the law-coverage rework; one (FIND-001…046) predates the other
   (LAWCOV-001…045). They differ by exactly one line.

3. **`23` namespace collision:** `23_code_intent.jsonl` and `23_law_coverage.jsonl` both occupy
   the `23` position. The suite legitimately emits 31 dimension logs, not the documented 30.

4. **Law-count stale note:** `s24_declared_laws`'s docstring says "114 enforced" while
   `lawmap.json` says `enforced_by_check = 126`. This reconciles precisely: 114 enforced by
   the pre-s24 scanners + 12 of the 13 s24-declared law IDs present in the registry = 126.
   The 13th s24-declared law (Law 52) is **missing** from `lawmap.json`'s
   `enforced_by_check` — the registry was not updated when the s24 check was added.

5. **`zozi_audit.py --self-test`** is documented as the regression gate; the flag's handler was
   never written and instead delegates to `tests/run_tests.py`. Functionally the gate still
   exists; the docstring in the flag handler (lines 66–73) notes this explicitly.

6. **Report section numbering** in `zozi_forest_audit.md` (sections 0–8 + appendices) differs
   from PLAN.md v3's §4 description (13 sections). The rendered report has 11 numbered sections.
   The description in §4 above reflects the actual render.

7. **Anti-pattern categories:** `facts.json` lists 9 categories; the report headline says 7.
    The facts value is the measured one; the report count appears to exclude two low-count
    categories.

8. **`_zozi_audit/.gitignore` has stale references:** it mentions `zz_core/summary.py` (which
   never existed in the current layout) and `AUDIT_RESULT.md` as the "single file to read for
   the current result." Neither file exists. The `.gitignore` correctly ignores the three
   output reports (`zozi_forensic_audit.md`, `zozi_remediation_plan.md`,
   `zozi_verification.md`) and the entire `logs/` directory (except `.gitkeep`), and keeps
   `AUDIT_SUITE_PLAN.md` and `PLAN.md` tracked. The references to `summary.py` and
   `AUDIT_RESULT.md` can be cleaned but do no functional harm.

## 13 · Validation commands

```
python _zozi_audit/zozi_audit.py --self-test     # regression gate, delegates to tests/run_tests.py
python -c "from zz_core.registry import all_checks; print(len(all_checks()))"  # confirm 92 @check-decorated checks
python -c "import zz_scanners; print('import_failures:', zz_scanners.import_failures())"  # confirm 0
cd zz_core && python -c "import measurements; from measurements import MEASUREMENTS; print(len(MEASUREMENTS))"  # confirm 76
python -c "
from pathlib import Path
pycs = list(Path('_zozi_audit').rglob('*.pyc'))
print('pyc total:', len(pycs))
dead = [p for p in pycs if not (p.with_suffix('.py')).exists()]
print('dead pyc (no source):', [p.name for p in dead])
"
grep -n '^\s*@check(' _zozi_audit/zz_scanners/*.py | sed 's/:.*//' | sort | uniq -c   # per-module @check counts
python _zozi_audit/zozi_verify.py --strict        # exits ≠0 if false-positive rate > 20%
```

---

## 14 · Complete file inventory (by directory)

Sizes verified against disk (`20261005T143848Z-2dbc4d` run). Generated artifacts are
marked **(output)**; they are ignored by `.gitignore` but still present on disk from the
last run. Source files are marked **(source)**.

### `_zozi_audit/` (root)

| File | Bytes | Type | Notes |
|---|---|---|---|
| `.gitignore` | 1,092 | source | Ignores outputs + bytecode; has stale refs to `summary.py` / `AUDIT_RESULT.md` (see §12.8) |
| `AUDIT_SUITE_PLAN.md` | 10,191 | deprecated | Superseded by this file; flagged for removal (§11.2) |
| `PLAN.md` | 47,759 | source | This file |
| `zozi_audit.py` | 14,288 | source | PHASE C entry point — scan → `zozi_forensic_audit.md` |
| `zozi_verify.py` | 36,071 | source | Phase 1 adjudication — → `zozi_verification.md` + `logs/verdicts.jsonl` |
| `zozi_compile.py` | 44,011 | source | Phase 2 compilation — → `zozi_remediation_plan.md` + `logs/plan.json` |
| `zozi_forensic_audit.md` | 1,573,014 | output | Consolidated audit report (regenerable) |
| `zozi_remediation_plan.md` | 699,399 | output | Ordered remediation plan (regenerable) |
| `zozi_verification.md` | 4,554 | output | Verification summary (regenerable) |

### `zz_core/` (12 source files)

| File | Bytes | Notes |
|---|---|---|
| `__init__.py` | 201 | `__all__ = [model, constants, util, tools, registry, logs, report]` |
| `constants.py` | 14,268 | Canonical modules/domains, router allowlist, env contract, ID prefixes |
| `lawmap.json` | 16,889 | 325-law coverage table (`enforced_by_check=126`, `candidate_unattributed=133`) |
| `logs.py` | 4,475 | JSONL writers, checkpoint, run metadata, tool ledger |
| `measurements.py` | 60,065 | 76 `m_*` independent re-derivation functions |
| `model.py` | 11,957 | Finding, Observation, CheckResult, ToolResult, ScanContext, enums |
| `probe.py` | 93,271 | `ProbeRunner` — 38 probe kinds dispatch map + SQL destructiveness helpers |
| `probes.py` | 61,846 | LAW/CLUSTER/FINDING measurement maps + wiring |
| `registry.py` | 10,738 | `@check()` decorator + bounded 10-worker executor |
| `report.py` | 40,844 | Single consolidated Markdown renderer; 18-condition production gate |
| `tools.py` | 17,593 | Subprocess orchestration (ruff/pytest/tsc/alembic/pnpm/ollama) |
| `util.py` | 21,131 | `walk_files`, `read_text` (BOM-tolerant), AST helpers, `snippet()` |

### `zz_integrations/` (6 source files)

| File | Bytes | Notes |
|---|---|---|
| `__init__.py` | 330 | Package init |
| `http_probe.py` | 12,105 | Raw-socket HTTP/1.1 probe (GET/OPTIONS/HEAD only — never mutates) |
| `browser_probe.py` | 4,874 | Playwright step capture (independent CLI) |
| `db_probe.py` | 5,959 | ORM↔DB schema introspection (independent CLI) |
| `load_probe.py` | 3,051 | Latency sampling (independent CLI) |
| `ollama_probe.py` | 6,556 | Local-LLM semantic review (L2/INFERRED findings only) |

### `zz_scanners/` (26 source files)

| File | Bytes | @check-decorated | Dimensions |
|---|---|---|---|
| `__init__.py` | 1,953 | — | Imports all 24 `s*` + `preflight` at import time |
| `preflight.py` | 30,425 | 10 (not @check-decorated) | Phase 0 boot smoke + Phase 0.5 pre-flight |
| `s01_architecture.py` | 34,039 | 7 | 01, 17 |
| `s02_technology.py` | 21,055 | 4 | 02, 28 |
| `s03_logic.py` | 31,916 | 7 | 03, 22, 25 |
| `s04_operations.py` | 14,224 | 5 | 04, 13 |
| `s05_wiring.py` | 30,052 | 7 | 05, 20 |
| `s06_database.py` | 28,228 | 5 | 06, 07, 10 |
| `s07_providers.py` | 9,238 | 2 | 08 |
| `s08_laws.py` | 26,850 | 1 | 09 |
| `s09_environment.py` | 14,869 | 3 | 11 |
| `s10_tests.py` | 7,500 | 1 | 12 |
| `s11_frontend.py` | 17,863 | 4 | 14, 15, 26 |
| `s12_features.py` | 7,495 | 2 | 16, 23 |
| `s13_security.py` | 11,846 | 4 | 18 |
| `s14_performance.py` | 6,638 | 3 | 19 |
| `s15_crosscut.py` | 26,715 | 5 | 21, 24, 27 |
| `s16_design.py` | 23,072 | 3 | 14 extension (design system) |
| `s17_interactions.py` | 28,931 | 5 | 14/12 extension (interaction robustness) |
| `s18_feature_matrix.py` | 28,641 | 3 | 16 extension (feature matrix) |
| `s19_workflow.py` | 43,509 | 7 | 04/27 extension (workflow) |
| `s20_db_advisor.py` | 21,248 | 2 | 07 extension (table posture) |
| `s21_http_layer.py` | 28,172 | 2 | 14/18 extension (live response contract) |
| `s22_frontend_contracts.py` | 16,936 | 4 | 14/26 extension (frontend contracts) |
| `s23_law_coverage.py` | 10,175 | 1 | Dimension 29 — law-coverage accounting |
| `s24_declared_laws.py` | 18,922 | 5 | Dimension 30 — declared laws from source |

### `tests/` (4 source files)

| File | Bytes | Notes |
|---|---|---|
| `__init__.py` | 0 | Empty init |
| `fixtures.py` | 8,154 | Known-positive / known-negative benchmark sources |
| `run_tests.py` | 17,533 | Regression gate — each detector's polarity vs fixtures |

### `logs/` (43 files)

**Run metadata:**

| File | Bytes | Notes |
|---|---|---|
| `run.json` | 786 | Run metadata (run_id, commit, options, file_counts) |
| `checkpoint.json` | 255 | Phase final, files_processed=3806, pass 2, findings_written=1345 |

**Core output (JSONL):**

| File | Bytes | Lines | Notes |
|---|---|---|---|
| `findings.jsonl` | 1,540,171 | 1,345 | All emitted findings (NEW this run) |
| `verdicts.jsonl` | 546,102 | 1,345 | Adjudicated (1174 CONFIRMED, 164 UNVERIFIABLE, 7 ALREADY_FIXED) |
| `observations.jsonl` | 414,432 | — | Intermediate observations |
| `plan.json` | 1,099,468 | — | Compiled remediation plan (1193 steps) |
| `facts.json` | 718,335 | — | 116 measured aggregates (see §7.1) |
| `tool_ledger.json` | 385 | — | Tool runs (cmd, exit, duration, tail) |
| `recommendations.jsonl` | 17,710 | — | Non-gating recommendations |
| `verification_summary.json` | 9,631 | — | Adjudication metrics |

**Per-dimension logs (28 primary + 4 support = 32 dimension logs):**

| File | Bytes | Findings (from §7.2) |
|---|---|---|
| `01_architectural.jsonl` | 217,328 | 172 |
| `02_technological.jsonl` | 20,057 | 21 |
| `03_logical.jsonl` | 361,707 | 306 |
| `04_operational.jsonl` | 32,417 | 30 |
| `05_wiring.jsonl` | 13,828 | 13 |
| `06_database.jsonl` | 7,622 | 9 |
| `07_tables_fields.jsonl` | 296,073 | 266 |
| `08_providers.jsonl` | 6,985 | 8 |
| `09_laws.jsonl` | 22,254 | 26 |
| `10_migrations.jsonl` | 16,348 | 15 |
| `11_environmental.jsonl` | 18,429 | 15 |
| `12_tests.jsonl` | 39,171 | 36 |
| `13_dev_to_prod.jsonl` | 6,055 | 8 |
| `14_frontend_web.jsonl` | 236,130 | 216 |
| `15_frontend_mobile.jsonl` | 1,043 | 1 |
| `16_features.jsonl` | 5,846 | 5 |
| `17_code_file_management.jsonl` | 139,645 | 94 |
| `18_security.jsonl` | 14,160 | 12 |
| `19_performance.jsonl` | 2,277 | 3 |
| `20_observability_resilience.jsonl` | 4,106 | 5 |
| `21_contradictions.jsonl` | 4,852 | 5 |
| `22_anti_patterns.jsonl` | 4,697 | 5 |
| `23_code_intent.jsonl` | 2,401 | 3 |
| `23_law_coverage.jsonl` | 44,629 | 46 | **DEAD COPY — flagged for removal (§11.3)** |
| `24_browser_behavior.jsonl` | 1,238 | 1 |
| `25_ai_drift.jsonl` | 1,807 | 1 |
| `26_code_alignment.jsonl` | 8,530 | 7 |
| `27_project_completion_blockers.jsonl` | 3,622 | 4 |
| `28_supply_chain_security.jsonl` | 6,575 | 7 |
| `29_law_coverage.jsonl` | 43,527 | 45 | **Canonical law-coverage log** |
| `30_declared_laws.jsonl` | 11,778 | 14 |

**Recommendation (rec_*) dumps:**

| File | Bytes |
|---|---|
| `rec_automation.jsonl` | 6,785 |
| `rec_data.jsonl` | 3,922 |
| `rec_design.jsonl` | 785 |
| `rec_finance.jsonl` | 1,172 |
| `rec_frontend.jsonl` | 926 |
| `rec_ops.jsonl` | 806 |
| `rec_qa.jsonl` | 1,274 |
| `rec_workflow.jsonl` | 2,040 |

**Runtime probe artifacts (stale — from `--full` run):**

| File | Bytes | Notes |
|---|---|---|
| `runtime_results.json` | 171 | Browser probe results |
| `db_results.json` | 1,028 | DB introspection results |
| `load_results.json` | 232 | Load/latency probe results |
| `llm_results.json` | 261 | Ollama semantic review results |
| `http_probe.log` | 2,814 | Raw live HTTP probe log |
| `llm_cache.json` | 2 | Ollama cache (empty) |

**Keep file:**

| File | Bytes | Notes |
|---|---|---|
| `.gitkeep` | 0 | Keeps `logs/` directory in git |

### `__pycache__/` directories (all dead — see §11.1)

| Location | Count | Dead (no source) |
|---|---|---|
| `__pycache__/` (root) | 3 | 0 (`zozi_audit.py`, `zozi_compile.py`, `zozi_verify.py` exist) |
| `zz_core/__pycache__/` | 17 | **6** (`checklist`, `emit`, `lawroute`, `loop`, `rollup`, `summary`) |
| `zz_scanners/__pycache__/` | 26 | 0 (all 24 source `.py` + `__init__` + `preflight`) |
| `zz_integrations/__pycache__/` | 6 | 0 (all 5 source `.py` + `__init__`) |
| `tests/__pycache__/` | 3 | 0 (`fixtures.py`, `run_tests.py`, `__init__.py`) |
| **Total** | **55** | **6** |

---

**End of PLAN.md (v4).**
