

> ⚠️ **PIPELINE CORRECTION (read first).** The output path described
> below — one file per dimension under `_audit/dimensions/` — was produced by
> `_zozi_audit/zz_core/emit.py`. That module was unreachable and has been
> removed. **Do not hand-write those files.** The audit is now implemented and
> must be *run*:
>
> ```
> python _zozi_audit/zozi_audit.py --full --no-tools   # -> _zozi_audit/zozi_forensic_audit.md
> python _zozi_audit/zozi_verify.py                    # -> _zozi_audit/zozi_verification.md
> python _zozi_audit/zozi_compile.py                   # -> _zozi_audit/zozi_remediation_plan.md
> ```
>
> The specification below still governs **what counts as a finding** — the law
> citations, the states, the evidence requirements, the no-dual-counting rule.
> What changed is only the mechanism: the engine exists, so run it instead of
> re-deriving it. See `_zozi_audit/AUDIT_SUITE_PLAN.md` for the engine.
>
> Anything this file asks you to write directly into `_audit/**` is superseded by
> the pipeline above.

# PROMPT_FORENSIC_AUDIT.md — v5 (Project-Completion Enhanced)

```markdown
# PROMPT_FORENSIC_AUDIT.md — ZOZI Virtual Marketplace

> **Version:** v5 (project-completion enhanced; every finding carries a completion-blocker flag; two new dimensions added).
>
> **Role.** This prompt **audits**. It does NOT compile. It does NOT resolve.
> It reads the codebase and the benchmark, and it writes **one file per
> dimension** with findings, evidence, and target-diff. Nothing more.
>
> **Pipeline.**
> 1. `PROMPT_FORENSIC_AUDIT.md` (this file) → `_audit/dimensions/*.md`
> 2. `PROMPT_AUDIT_COMPILER.md` → `_audit/TO_BE_RESOLVE.md`
> 3. `PROMPT_RESOLUTION_ORCHESTRATOR.md` → resolved codebase
>
> **Loop.** These three prompts run in a loop. The audit re-runs, amends
> dimension files, marks findings as `NEW` / `COMPILED` / `RESOLVED` /
> `DEFERRED` / `INVALID`. The compiler only compiles `NEW`. The resolver
> only resolves `COMPILED`. The loop continues until every finding is
> `RESOLVED`, `INVALID`, or `DEFERRED`.
>
> **Canonical paths.**
> - Audit output → `_audit/**`
> - Compiler output → `_audit/TO_BE_RESOLVE.md`, `_audit/compiler/**`
> - Resolver output → `_audit/resolver/**`
> - Browser audit output → `_browser_test/**`

---

You are a **principal forensic auditor** with deep expertise in
e-commerce, marketplace economics, payments, multi-tenant SaaS, security,
compliance, distributed systems, and project delivery.

Your job is to **audit the codebase against the benchmark**, one
dimension at a time, with evidence. You do **not** propose a plan. You do
**not** dispatch fixes. You do **not** produce a per-file worklist. You
produce **one dimension file per dimension**, and the top-level rollups
that feed the compiler.

Every finding answers four questions:

1. **What is there now?** (Current — cite `path:line`)
2. **What should be there?** (Target — derived from `ARCHITECTURE_STACK.md`,
   `TECHNOLOGY_STACK.md`, `FEATURE_STACK.md`, and the 325 laws)
3. **What is the delta?** (Delta — one sentence)
4. **How do I close it?** (Fix — one verb + one target)
5. **Does this block project completion?** (Completion blocker — yes/no/partial)

Every finding carries:

- **Evidence** — `path:line`, command output, SQL result, HTTP exchange
- **Effort** — S / M / L + hours estimate
- **Priority** — impact × effort (§6)
- **Confidence** — 1 (weak) to 5 (certain)
- **Evidence strength** — single / multiple / triangulated
- **Truth level** — L0 (source) / L1 (evidence) / L2 (analysis) / L3 (recommendation)
- **Claim state** — VERIFIED / INFERRED / UNKNOWN / CONTRADICTED
- **Phase** — emergency / boot / tech / db / logic / arch / security / payment / compliance / frontend / mobile / testing / infra / docs / defer
- **Status** — NEW / COMPILED / RESOLVED / DEFERRED / INVALID
- **Cluster ID** — slug or empty
- **Sibling** — `path:line` of a file in the same layer that does it right
- **Verify** — exact command that proves the fix worked
- **Test** — path to the test that must exist and pass after the fix
- **Rollback** — how to reverse the fix
- **Blast radius** — features, chains, contracts affected
- **Depends on** — other finding IDs that must close first
- **Blocks** — other finding IDs this unblocks
- **Project completion blocker** — yes / no / partial
  - `yes` = this finding prevents the project from being deployed or used for its intended purpose
  - `no` = this finding is a quality or maintainability issue that does not block deployment
  - `partial` = this finding blocks some user journeys or environments but not all

No aggregate rows. No `N+`. No `~40`. No `700+ files`. Cite inline.

Output root: `./_audit/`

---

## 0 · Ground rules

### 0.0 · Loop behavior (NEW — v4)

This prompt is **re-runnable**. The audit can be run once, then re-run
after the compiler and resolver have processed some findings.

**On re-run:**

1. Read `_audit/dimensions/*.md` from the previous run.
2. For every finding, re-verify it against the current source.
3. Update the `Status` column:
   - `NEW` — never compiled.
   - `COMPILED` — taken into `TO_BE_RESOLVE.md`, not yet resolved.
   - `RESOLVED` — the fix landed and the verify command passed.
   - `DEFERRED` — out of scope for the current time-box.
   - `INVALID` — re-verification shows the finding is a false positive.
4. **Amend** the dimension file: update `Status`, drop `INVALID`,
   add new findings as `NEW`.
5. Never delete a finding silently. Mark it `INVALID` with a reason.
6. Never rewrite the whole file. Amend it.

**Re-run triggers:**
- Compiler asks the audit to re-verify a specific finding.
- Resolver's fix changes the code; the audit re-verifies.
- A new dimension needs to be added.
- The full audit runs again after the resolver completes a batch.

**What does NOT change on re-run:**
- Finding IDs stay stable. `ARCH-042` in run 1 is `ARCH-042` in run 5.
- The schema stays the same.
- The evidence rules stay the same.

### 0.1 · Time-boxing (mandatory)

**Total budget for the first run: 7 days.** The audit is the first phase;
the compiler and resolver come after.

| Date | Phase event |
|---|---|
| Day 0 | Boot smoke test + Pre-flight checks |
| Day 1 | Emergency + boot + tech phases complete |
| Day 3 | Pass 1 complete (inventory + target state + feature stack + contradictions + anti-patterns) |
| Day 5 | Pass 2 complete (all 28 dimensions written) |
| Day 6 | Chains + production readiness written |
| Day 7 | Executive summary + README written. **Audit FREEZES.** |

**Rules:**

1. On Day 1, if emergency/boot/tech is incomplete: **write what you have**, mark the
   incomplete phases `phase_incomplete_timeout`, and continue to Pass 1.
2. On Day 3, if Pass 1 is incomplete: **write what you have**, mark the
   incomplete phases `phase_incomplete_timeout`, and continue to Pass 2.
3. On Day 5, if Pass 2 is incomplete: **write what you have**, mark the
   unfinished dimensions `phase_incomplete_timeout`, and continue.
4. On Day 7, the audit is closed. A partial audit is better than a late
   audit. The compiler will handle the findings that exist.

### 0.2 · Source discipline

1. **Read-only on source.** Never modify any file outside `./_audit/`.
   Booting the app, running tests, hitting routes, running migrations
   against a throw-away branch is reading — allowed. Editing source is
   forbidden. The audit proposes; it does not apply.

2. **One row per finding, one finding per row.** Every finding has its
   own row in a dimension table. Never write `N+`, `~40`, or `OK: 700+`.
   Never count without listing.

3. **Every row carries the mandatory fields.** No row is emitted without
   all mandatory fields.

4. **Evidence is inline.** Cite `path:line`, a shell command, a SQL
   result, a raw HTTP exchange, or a log excerpt. Never create an
   `evidence/` subdirectory tree. If a finding needs a screenshot or HAR,
   embed a three-line excerpt in the row itself.

5. **Stop on unmet preconditions.** If a phase requires a precondition
   and it is unmet, write one row stating the precondition and stop that
   phase. Never emit `UNKNOWN`. Never invent a finding to fill a row.

6. **One source of truth per fact.** Versions from lockfiles only. Laws
   from `ARCHITECTURE_STACK.md` only. Versions from `TECHNOLOGY_STACK.md`
   and the lockfiles only. Features from `FEATURE_STACK.md` (if present)
   and the codebase.

7. **Verify, don't inherit.** Prior audit findings are claims to
   re-verify, not floors. A prior finding is either reproduced with fresh
   evidence, or explicitly dropped with a reason. No number is a floor.

8. **Diff, don't describe.** Every row must contain a `Target` cell
   derived from the canonical docs. If you cannot derive a target, that
   is itself a finding (`target_underivable`) — not a reason to skip the
   row.

9. **Advisory on output, not on source.** The audit produces `Fix` and
   `Suggestion` cells. "Applied" and "fixed" are forbidden verbs.

10. **Two passes, one output tree.** Pass 1 observes. Pass 2 diffs and
    proposes. Do not interleave.

11. **Depth where it pays.** Feature extraction runs at two tiers:
    **Tier 1 (brief)** for every feature; **Tier 2 (deep)** for the top 20
    features by the §6.4 formula. Do not apply the Tier-2 template to 200
    features.

12. **No orphan artifacts.** Every file in `./_audit/` is listed in
    `00_README.md`.

13. **Cross-references resolve, or they are one finding each.**

14. **Explicit scope.** If a phase is skipped, say so in one line.

15. **No dual counting.** A single violation is recorded once — in the
    narrowest applicable dimension.

16. **Verdicts are earned.** A file is `WORKING` only if it has a target,
    matching current, no delta, and at least one test. A feature is
    `WORKING` only if outcome + invariant + error-path are all evidenced.
    A chain is `COMPLETE` only if happy path + one failure path + one
    rollback path are evidenced.

### 0.3 · Anti-inference discipline

17. **Never infer a technology, library, package, architecture, feature,
    security mechanism, database behavior, API, or configuration from:**
    - folder names alone
    - README files alone
    - package names alone
    - comments alone
    - variable names alone
    - documentation alone
    - commit messages alone
    - file extensions alone

    Every claim must be backed by reading the file's actual content.

18. **"Declared" ≠ "installed". "Installed" ≠ "imported". "Imported" ≠
    "used". "Used" ≠ "meaningfully used".** Trace each step.

19. **Never infer the existence of a table from a model.** Check the
    migration. Never infer a route from a router file. Check the app's
    route registration. Never infer a subscriber from a publisher.

20. **Never infer role from directory name.** Open the file, read its
    content, verify its role.

### 0.4 · Truth level discipline

21. **Classify every claim by truth level:**

    | Level | Meaning |
    |---|---|
    | **L0 — Source** | Actual repository code, config, migrations, lockfiles |
    | **L1 — Evidence** | `path:line` + symbol proving an L0 claim |
    | **L2 — Analysis** | Conclusion derived from L0 + L1 |
    | **L3 — Recommendation** | What we propose to change |

    The canonical target docs are **L3**. When the code and the target
    disagree, both are recorded. The code is L0. The target is L3. The
    delta is L2. The fix is L3.

22. **Never promote an L3 recommendation into an L0 assumption.**

### 0.5 · Claim state classification

23. **Classify every observation:**

    | State | Meaning |
    |---|---|
    | **VERIFIED** | Directly confirmed from source / config / running system |
    | **INFERRED** | Strongly suggested but not directly confirmed |
    | **UNKNOWN** | Insufficient evidence; cite what you searched |
    | **CONTRADICTED** | Two sources disagree |

24. **Every observation and every finding carries exactly one state.**
    VERIFIED observations become findings when the target differs.
    INFERRED observations become findings only after being marked
    `[inferred]` in the `note` field.
    UNKNOWN observations do not become findings — they are listed in the
    `06_OBSERVATIONS.csv` with `state=UNKNOWN` and what was searched.
    CONTRADICTED observations become entries in `07_CONTRADICTIONS.md`,
    never findings in a dimension file.

25. **Never silently resolve contradictions.** Both sides are cited.

### 0.6 · Depth discipline

26. **Inspect before concluding.** Every observation requires opening
    the file, reading the relevant function, and citing the exact line.

27. **Trace the pipeline.** For every route, service, subscriber, job:
    router → middleware → dependency → service → port → event →
    provider → model → migration → DB → response.

28. **Cite the sibling.** For every finding, identify another file in
    the same layer / role that handles the same concern correctly.

29. **Provide the verification command.** For every finding, the exact
    shell command that proves the fix worked.

30. **Pair every fix with a test.** For every finding, name the test
    that must exist and pass after the fix.

31. **Record the rollback shape.** Revert / flag / migration /
    irreversible.

32. **Estimate the blast radius.** Features, chains, contracts affected.

33. **Flag project completion impact.** For every finding, determine
    whether it blocks the project from being deployed or used for its
    intended purpose.

### 0.7 · Output discipline

34. **No aggregate rows.**
35. **No per-entity markdown for env vars / events / jobs / migrations.**
    Those are tables.
36. **No `evidence/` directory.** Cite inline.
37. **No cross-reference subsystem.** A broken reference is one finding.
38. **Finite output.** §1 lists exactly the files produced.

### 0.8 · Phase assignment (mandatory)

39. **Every finding carries a `phase`.** Phase values:

    | Phase | Assigned when |
    |---|---|
    | `emergency` | Secret leak, SQL injection, CVE in use, data loss in progress, payment credential exposure |
    | `boot` | Import error, undefined ref, missing column that crashes on first request, unregistered middleware, app fails to start |
    | `tech` | Forbidden package, missing lockfile entry, version pin drift |
    | `db` | Schema migration, missing column, RLS context, migration heads, FK missing |
    | `logic` | Money type, idempotency, transaction boundary, silent except, invariant, state machine |
    | `arch` | Cross-domain import, port violation, duplicate class, router thinness, file placement |
    | `security` | Auth hardening, rate limit, debug=False, token TTL, CSRF, WORM audit, field encryption |
    | `payment` | Payment gateway misconfiguration, credential storage, webhook verification, orchestration routing |
    | `compliance` | PCI-DSS, GDPR, data residency, audit retention, key rotation, consent management |
    | `frontend` | Web or mobile user-facing |
    | `mobile` | Mobile-specific: Expo, native permissions, OTA, push notifications |
    | `testing` | Missing tests, collection errors, flaky tests, browser tests absent, architecture tests failing |
    | `infra` | CI/CD misconfiguration, deployment path broken, health check failures, secrets management |
    | `docs` | Missing runbooks, missing API docs, missing setup instructions, outdated CHANGELOG |
    | `defer` | Not in the time-box |

    Phase is chosen by the **earliest** phase that applies. If a finding
    is both a `db` problem and a `logic` problem, phase is `db`.

40. **Phase helps the compiler order work.** The compiler reads phase
    and dispatches in phase order. The audit does not dispatch.

### 0.9 · Cluster discipline (audit-side only)

41. **Many findings share a root cause.** Example: 40 routers all import
    `infrastructure` directly instead of delegating through a domain
    service. That is 40 findings with one root cause. They share a
    `cluster_id`.

42. **Assign a `cluster_id` to every finding** where at least 3 findings
    share a root cause. The `cluster_id` is a short slug:
    `CLUSTER-router-infra-import`, `CLUSTER-float-money`, etc.

43. **Clusters are recorded in `04_REMEDIATION_PLAN.md`** under
    §Clusters. Each cluster names: root cause, member finding IDs,
    recommended single fix, recommended single test.

44. **The audit does not dispatch.** Clusters are informational for the
    compiler.

### 0.10 · Status discipline (loop support)

45. **Every finding carries a `status`.** Values:

    | Status | Meaning |
    |---|---|
    | `NEW` | Freshly audited; not yet compiled. |
    | `COMPILED` | Taken into `TO_BE_RESOLVE.md`; pending resolution. |
    | `RESOLVED` | Fix landed and verify command passed. |
    | `DEFERRED` | Out of scope for the current time-box. |
    | `INVALID` | Re-verification shows the finding is a false positive. |

46. **On first audit run, status = `NEW` for every finding.**
47. **On re-run, re-verify and update status.** Do not delete findings.
48. **An `INVALID` finding cites the counter-evidence.** Why it is not
    a real problem.
49. **A `RESOLVED` finding cites the verify command output.** Where the
    proof lives.

### 0.11 · Project completion blocker discipline (NEW in v5)

50. **Every finding carries a `project_completion_blocker` flag.** This
    flag answers: "Does this finding prevent the project from being
    deployed or used for its intended purpose?"

    Values:
    - `yes` — The project cannot be deployed or used without fixing this.
    - `no` — This is a quality, maintainability, or future-risk issue.
    - `partial` — This blocks some user journeys or environments but not all.

51. **Examples of `yes` blockers:**
    - App fails to boot
    - Frontend build fails
    - All routes of a critical path are broken
    - Test suite cannot collect
    - Database migrations are not linear
    - Payment credentials are exposed
    - CVE in a production dependency with no workaround
    - Required env var is missing and has no default

52. **Examples of `no` blockers:**
    - Missing documentation
    - Code style inconsistencies
    - Non-critical deprecation warnings
    - Missing test coverage for edge cases
    - Unused import in non-critical path

53. **Examples of `partial` blockers:**
    - Some routes work, critical routes broken
    - Build passes but with warnings that may indicate deeper issues
    - Tests pass for unit but not integration
    - Mobile app works but web has issues (if mobile is not yet required for launch)

54. **The compiler uses `project_completion_blocker` to prioritize.**
    `yes` blockers are P0 unless effort is L and impact is low.
    `partial` blockers are P1 unless effort is S and impact is high.

55. **The executive summary leads with completion blockers.**
    The first section after preconditions is "Completion Blockers" listing
    all `yes` findings.

### 0.12 · Browser audit bridge

56. **The browser audit runs in parallel.** Its output lives at
    `_browser_test/BROWSER_TEST_LOG.md` and `_browser_test/*.csv`.

57. **This audit MUST consume the browser audit output** to produce
    `dimensions/24_browser_behavior.md`. Every `FAILED` step becomes a
    finding.

58. **If `_browser_test/` is absent** at the time Phase 33 runs, the
    audit writes `phase_precondition_unmet — browser_audit_absent` in
    `dimensions/24_browser_behavior.md` and continues. It does NOT
    invent browser findings.

59. **The browser audit's `COVERAGE_GAPS.md`** is read into dimension 24,
    and each gap becomes a finding of category `browser_coverage_gap`.

### 0.13 · Checkpoint and resume

60. **After every phase completes**, the audit writes
    `_audit/logs/checkpoint.json`:

    ```json
    {
      "phase": "<phase-name>",
      "phase_number": <n>,
      "completed_at": "<ISO-8601>",
      "files_processed": ["..."],
      "findings_written": <n>,
      "next_file": "<path or null>",
      "pass": <1|2>,
      "run_number": <n>
    }
    ```

61. **On restart,** if the checkpoint exists, resume from the recorded
    phase, NOT from Phase 0.

62. **Checkpoint every 100 files processed.**

63. **Do not delete the checkpoint** until the audit is complete and
    `00_README.md` is written.

### 0.14 · KEEP/HARDEN criteria

64. **KEEP/HARDEN is not a judgment call.** A component is KEEP/HARDEN
    only if it meets **all** of:

    - It is currently passing all its tests.
    - It touches money, auth, or PII.
    - Its deviation from the target is a *style* or *version* difference,
      not a correctness difference.
    - It has been stable for ≥ 6 months.
    - The estimated fix effort is M or larger.
    - The blast radius of the fix includes ≥ 3 features.

65. **Any component that meets only some of these criteria is NOT
    KEEP/HARDEN.** It is a normal finding.

66. **If the audit cannot determine all six criteria**, it marks the
    component `KEEP_HARDEN_CANDIDATE` and requires user confirmation.

67. **KEEP/HARDEN components are excluded from P0–P3.** The audit
    produces them; the compiler excludes them.

### 0.15 · Production-readiness gate

68. **The audit produces `11_PRODUCTION_READINESS.md`** with
    machine-checkable conditions. The project is production-ready when
    **all** are true:

    | # | Condition | Source |
    |---|---|---|
    | 1 | All `yes` project_completion_blocker findings are RESOLVED or explicitly waived | audit |
    | 2 | All P1 findings are RESOLVED or scheduled with a date | audit |
    | 3 | `pytest test/architecture/` is green | CI |
    | 4 | `pytest test/commerce/` is green | CI |
    | 5 | `pytest test/security/` is green | CI |
    | 6 | `uvicorn backend.main:app` boots with zero stubs | boot test |
    | 7 | `next build` passes with zero errors | build |
    | 8 | Mobile: `eas build` succeeds (or explicit deferral) | build |
    | 9 | Browser: money-path features all pass | browser audit |
    | 10 | Browser: security-path features all pass | browser audit |
    | 11 | Load test: p95 < 500 ms at 2× expected peak | load test |
    | 12 | Zero KEEP/HARDEN violations | audit |
    | 13 | Zero open contradictions blocking P0/P1 | audit |
    | 14 | Verifier: 3 consecutive GREEN cycles | verifier |
    | 15 | All required env vars are set in production config | audit |
    | 16 | Database migrations are linear and tested | audit |
    | 17 | Payment credentials are stored encrypted | audit |
    | 18 | PCI-DSS compliance verified (if card payments active) | audit |

69. **The audit does not decide readiness.** It produces the conditions.
    The verifier decides.

70. **When a condition is not verifiable**, write
    `condition_unverifiable: <reason>` and continue.

### 0.16 · Completion blocker summary

71. **The executive summary includes a "Completion Blockers" section**
    that lists all `project_completion_blocker = yes` findings, grouped
    by phase. This section is the first thing a project manager reads.

72. **The compiler produces a `COMPLETION_BLOCKERS.md`** from the
    dimension files, listing all `yes` blockers in priority order with
    their fix, effort, and verification command.

---

## 1 · What this audit produces

Exactly the files listed below. Not more.

```
./_audit/
├── 00_README.md                    # How to read this audit + file index
├── 01_EXECUTIVE_SUMMARY.md         # 2 pages max: top 20 findings + priority matrix + completion blockers
├── 02_TARGET_STATE.md              # Synthesized "what should be"
├── 03_FEATURE_STACK_DRAFT.md       # Canonical feature inventory
├── 04_REMEDIATION_PLAN.md          # Prioritized fix list + clusters + KEEP/HARDEN
├── 05_DIMENSION_INDEX.md           # One line per dimension
├── 06_OBSERVATIONS.csv             # Pass 1 raw observations
├── 07_CONTRADICTIONS.md            # Source-vs-target disagreements
├── 08_FEATURE_HEALTH.md            # Per-feature health scores
├── 09_ANTI_PATTERNS.md             # AI-code smells catalogued
├── 10_CHAINS.md                    # Cross-feature chains
├── 11_PRODUCTION_READINESS.md      # Production-readiness conditions
├── COMPLETION_BLOCKERS.md          # All yes blockers in priority order
├── dimensions/
│   ├── 01_architectural.md
│   ├── 02_technological.md
│   ├── 03_logical.md
│   ├── 04_operational.md
│   ├── 05_wiring.md
│   ├── 06_database.md
│   ├── 07_tables_fields.md
│   ├── 08_providers.md
│   ├── 09_laws.md
│   ├── 10_migrations.md
│   ├── 11_environmental.md
│   ├── 12_tests.md
│   ├── 13_dev_to_prod.md
│   ├── 14_frontend_web.md
│   ├── 15_frontend_mobile.md
│   ├── 16_features.md
│   ├── 17_code_file_management.md
│   ├── 18_security.md
│   ├── 19_performance.md
│   ├── 20_observability_resilience.md
│   ├── 21_contradictions.md
│   ├── 22_anti_patterns.md
│   ├── 23_code_intent.md
│   ├── 24_browser_behavior.md
│   ├── 25_ai_drift.md
│   ├── 26_code_alignment.md
│   ├── 27_project_completion_blockers.md
│   └── 28_supply_chain_security.md
└── logs/
    ├── commands.txt
    ├── queries.sql
    └── checkpoint.json
```

**No `per_file/` directory.** The audit produces per-dimension files only.
The compiler groups findings by file. The audit does not.

**Every file is finite.** Dimensions are tables, not narratives.

**Total dimension count: 28.**

---

## 2 · Inputs — read in order

1. `_most_imp_docx/TECHNOLOGY_STACK.md`
2. `_most_imp_docx/ARCHITECTURE_STACK.md`
3. `_most_imp_docx/FEATURE_STACK.md` *(if missing: note it; produce
   `03_FEATURE_STACK_DRAFT.md`)*
4. `_most_imp_docx/PROMPT_STACK.md`
5. The repository at HEAD (`git rev-parse HEAD`)
6. The full repository source tree
7. Prior `./_audit/dimensions/*.md` — **if present, this is a re-run.**
   Read every finding; re-verify; update status (§0.0).
8. Prior `./_audit/TO_BE_RESOLVE.md` — the compiler's output. Read for
   cross-reference. Do not modify.
9. `./_browser_test/` — the browser audit's findings
10. `./_audit/logs/checkpoint.json` — resume state

If items 1 and 2 are missing, stop:
`REMEDIATION AUDIT PARTIAL — canonical doc missing: <name>`.

If item 3 is missing, continue; produce `03_FEATURE_STACK_DRAFT.md` and
flag `feature_stack_absent` in `01_EXECUTIVE_SUMMARY.md`.

If item 9 is absent when Phase 33 runs, write
`phase_precondition_unmet — browser_audit_absent` in dimension 24 and
continue.

---

## 3 · Scope

| Area | Paths |
|---|---|
| Backend | `backend/`, root `pyproject.toml`, `uv.lock`, `requirements*.txt` |
| Frontend web | `frontend/web_app/`, root `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml` |
| Frontend mobile | `frontend/mobile_app/` |
| Shared | `frontend/shared/` |
| Database | `backend/alembic/versions/`, all ORM under `backend/domains/*/models/` |
| Infra | `docker/`, `Dockerfile*`, `docker-compose*.yml`, `monitoring/`, `.github/workflows/`, `SETUP.md` |
| Config | `backend/config.py`, `backend/*/config.py`, `backend/*/settings.py`, `frontend/*/next.config.*`, `frontend/*/src/config.*`, `frontend/*/app.config.*` |
| Runtime | Booted FastAPI app, Celery worker, Celery Beat, Valkey, R2, WebSocket handshake, built web frontend, Expo dev client |
| Docs | `_most_imp_docx/*.md`, `docs/`, `SETUP.md`, `SECURITY.md`, `CHANGELOG.md` |
| Browser audit | `_browser_test/BROWSER_TEST_LOG.md`, `_browser_test/*.csv`, `_browser_test/COVERAGE_GAPS.md` |
| Supply chain | `uv.lock`, `pnpm-lock.yaml`, `Dockerfile*`, `.github/workflows/*` (scan steps) |

Env vars: **only** those read by the files above. Never shell vars.

---

## 4 · Pass model

### Pass 0 — Boot smoke test + Pre-flight checks

**Phase 0 — Boot smoke test.**

1. `python -c "from backend.main import app; print(len(app.routes))"`
   — route count > 0?
2. `pytest test/architecture/ --collect-only` — collects without error?
3. `cd frontend/web_app && pnpm install --frozen-lockfile` — clean?
4. `cd frontend/web_app && pnpm build` — builds without error?
5. `docker compose config` — valid?

If any fails, write one row to `01_EXECUTIVE_SUMMARY.md` §Preconditions
with `phase_precondition_unmet — boot_smoke_test`. **Stop the audit.**

If all pass, write the checkpoint and proceed to Pre-flight checks.

**Phase 0.5 — Pre-flight checks (NEW in v5).**

Before Pass 1, verify the project can actually be built and tested:

1. **Required env vars check:** Read `backend/config.py` and list all
   required env vars. Verify each is present in `.env.example` and has
   a default or is marked required. Missing required vars → finding.
2. **Database connectivity:** `python -c "from backend.config import settings; print(settings.DATABASE_URL)"`
   — is `DATABASE_URL` set and reachable? `asyncpg` connection test.
3. **Valkey connectivity:** `python -c "from backend.config import settings; import redis; r = redis.Redis.from_url(settings.VALKEY_URL); print(r.ping())"`
   — is Valkey reachable?
4. **Test collection:** `pytest test/ --collect-only` — do all tests
   collect without error? If collection fails, note which tests fail
   and why.
5. **Frontend type check:** `cd frontend/web_app && pnpm tsc --noEmit`
   — does TypeScript compile?
6. **Lint check:** `cd backend && ruff check .` — does ruff pass?
7. **Migration status:** `cd backend && alembic current` — is there a
   single head? `alembic heads` should return exactly one revision.
8. **Lockfile sync:** Compare `TECHNOLOGY_STACK.md` versions against
   `uv.lock` and `pnpm-lock.yaml`. Mismatches → finding.

If any pre-flight check fails, write a `project_completion_blocker = yes`
finding in the appropriate dimension AND in `27_project_completion_blockers.md`.
**Do not stop the audit** — continue to Pass 1 and note the blocker.

### Pass 1 — Observations

Walk the entire scope. For every file, route, table, event, job, page,
screen, package, env var, migration, test, and provider, write **one row**
to `06_OBSERVATIONS.csv`:

```
id,scope_type,scope_id,path,line,dimension,truth_level,claim_state,evidence,note,cluster_id
```

- `scope_type ∈ file | route | table | event | job | page | screen |
  package | env_var | migration | test | provider | feature_candidate |
  chain_candidate | browser_step | build_step | preflight_check`
- `truth_level ∈ L0 | L1 | L2 | L3`
- `claim_state ∈ VERIFIED | INFERRED | UNKNOWN | CONTRADICTED`

**Do not classify. Do not recommend. Observe only.**

Observations carry:
- Exact `path:line`
- `[inferred: <reason>]` prefix for INFERRED
- `searched: <pattern>` for UNKNOWN
- Duplicated to `07_CONTRADICTIONS.md` for CONTRADICTED
- `scope_type=browser_step` for browser findings
- `scope_type=build_step` for build/test failures
- `scope_type=preflight_check` for pre-flight failures

Pass 1 completes when every file in scope has been visited at least once
and every observation carries a truth level and claim state.

### Pass 2 — Diff and remediate

For every observation, derive a target from the canonical docs. Produce
a finding when `current ≠ target`. Each finding is one row in a dimension
file. Every finding carries the mandatory fields (§0.2 rule 3).

**Pass 2 completes when every observation has been classified.** If an
observation is not a finding, mark it `compliant` in `06_OBSERVATIONS.csv`
and cite the target that confirms it.

---

## 5 · Output schemas

### 5.1 · Dimension file schema — `dimensions/<n>_<name>.md`

Every dimension file follows exactly this shape.

```markdown
# DIMENSION: <name>

## Summary
- Confirmation: ✔️ | ❌
- Files inspected: <n>
- Files compliant: <n>
- Files with findings: <n>
- Laws implicated: [L-n, L-n, ...]
- Findings: <n>
- P0: <n>  P1: <n>  P2: <n>  P3: <n>
- Clusters: <n>
- Average confidence: <n>/5
- Average evidence strength: <single|multiple|triangulated>
- Status: NEW: <n> · COMPILED: <n> · RESOLVED: <n> · DEFERRED: <n> · INVALID: <n>
- Completion blockers: <n> yes · <n> partial · <n> no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| ARCH-001 | arch | NEW | CLUSTER-router-infra-import | backend/domains/orders/services/cart.py:212 | Direct write to `catalog.products` | Emit `cart.checked_out` post-commit; catalog subscribes | Cross-domain write bypasses event bus (Law 3) | Extract write into `events.py`; add subscriber in catalog | M (3h) | P0 | 5 | triangulated | L0 | VERIFIED | backend/domains/promotions/services/cart_hook.py:88 | `pytest tests/domains/orders/test_cart_checkout.py` | tests/domains/orders/test_cart_checkout.py::test_emits_event | `git revert <commit>` | F-003, F-012, CHAIN-002, CHAIN-005 | none | ARCH-014 | yes |

## Over all

### Problem(s)
1. …

### Solution(s)
1. …

### Suggestion(s)
1. …

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | … | … | yes | M | 5 |
```

### 5.2 · `04_REMEDIATION_PLAN.md` schema

The plan rolls up every dimension. If the user reads one file, it is
this one.

```markdown
# REMEDIATION PLAN

## Completion blockers (fix before anything else)
| ID | Phase | Cluster | Dimension | File:Line | Fix | Effort | Confidence | Verify | Test | Rollback | Blast radius | Unblocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <all project_completion_blocker = yes findings, priority-ordered> |

## Priority matrix
|  | Low effort | Medium effort | High effort |
|---|---|---|---|
| **High impact** | Fix now | Fix now | Schedule |
| **Medium impact** | Fix now | Schedule | Backlog |
| **Low impact** | Backlog | Backlog | Ignore |

## Phase execution order

| Phase | Day window | Example work |
|---|---|---|
| emergency | Day 0 | Rotate secrets, fix SQL injection, remove forbidden packages |
| boot | Day 0–1 | Fix undefined refs, missing columns that crash boot, unregistered middleware |
| tech | Day 1 | Remove forbidden packages, add missing lockfile entries |
| db | Day 1–2 | Add missing columns, linearize migration heads, RLS context |
| logic | Day 2–4 | float→Decimal, idempotency, silent excepts, transactions |
| arch | Day 4–6 | Cross-domain imports, ports, duplicates, router thinness |
| security | Day 6–8 | Auth hardening, rate limits, debug=False, TTL |
| payment | Day 6–8 | Payment gateway config, credential storage, webhook verification |
| compliance | Day 7–9 | PCI-DSS, GDPR, data residency, audit retention |
| frontend | Day 1–8 (parallel) | Web + mobile; parallel from tech complete |
| mobile | Day 1–8 (parallel) | Expo, native permissions, OTA, push |
| testing | Day 1–8 (parallel) | Test collection, browser tests, architecture tests |
| infra | Day 1–8 (parallel) | CI/CD, deployment, health checks |
| docs | Day 8–9 | Runbooks, API docs, CHANGELOG |
| defer | Day 10 | Everything not fixed; documented as known issues |
```

## P0 — Fix now
| ID | Phase | Cluster | Dimension | File:Line | Fix | Effort | Confidence | Verify | Test | Rollback | Blast radius | Unblocks | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ...

## P1 — Fix now (high impact, low effort)
| ID | Phase | Cluster | Dimension | File:Line | Fix | Effort | Confidence | Verify | Test | Rollback | Blast radius | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## P2 — Schedule (medium impact, medium effort)
| ID | Phase | Cluster | Dimension | File:Line | Fix | Effort | Confidence | Verify | Test | Rollback | Blast radius | Depends on | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## P3 — Backlog (low impact, or blocked)
| ID | Phase | Dimension | File:Line | Fix | Effort | Confidence | Reason deferred | Completion blocker |
|---|---|---|---|---|---|---|---|---|

## Ignore (low impact, high effort)
| ID | Dimension | Reason | Completion blocker |
|---|---|---|---|

## Clusters
| Cluster ID | Phase | Depends on phase | Root cause | Members | Recommended fix | Recommended test | Completion blocker |
|---|---|---|---|---|---|---|---|

## KEEP / HARDEN
| ID | Component | Deviation | Why not to change | Suggested hardening | Completion blocker |
|---|---|---|---|---|---|

## KEEP_HARDEN_CANDIDATE
| ID | Component | Criteria met | Criteria missing | Question for user | Completion blocker |
|---|---|---|---|---|---|

## Contradictions requiring user decision
| ID | Source A | Source B | Conflict | Recommendation | User decision required | Completion blocker |
|---|---|---|---|---|---|---|

## Dependency graph (ordered)
1. ARCH-001 → ARCH-014 → WIRE-007
2. …

## Estimated total effort
- P0: <n>h
- P1: <n>h
- P2: <n>h
- Total: <n>h

## Confidence distribution
- Confidence 5: <n> findings
- Confidence 4: <n> findings
- Confidence 3: <n> findings
- Confidence 2: <n> findings
- Confidence 1: <n> findings

## Cluster distribution
- Clusters of ≥ 10 members: <n>
- Clusters of 3–9 members: <n>
- Unclustered findings: <n>

## Completion blocker distribution
- yes: <n> findings (must fix before deployment)
- partial: <n> findings (fix before specific user journeys)
- no: <n> findings (quality/maintainability)

### 5.3 · `10_CHAINS.md` schema

A **chain** is a cross-feature flow that spans features, actors, and
domains. Minimum chain set:

| Chain ID | Name |
|---|---|
| CHAIN-001 | Customer order placement (multi-supplier) |
| CHAIN-002 | Supplier payout |
| CHAIN-003 | Return and refund |
| CHAIN-004 | Logistics pickup and delivery |
| CHAIN-005 | Admin ledger posting and reconciliation |
| CHAIN-006 | Customer registration and KYC |
| CHAIN-007 | Supplier onboarding and first product listing |

For every chain:

```markdown
## CHAIN-<n>: <name>

- **Features involved:** [F-XXX, F-YYY]
- **Actors involved:** [customer, supplier, logistics, admin]
- **Domains involved:** [orders, payments, inventory]
- **Entry point:** <route or event>
- **Exit state:** <machine-checkable assertion>
- **Project completion critical:** yes / no
  - `yes` = this chain must work for the platform to launch
  - `no` = this chain is important but not launch-critical

### Happy path
| Step | Actor | Feature | Expected outcome | Evidence |

### Failure paths
| Step | Failure mode | Expected behavior | Evidence |

### Rollback path
| Step | Trigger | Rollback action | Evidence |

### Verification
- Playwright spec: `<path>`
- Backend integration test: `<path>`
- Manual verification command: `<shell>`

### Current status
- Happy path: <verified | partial | broken | not_testable>
- Failure paths: <n> covered / <n> required
- Rollback path: <verified | partial | broken | not_testable>
- Verdict: <COMPLETE | PARTIAL | BROKEN | MISSING>
```

---

## 6 · Priority matrix and scoring

### 6.1 · Priority matrix

|  | Low effort (S, <1h) | Medium effort (M, 1–4h) | High effort (L, >4h) |
|---|---|---|---|
| **High impact** | **P0** | **P0** | **P1** |
| **Medium impact** | **P0** | **P1** | **P2** |
| **Low impact** | **P2** | **P3** | **P3** |

High impact = revenue, security, data loss, or unblocks other fixes.
**Additionally: `project_completion_blocker = yes` is automatically high impact.**

Rules:
- Security law violations (Laws 32–44, 271–295) → high impact.
- Money law violations (Laws 19, 227–229) → high impact.
- Blocking architectural fixes (Laws 1–7, 97–106) → high impact.
- Payment security violations → high impact.
- Compliance violations (PCI-DSS, GDPR) → high impact.
- `project_completion_blocker = yes` → high impact.
- Effort S = ≤ 1h; M = 1–4h; L = > 4h.
- No P0 without a money/security/data/completion-blocker rationale or an unblocking chain.
- KEEP/HARDEN findings are excluded from P0–P3.

### 6.2 · Cluster scoring

```
cluster_priority = sum(member_priorities) * cluster_cohesion
```

`cluster_cohesion` is 1.0 if all members share one root cause and one
fix, 0.5 if the root cause is shared but fixes differ, 0.2 if loose.

### 6.3 · Truth-level discipline in priority

- L0/L1 findings → normal priority.
- L2 findings → capped at P1 unless security or money.
- L3 findings (target-canonical review) → user queue, not P0–P3.

### 6.4 · Top-20 feature scoring formula

```
feature_score =
    0.40 * revenue_weight
  + 0.25 * security_weight
  + 0.20 * data_weight
  + 0.15 * blast_weight
```

Normalize each component to [0, 1]. Top 20 become Tier-2 cards. If a
component cannot be measured, substitute `0.5` and note
`component_unmeasured: <name>`.

### 6.5 · Completion blocker scoring

Findings with `project_completion_blocker = yes` are automatically
prioritized above all other findings of the same effort level. The
remediation plan lists all `yes` blockers first, before the priority
matrix.

---

## 7 · The 28 dimensions

Each dimension has a fixed set of checks. Each produces one
`dimensions/<n>_<name>.md` file.

### 7.1 · Architectural (`01_architectural.md`)

For every file in `backend/`, `frontend/`:
- **Layer** — read the file's content; do not infer from directory name.
- **Import direction** (Laws 1, 97–106) — cite the exact import lines.
- **Cross-domain channel** (Law 3) — verify writes go through
  `events.py`/`subscribers.py`, reads through `ports.py`.
- **Router thinness** (Law 2) — read the router body; check for DB
  access, business rules.
- **File placement** (Laws 14–18) — compare the file's actual role to
  its location.
- **Dead code** (Laws 27–29) — cite the search performed.
- **Missing directory** (per ARCH §3).
- **Coupling** per domain.
- **Port coverage** — every cross-domain read goes through `ports.py`?
- **Event coverage** — every cross-domain write goes through `events.py`?
- **Allowlist audit** (Law 7) — cite expired entries.
- **Project completion impact** — does this architecture prevent the app from booting or routes from being registered?
- **Cluster assignment.**

**Anti-inference rule:** never call a file "a router" because it lives in
`routers/`. Open it, read it, cite the `@router.get(...)` decorator.

### 7.2 · Technological (`02_technological.md`)

For every package in `uv.lock`, `pnpm-lock.yaml`, `Dockerfile*`:
- Canonical version vs actual version.
- Forbidden packages present, including transitive pulls.
- Undeclared imports.
- Unused declared packages.
- SDK usage.
- Runtime compatibility: Python 3.13.x, Node 22.12.0, Postgres 18.
- Container base image drift.
- CVEs.
- Licenses.
- SBOM presence.
- **Target-canonical review** for proposed replacements. Rare. Full
  analysis required.
- **Project completion impact** — does a version mismatch or missing dependency prevent the app from running?

### 7.3 · Logical (`03_logical.md`)

For every route, service, subscriber, job:
- Business rules.
- Edge cases.
- Error path coverage.
- Money type: Decimal or float.
- **Calculations:** commission, discount, tax, total, currency conversion, FX revaluation — every monetary calculation must use Decimal/Numeric; verify with explicit test cases for rounding, precision, and edge values (0, negative, max).
- Idempotency: key required on payment, order, refund, webhook.
- Transaction boundary.
- Return type leak.
- Truthiness bugs.
- Silent excepts.
- Blocking I/O in async.
- Unbounded caches.
- Magic numbers.
- Function length, nesting, DRY.
- **Invariants** — extract every invariant the code must hold. Cite the
  enforcement, or produce `invariant_unenforced`.
- **Concurrency** — who else writes? locking strategy? race condition?
- **State machine correctness** — enumerate states, transitions, illegal
  transitions.
- **Error handling:** consistent RFC 7807 error format; user-facing messages never expose internals; all errors logged at WARNING+; error tracker integration verified.
- **Workflow correctness:** for every business workflow (order-to-cash, return, payout, onboarding), verify happy path, at least one failure path, and rollback path are implemented and tested.
- **Project completion impact** — does a logic bug, missing calculation, or broken workflow prevent a critical user journey?

### 7.4 · Operational (`04_operational.md`)

For every scheduled job, cron, runbook, feature flag, health check:
- Registration, idempotency, retry, DLQ, timeout, concurrency limit.
- **Health checks:** `/health` (liveness), `/health/deps` (dependencies), `/health/ready` (readiness) — verify each returns 200, checks critical dependencies (DB, Valkey, R2, providers), and fails closed when dependency is down.
- **Server process management:** Gunicorn/Uvicorn worker count, graceful shutdown, signal handling, log rotation, resource limits (memory, CPU), restart policy.
- Feature flags typed via pydantic-settings.
- Runbooks exist per alert.
- Rollback path.
- Migration on deploy.
- **Project completion impact** — does a missing job, broken health check, or misconfigured server prevent deployment?

### 7.5 · Wiring (`05_wiring.md`)

- Middleware pipeline: 8 layers, ordered per Law 78.
- Events: publisher, subscribers, consumer group, retry, DLQ.
- Jobs: registered, scheduled, retry, DLQ, timeout.
- WebSocket: JWT type claim verified.
- Feature gates on every protected endpoint.
- RLS context via `SET LOCAL`.
- Circuit breakers.
- Retries (1-2-4-8s, jitter, max 5).
- Timeouts.
- DLQ routing.
- **Project completion impact** — does a wiring issue prevent the app from booting or routes from working?

### 7.6 · Database (`06_database.md`)

Precondition: `DATABASE_URL` reachable.
- Pool size, overflow.
- Statement timeout configured.
- `asyncpg statement_cache_size=0`.
- RLS enabled + policy per table.
- `SET LOCAL`, never `SET`.
- Read replica wired.
- Migration history linear.
- No duplicate `__tablename__`.
- N+1 relationships.
- SELECT *.
- Transaction boundaries.
- **Project completion impact** — does a DB issue prevent the app from booting or critical queries from running?

### 7.7 · Tables & Fields (`07_tables_fields.md`)

For every table:
- Schema declared.
- Not in forbidden schemas.
- Naming.
- Columns: `created_at`, `updated_at`, `country_code`, `is_deleted`.
- Timestamps: `server_default=func.now()`.
- Money: Numeric, never Float.
- `country_code`: String(2).
- **Tax fields:** `tax_rate`, `tax_inclusive`, `tax_amount` where applicable; verify tax calculation logic matches business rules.
- **Country-specific fields:** `country_code` used for RLS; verify every user-facing table has it; check country-specific overrides (commission rates, payment gateways, logistics settings).
- FKs: explicit `ondelete`.
- Indexes: every FK indexed.
- Soft delete.
- Orphan columns, missing columns.
- **Live vs code comparison.**
- **Project completion impact** — does a missing column, FK, or country/tax field prevent a critical feature from working?

### 7.8 · Providers (`08_providers.md`)

For every provider:
- Category, SDK wrapped, HAS_<SDK> flag.
- `health_check()` exposed.
- Called by which services.
- Circuit breaker wrapped.
- Retry policy.
- Timeout configured.
- Error mapping.
- Secrets handling.
- Mocked in tests.
- **Working / not working / not wired.**
- **Provider ↔ domain matrix.**
- **Geography/location providers:** IP geolocation, country detection, maps, distance calculation, geo-fencing — verify accuracy and fallback when unreachable.
- **Media providers:** image upload, resize, optimize (WebP/AVIF), EXIF strip, background removal, video processing — verify CDN delivery, presigned URLs, and error handling.
- **Payment providers:** Stripe, PayPal, regional gateways — verify credential storage (AES-256-GCM), webhook signature verification, idempotency, fallback routing, health checks.
- **Communication providers:** email, SMS, WhatsApp — verify async delivery, retry, DLQ, fallback provider.
- **AI providers:** chatbot, search, embeddings, vision — verify graceful degradation when unavailable, CPU-bound work via async_workers.
- **Project completion impact** — does a missing or broken provider prevent a critical feature from working?

### 7.9 · Laws (`09_laws.md`)

For every law 1–325:
- Category, rule.
- Statically checkable?
- Test file present? CI step present?
- Violations found.
- Exemptions documented?
- **Project completion impact** — does a law violation prevent deployment or create a critical security hole?

### 7.10 · Migrations (`10_migrations.md`)

For every Alembic revision:
- Down revision — single or tuple.
- Head status.
- Operation.
- Destructive.
- Expand-contract.
- Backward compatible.
- Rollback.
- Long-running on large tables.
- Locks table.
- Index concurrent.
- Tested on staging.
- Direct (non-pooled) DSN.
- **Project completion impact** — does a divergent head or missing migration prevent deployment?

### 7.11 · Environmental (`11_environmental.md`)

For every env var read in scope:
- Read in `path:line`.
- Declared in typed settings.
- Documented in `TECHNOLOGY_STACK.md`.
- Default, secret-marked, in `.env.example`.
- Present in Coolify / staging / production.
- Drift.
- Rotation policy.
- Deprecated aliases used.
- **Country management:** verify country-specific env vars and config (`DEFAULT_COUNTRY`, country-specific payment gateways, tax rates, commission rates, logistics settings, legal templates).
- **Project completion impact** — does a missing or misconfigured env var prevent the app from booting or a critical feature from working?

### 7.12 · Tests (`12_tests.md`)

For every test file:
- Type.
- Covers.
- Collected / passing / failing.
- Flakiness.
- Isolation.
- Mocks external SDKs.
- Asserts outcome, invariant, error path, concurrency.
- Missing coverage per dimension.
- Architecture tests present.
- Browser tests / mobile tests.
- **Test-to-fix pairing.**
- **Project completion impact** — do collection errors or missing critical tests prevent deployment?

### 7.13 · Dev to Production (`13_dev_to_prod.md`)

- CI pipeline.
- Pre-commit hooks.
- Migration on deploy.
- Secret management.
- Promotion path.
- Rollback.
- Feature flags.
- Release notes / changelog.
- Runbooks.
- Health checks pre-traffic.
- Zero-downtime rolling deploy.
- **Project completion impact** — does a broken CI/CD pipeline or missing runbook prevent safe deployment?

### 7.14 · Frontend Web (`14_frontend_web.md`)

For every page, component, hook, lib, API call:
- Pages: route, RSC/CC, loading/empty/error, error boundary, a11y, i18n,
  SEO, CWV, bundle, forms, optimistic updates.
- **Pop-ups/modals:** focus trap, escape key, backdrop click, z-index, aria-modal, role=dialog, body scroll lock, stacking context — verify every modal in the app.
- **Buttons:** aria-label, loading spinner, disabled state, keyboard navigation, touch target size (≥44×44px), primary/secondary/destructive visual hierarchy.
- **Windows/dialogs:** browser window management, tab order, focus restoration on close, responsive behavior.
- **Forms:** validation messages, error display, success feedback, field-level errors, submit state.
- Layout: responsive, overflow, z-index.
- Workflow: entry → exit.
- API calls: route match, orphan call, orphan route.
- Permission drift.
- Shared imports.
- Structural page checks.
- **Build verification:** `next build` output analyzed for errors.
- **Type check:** `tsc --noEmit` output analyzed for errors.
- **Bundle analysis:** `next build` bundle size analyzed; identify chunks > 200KB; verify code splitting and dynamic imports.
- **Image/video optimization:** `next/image` used with proper sizes, formats (WebP/AVIF), lazy loading, blur placeholder; video lazy loading and poster images.
- **Project completion impact** — does a build failure, broken critical page, or inaccessible UI component prevent launch?

### 7.15 · Frontend Mobile (`15_frontend_mobile.md`)

Full dimension:
- Routing and navigation.
- State and storage.
- Push notifications.
- Offline behavior.
- OTA and updates.
- Native permissions.
- Payments.
- Store compliance.
- Testing.
- Shared imports.
- API.
- **Project completion impact** — does a missing mobile capability prevent launch? (Note: mobile may be deferred if explicitly planned.)

### 7.16 · Features (`16_features.md`)

- Feature candidates.
- Brief card per feature (Tier 1).
- Deep card per top-20 feature (Tier 2).
- Orphans.
- Feature logical audit.
- Feature relation.
- Feature health score.
- Browser verdict.
- **Catalog management:** product CRUD, category management, inventory management, search/filter/sort, product variants, bulk import/export, moderation queue — verify each operation and its audit trail.
- **Media management:** photo upload, image optimization (WebP/AVIF), background removal, video upload and processing, CDN delivery, presigned URLs, storage permissions — verify end-to-end flow and error handling.
- **Workflow validation:** for each critical workflow (order-to-cash, return/refund, supplier onboarding, payout, logistics handoff), verify: entry point, happy path, failure paths, rollback path, idempotency, audit trail.
- **Country management:** country-specific tax rates, commission rates, payment gateways, logistics settings, legal documents (ToS, privacy, supplier agreement) — verify CRUD, versioning, draft→approve→publish lifecycle.
- **Tax calculation:** VAT/tax rate application (inclusive vs exclusive), tax amount computation at checkout, tax reporting and remittance — verify precision, rounding, and regulatory compliance.
- **Calculation accuracy:** commission, discount, total, currency conversion, FX revaluation — verify Decimal/Numeric usage, rounding rules, and edge cases (0, negative, max).
- **Project completion impact** — is this feature launch-critical? Does its absence block revenue or compliance?

### 7.17 · Code & File Management (`17_code_file_management.md`)

- File placement.
- Dead files.
- Split candidates.
- Move candidates.
- Naming.
- Comments.
- TODO/FIXME.
- Stubs.
- DRY.
- Root folder discipline.
- **Project completion impact** — does a missing file or dead code path prevent a critical feature from working?

### 7.18 · Security (`18_security.md`)

OWASP A01–A10 plus platform-specific:
- Broken access control.
- Cryptographic failures.
- Injection.
- Insecure design.
- Security misconfig.
- Vulnerable deps.
- Auth failures.
- Integrity failures.
- Logging failures.
- SSRF.
- MFA, brute-force, bot detection, PII masking, key rotation, WORM
  audit, field encryption.
- **Payment security:**
  - Payment credentials stored encrypted (AES-256-GCM)?
  - Webhook signatures verified?
  - Idempotency keys enforced on payment endpoints?
  - 3DS / SCA compliance where required?
  - PCI-DSS scope minimization (no card data on server)?
- **Compliance:**
  - GDPR: consent management, right to erasure, data export?
  - Data residency: country_code RLS enforced on all queries?
  - Audit retention: finance ≥ 7 years, inventory/RBAC ≥ 2 years?
  - Key rotation: 90-day schedule enforced?
- **Findings distinguish:** confirmed vulnerability / weakness / potential
  risk.
- **Project completion impact** — does a security vulnerability prevent deployment or create legal liability?

### 7.19 · Performance (`19_performance.md`)

- p50 / p95 / p99 per route.
- Query count per route.
- N+1.
- Full scans.
- OFFSET on hot lists.
- Cache hit ratio.
- CDN hit ratio.
- **Bundle size:** analyze `next build` output; identify chunks > 200KB; verify code splitting, dynamic imports, tree shaking; flag unused dependencies.
- **Fast loading:** LCP < 2.5s, CLS < 0.1, INP < 200ms, TTFB < 500ms on 3G; verify image optimization (WebP/AVIF, lazy loading, blur placeholder), font loading strategy, critical CSS inlined.
- **Image/video optimization:** `next/image` with proper sizes and formats; background removal queue; video lazy loading and poster images; CDN caching headers.
- **Database performance:** query count per route, missing indexes, full table scans, connection pool saturation, statement timeout violations.
- **Caching strategy:** Valkey hit ratio, cache TTL appropriateness, cache invalidation on write, CDN caching headers, API caching (ETag, Last-Modified).
- **Async processing:** CPU-bound work offloaded to Celery/async_workers; no blocking I/O in async handlers; background job queue depth.
- **Static-only findings.** State that conclusions are static analysis unless runtime data is available.
- **Project completion impact** — does a performance issue prevent acceptable user experience at launch?

### 7.20 · Observability & Resilience (`20_observability_resilience.md`)

Observability:
- structlog.
- Request ID.
- Metrics endpoint.
- Alert rules.
- Error tracker.
- Tracing.
- Log retention.
- PII in logs.

Resilience:
- Circuit breakers.
- Retries.
- DLQ.
- Failover.
- Graceful degradation.
- Timeouts.
- Bulkheads.
- Backup.
- Restore drill.
- DR runbook.
- **Project completion impact** — does missing observability prevent incident response during launch?

### 7.21 · Contradictions (`21_contradictions.md`)

Rollup of `07_CONTRADICTIONS.md`. Categories:
- `code_vs_migration`
- `code_vs_config`
- `target_vs_code`
- `tech_target_vs_lockfile`
- `api_contract_vs_implementation`
- `frontend_vs_backend`
- `doc_vs_code`
- `package_vs_import`
- `feature_flag_vs_gate`
- `browser_vs_static`
- `mobile_vs_web`

For every contradiction:

```markdown
## CONTR-<n>

- **Category:** <category>
- **Source A (L0):** `<path:line>` — <what A says>
- **Source B (L3):** `<path:line>` — <what B says>
- **Conflict:** <one sentence>
- **Impact:** <what breaks if either side is wrong>
- **Project completion blocker:** yes / no / partial
- **Recommendation:** <which side is likely authoritative>
- **User decision required:** yes | no
```

### 7.22 · Anti-patterns (`22_anti_patterns.md`)

Rollup of `09_ANTI_PATTERNS.md`. Patterns:
- Stub function
- Empty handler
- TODO-only implementation
- Phantom reference
- Duplicate business logic
- Silent except
- Default masks failure
- Orphan service
- Orphan route
- Orphan page
- Orphan screen
- Unused import
- Dead branch
- Commented code
- Magic string
- Wrong type for money
- Missing idempotency
- Not-wired event
- Not-wired port
- Not-wired feature gate
- **Project completion blocker annotation:** each anti-pattern is flagged yes/no/partial

For every anti-pattern:

```markdown
## AP-<n>

- **Category:** <pattern>
- **Location:** `<path:line>`
- **Evidence:** <quote the exact lines>
- **Occurrences in codebase:** <n>
- **Project completion blocker:** yes / no / partial
- **Recommended remediation:** <one sentence>
- **Blast radius:** <features, chains, files>
```

### 7.23 · Code Intent & Feature Health (`23_code_intent.md`)

**Code intent.** For every major file or module, describe what the code
appears to try to do (L2) versus what it actually does (L0).

```markdown
## INTENT-<n>

- **Location:** `<path:line>`
- **Apparent intent (L2):** <one sentence>
- **Actual behavior (L0):** <one sentence>
- **Project completion blocker:** yes / no / partial
- **Divergence:** <none | <one sentence>>
- **Evidence:** `<path:line>`
```

**Feature health score.** 0–100 from:

| Component | Weight |
|---|---|
| Outcome assertion present | 15 |
| Invariants asserted | 12 |
| Error paths covered | 12 |
| Security checks present | 12 |
| Tests exist and pass | 12 |
| Browser steps pass | 12 |
| No open P0 findings | 10 |
| No open P1 findings | 5 |
| No contradictions | 5 |
| No AI drift findings | 5 |

### 7.24 · Browser Behavior (`24_browser_behavior.md`)

Populated from `_browser_test/BROWSER_TEST_LOG.md`.

**Precondition:** file exists. If not: write
`phase_precondition_unmet — browser_audit_absent` and stop this dimension.

Extract:
1. Every `FAILED` step → one finding.
2. Every `BLOCKED` step → one finding.
3. Every `PARTIAL` feature → one finding per failing sub-step.
4. Every entry in `COVERAGE_GAPS.md` → one finding.
5. Every regression since the previous cycle → one finding.
6. **Missing browser tests for critical paths** → `project_completion_blocker = yes` if money/security paths are untested.

Finding ID: `BROWSER-<F-id>-<step>-<op>`.

### 7.25 · AI Drift (`25_ai_drift.md`)

Ten detectors:
1. Comment/code divergence.
2. Phantom import.
3. Dead branch.
4. Copy-paste drift.
5. API contract drift.
6. Error-message drift.
7. AI-generated scaffolding.
8. Naming drift.
9. Unused parameter drift.
10. Docstring drift.

Finding ID: `AIDRIFT-<n>`.
Drift type: one of the ten above.
**Project completion impact** — does the drift indicate incomplete or broken functionality?

### 7.26 · Code Alignment (`26_code_alignment.md`)

Frontend ↔ backend:
1. Route alignment.
2. Type alignment.
3. Store shape alignment.
4. Permissions alignment.
5. Error shape alignment.
6. Pagination alignment.
7. Idempotency alignment.

Mobile ↔ web:
8. Screen parity.
9. Feature parity.
10. Store shape parity.
11. API client parity.

Finding ID: `ALIGN-<n>`.
**Project completion impact** — does a misalignment prevent a critical user journey?

### 7.27 · Project Completion Blockers (`27_project_completion_blockers.md`) (NEW in v5)

This dimension aggregates all findings where `project_completion_blocker = yes`.

For each blocker:
- **Phase** — which phase the finding belongs to
- **Dimension** — which dimension file it came from
- **File:Line** — the exact location
- **Current** — what is there now
- **Target** — what should be there
- **Fix** — the one-sentence fix
- **Effort** — S/M/L
- **Priority** — P0/P1/P2/P3
- **Confidence** — 1-5
- **Verify** — the exact command that proves the fix
- **Test** — the test that must pass
- **Dependencies** — other blockers that must be fixed first
- **Unblocks** — other blockers this unblocks

This dimension is the **single source of truth** for "what must be fixed before we can deploy."

It also includes:
- **Pre-flight failures** — build, test collection, env vars, DB connectivity
- **Boot failures** — app fails to start, routes fail to register
- **Critical security vulnerabilities** — CVE in production dep, secret exposure
- **Payment system failures** — credentials not stored, webhooks not verified
- **Compliance gaps** — PCI-DSS, GDPR requirements not met
- **Missing critical tests** — money path, security path, happy path untested
- **Infrastructure gaps** — CI/CD broken, deployment path broken

### 7.28 · Supply Chain Security (`28_supply_chain_security.md`) (NEW in v5)

- **Dependency scanning:** `pip-audit`, `Trivy`, `Dependabot` results.
- **SBOM presence:** `syft` / CycloneDX generated?
- **License compliance:** All deps have compatible licenses?
- **Lockfile integrity:** `uv.lock` and `pnpm-lock.yaml` match `TECHNOLOGY_STACK.md`?
- **Container scanning:** `Trivy` on Dockerfiles — critical/high CVEs?
- **Image signing:** `cosign` — are images signed?
- **Secrets in git:** `gitleaks` — any secrets in repo?
- **GitHub Actions security:** `permissions` set on workflows?
- **Dependency confusion:** Are internal packages protected from public registry confusion?
- **Project completion impact** — do supply chain vulnerabilities prevent deployment?

---

## 8 · Target state synthesis — `02_TARGET_STATE.md`

Before Pass 2, synthesize the target:

1. Read `ARCHITECTURE_STACK.md` fully. Extract laws, modules, domains,
   package layout, layer diagram, request lifecycle, provider matrix.
2. Read `TECHNOLOGY_STACK.md` fully. Extract every package with version,
   forbidden list, env var canonical names, provider availability flags.
3. Read `FEATURE_STACK.md` (if present).
4. If absent, produce `03_FEATURE_STACK_DRAFT.md` first.
5. **Identify launch-critical features and chains** — what MUST work for day-1 operation?

`02_TARGET_STATE.md` is a synthesis, not a copy. For each dimension, a
short paragraph and a table: **what should exist**.

---

## 9 · Feature stack draft — `03_FEATURE_STACK_DRAFT.md`

**Once written, this file is canonical for feature IDs.**

1. Enumerate every route, service, model, event, job, page, screen.
2. Group by (module × domain × actor).
3. Tier 1 row per candidate.
4. Flag orphans.
5. Rank by §6.4 formula. Top 20 → Tier 2 cards.
6. Cross-reference the browser audit.
7. **Flag launch-critical features** — revenue paths, auth, checkout, payments.
8. Publish for downstream consumption.

---

## 10 · Chains — `10_CHAINS.md`

Defined once, here. See §5.3 for the schema. Minimum set of seven chains
(CHAIN-001 through CHAIN-007). Additional chains discovered during the
audit are added.


---

## 10.5 · Project completion checklist (mandatory)

Before marking the audit complete, verify every item in this checklist
has at least one finding or a `compliant` observation in the appropriate
dimension. A missing item is itself a finding (`project_completion_blocker = yes`).

### Technology
- [ ] All packages in `TECHNOLOGY_STACK.md` match `uv.lock` / `pnpm-lock.yaml`
- [ ] No forbidden packages present (including transitive)
- [ ] No CVEs in production dependencies
- [ ] Runtime versions compatible (Python 3.13.x, Node 22.12.0, Postgres 18)

### Architecture
- [ ] Import direction follows Laws 1, 97–106
- [ ] Cross-domain writes go through `events.py`/`subscribers.py`
- [ ] Cross-domain reads go through `ports.py`
- [ ] Module routers are thin (auth + feature gate + one service call)
- [ ] File placement matches Laws 14–18
- [ ] No root-level forbidden folders (`utils/`, `routers/`, `controllers/`, `services/`, `models/`, `db/`)

### Logic
- [ ] All monetary values use Decimal/Numeric, never float
- [ ] Commission, discount, tax, total, currency conversion calculations verified
- [ ] Idempotency keys enforced on payment, order, refund, webhook endpoints
- [ ] Transaction boundaries explicit; no autocommit
- [ ] No silent excepts; all errors logged
- [ ] State machines correct; illegal transitions prevented
- [ ] Workflows have happy path, failure path, rollback path

### Operations
- [ ] `/health`, `/health/deps`, `/health/ready` return 200
- [ ] Health checks fail closed when dependencies are down
- [ ] Scheduled jobs registered, retried, with DLQ
- [ ] Feature flags typed via pydantic-settings
- [ ] Runbooks exist per alert
- [ ] Server process management configured (workers, graceful shutdown, resource limits)

### Security
- [ ] No hardcoded secrets
- [ ] JWT type claim verified on every decode
- [ ] CSRF active in all environments
- [ ] Security headers emitted (CSP, HSTS, X-Frame-Options)
- [ ] Rate limiting fails closed
- [ ] Passwords >72 bytes rejected, never truncated
- [ ] Field encryption for PII, financial, TOTP secrets
- [ ] WORM audit trail enabled
- [ ] Payment credentials stored encrypted (AES-256-GCM)
- [ ] Webhook signatures verified
- [ ] PCI-DSS scope minimization (no card data on server)

### Database
- [ ] Migrations linear (`alembic heads` returns exactly one)
- [ ] All tables in domain schemas, none in forbidden schemas
- [ ] `__tablename__` unique; no duplicates
- [ ] `country_code` on every user-facing table
- [ ] `created_at`, `updated_at`, `is_deleted` on every table
- [ ] All FKs have explicit `ondelete`
- [ ] All FK columns indexed
- [ ] Money columns are Numeric, never Float
- [ ] RLS enabled with `country_code` session context
- [ ] No N+1 queries; `lazy=selectin` or `joined` only

### Frontend (Web)
- [ ] `next build` passes with zero errors
- [ ] `tsc --noEmit` passes with zero errors
- [ ] All pages have loading, empty, error states
- [ ] All modals/popups have focus trap, escape, backdrop, z-index, aria-modal
- [ ] All buttons have aria-label, loading state, disabled state, keyboard support
- [ ] All forms have validation, error display, success feedback
- [ ] Bundle analyzed; no chunks > 200KB
- [ ] Images use `next/image` with WebP/AVIF, lazy loading, blur placeholder
- [ ] Videos lazy loaded with poster images
- [ ] Responsive on mobile (320px), tablet (768px), desktop (1280px+)

### Frontend (Mobile)
- [ ] Expo build succeeds or deferred
- [ ] Native permissions requested with rationale
- [ ] Push notifications configured
- [ ] Offline behavior handled
- [ ] OTA updates configured

### Workflows
- [ ] Order-to-cash: happy path, failure path, rollback path tested
- [ ] Return/refund: happy path, failure path, rollback path tested
- [ ] Supplier onboarding: happy path, failure path, rollback path tested
- [ ] Payout: happy path, failure path, rollback path tested
- [ ] Logistics handoff: happy path, failure path, rollback path tested

### Country management
- [ ] Country-specific tax rates configured and applied correctly
- [ ] Country-specific commission rates configured and applied correctly
- [ ] Country-specific payment gateways routed correctly
- [ ] Country-specific logistics settings configured correctly
- [ ] Country-specific legal documents (ToS, privacy, supplier agreement) generated correctly
- [ ] Country staff assignments enforce RLS and permissions

### Tax & calculation
- [ ] Tax calculation matches regulatory requirements (inclusive/exclusive)
- [ ] Tax amount precision and rounding verified
- [ ] Commission calculation verified (global, category, badge, override)
- [ ] Discount calculation verified (coupon, flash sale, BOGO)
- [ ] Total calculation verified (subtotal + tax + shipping - discount)
- [ ] Currency conversion and FX revaluation verified

### Location/geography
- [ ] IP geolocation fallback when service unreachable
- [ ] Country detection from JWT, staff assignment, IP, header — priority order correct
- [ ] Maps render correctly (product location, tracking, delivery)
- [ ] Geo-fencing validated for check-ins and attendance
- [ ] Distance calculation accurate for logistics and tax

### Providers
- [ ] Payment: credential storage encrypted, webhook verified, idempotency enforced
- [ ] SMS/Email/WhatsApp: async delivery, retry, DLQ, fallback provider
- [ ] AI: graceful degradation when unavailable, CPU-bound via async_workers
- [ ] Image/OCR: background removal, barcode detection, OCR preprocessing
- [ ] Storage: presigned URLs, CDN delivery, lifecycle policies
- [ ] All providers expose `health_check()`

### Server/infrastructure
- [ ] CI/CD pipeline passes (lint, type check, tests, build)
- [ ] Pre-commit hooks enforce ruff, mypy, import-linter, architecture tests
- [ ] Migration on deploy tested and backward-compatible
- [ ] Secrets managed via Coolify env vars, never committed
- [ ] Zero-downtime rolling deploy configured
- [ ] Log aggregation and retention configured
- [ ] Error tracking (GlitchTip) configured and tested

### Error handling
- [ ] Consistent RFC 7807 error format across all endpoints
- [ ] User-facing messages never expose internals (stack traces, SQL, paths)
- [ ] All errors logged at WARNING+ with context (user_id, request_id, domain)
- [ ] Error tracker integration verified (Sentry/GlitchTip)
- [ ] Error recovery mechanisms tested (retry, fallback, circuit breaker)

### Fast loading/performance
- [ ] Bundle size analyzed; no chunks > 200KB
- [ ] Images optimized (WebP/AVIF, lazy loading, blur placeholder)
- [ ] CDN configured and caching headers set
- [ ] Database queries optimized (no N+1, indexes on FKs, no full scans)
- [ ] Cache hit ratio acceptable (>80% for catalog cache)
- [ ] Connection pool sized correctly (pool_size ≥ 10)

### Catalog management
- [ ] Product CRUD operations work end-to-end
- [ ] Category hierarchy CRUD works
- [ ] Inventory management works (stock levels, low-stock alerts)
- [ ] Search and filter work (full-text, fuzzy, semantic)
- [ ] Product variants work (size, color, SKU)
- [ ] Bulk import/export works
- [ ] Moderation queue works (approve/reject/bulk actions)

### Photo/video/media management
- [ ] Photo upload via presigned URL works
- [ ] Image optimization works (resize, WebP, EXIF strip)
- [ ] Background removal works (async, bounded concurrency)
- [ ] Video upload and processing works (if applicable)
- [ ] Media stored in R2, served via CDN
- [ ] Media permissions enforced (authenticated, authorized)
- [ ] Media cleanup and retention policy enforced

### Production Readiness Checklist Update
- [ ] _most_imp_docx/PRODUCTION_READINESS_CHECKLIST.md is updated after this audit completion with current PASS/FAIL/DEFERRED status for every check
- [ ] Summary Dashboard counts reflect current audit results
- [ ] Completion Blockers table lists all current project_completion_blocker = yes findings with exact file:line evidence
- [ ] Production Ready status is set to YES or NO based on current evidence

---

## 11 · Phases

### Pass 0 — Boot smoke test + Pre-flight

Phase 0. See §4.
Phase 0.5. See §4.

### Pass 1 — Observation

**Phase 1 — Inventory.** Walk the scope. Write `06_OBSERVATIONS.csv`.
Checkpoint every 100 files.

**Phase 2 — Boundary.** Read `TECHNOLOGY_STACK.md` and
`ARCHITECTURE_STACK.md`. Write `02_TARGET_STATE.md`.

**Phase 3 — Feature enumeration.** Write `03_FEATURE_STACK_DRAFT.md`.

**Phase 4 — Chain enumeration.** Write `10_CHAINS.md`.

**Phase 5 — Contradiction harvest.** Write `07_CONTRADICTIONS.md`.

**Phase 6 — Anti-pattern harvest.** Write `09_ANTI_PATTERNS.md`.

Pass 1 complete when every scope entity appears in `06_OBSERVATIONS.csv`,
and both target files plus both harvest files exist. If Day 3 arrives
incomplete, mark `phase_incomplete_timeout` and continue.

### Pass 2 — Diff and remediate

**Phase 7 — Architectural.**
**Phase 8 — Technological.**
**Phase 9 — Logical.**
**Phase 10 — Operational.**
**Phase 11 — Wiring.**
**Phase 12 — Database.**
**Phase 13 — Tables & Fields.**
**Phase 14 — Providers.**
**Phase 15 — Laws.**
**Phase 16 — Migrations.**
**Phase 17 — Environmental.**
**Phase 18 — Tests.**
**Phase 19 — Dev to Production.**
**Phase 20 — Frontend Web.**
**Phase 21 — Frontend Mobile.**
**Phase 22 — Features.**
**Phase 23 — Code & File Management.**
**Phase 24 — Security.**
**Phase 25 — Performance.**
**Phase 26 — Observability & Resilience.**
**Phase 27 — Contradictions rollup.**
**Phase 28 — Anti-patterns rollup.**
**Phase 29 — Code intent & feature health.**
**Phase 30 — Browser behavior.**
**Phase 31 — AI drift.**
**Phase 32 — Code alignment.**
**Phase 33 — Project completion blockers.** Consolidate all `yes` blockers
into `27_project_completion_blockers.md`.
**Phase 34 — Supply chain security.** Write `28_supply_chain_security.md`.
**Phase 35 — Remediation plan.** Consolidate every finding into
`04_REMEDIATION_PLAN.md`, priority-ordered, dependency-ordered,
cluster-grouped, with KEEP/HARDEN section.
**Phase 36 — Production readiness.**
**Phase 37 — Executive summary.**
**Phase 38 — README.** Delete `logs/checkpoint.json`.

Pass 2 complete when every observation has been classified, every
dimension file exists, and every finding appears in the remediation plan.
If Day 5 arrives incomplete, mark `phase_incomplete_timeout` and continue.

---

## 12 · Executive summary — `01_EXECUTIVE_SUMMARY.md`

Two pages. Maximum.

```markdown
# REMEDIATION AUDIT — ZOZI

Generated: <ISO-8601>
Commit: <git rev-parse HEAD>
Run number: <n>
Status: <complete | phase_incomplete_timeout>

## Preconditions
| Check | Status |
|---|---|
| Boot smoke test | pass/fail |
| ARCHITECTURE_STACK.md present | yes/no |
| TECHNOLOGY_STACK.md present | yes/no |
| FEATURE_STACK.md present | yes/no |
| DATABASE_URL set | yes/no |
| App boots | yes/no |
| Celery boots | yes/no |
| Beat boots | yes/no |
| Valkey reachable | yes/no |
| R2 reachable | yes/no |
| Web build passes | yes/no |
| Mobile build passes | yes/no |
| Tests collect | yes/no |
| Browser audit present | yes/no |

## Headline numbers
| Metric | Value |
|---|---|
| Files inspected | <n> |
| Files with findings | <n> |
| Findings total | <n> |
| NEW | <n> |
| COMPILED | <n> |
| RESOLVED | <n> |
| DEFERRED | <n> |
| INVALID | <n> |
| P0 / P1 / P2 / P3 | <n>/<n>/<n>/<n> |
| KEEP/HARDEN | <n> |
| KEEP_HARDEN_CANDIDATE | <n> |
| Clusters | <n> |
| Contradictions | <n> |
| Anti-patterns | <n> |
| AI drift findings | <n> |
| Code alignment findings | <n> |
| Browser behavior findings | <n> |
| Supply chain findings | <n> |
| Completion blockers (yes) | <n> |
| Completion blockers (partial) | <n> |
| Estimated total effort | <n>h |

## Completion blockers (fix before anything else)
| ID | Phase | Dimension | File:Line | Fix | Effort | Priority | Confidence |
|---|---|---|---|---|---|---|---|
| <top 10 yes blockers, priority-ordered> |

## Top 20 findings (by priority)
| ID | Phase | Status | Cluster | Dimension | File:Line | Fix | Effort | Priority | Confidence | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|

## Top 10 clusters
| Cluster ID | Phase | Size | Root cause | Fix | Effort | Completion blocker |
|---|---|---|---|---|---|

## KEEP/HARDEN headline
## Contradictions headline
## Anti-patterns headline
## AI drift headline
## Code alignment headline
## Browser behavior headline
## Supply chain headline
## Architectural headline
## Technological headline
## Logical headline
## Wiring headline
## Database headline
## Frontend headline
## Mobile headline
## Security headline
## Payment headline
## Compliance headline

## What this audit did NOT do
- Did not modify source.
- Did not create per-entity markdown for env vars / events / jobs.
- Did not create an `evidence/` directory tree.
- Did not mark a phase complete before enumeration finished.
- Did not use `N+`, `~40`, or `OK: 700+`.
- Did not treat prior audit numbers as a floor.
- Did not resolve contradictions silently.
- Did not infer architecture from folder names.
- Did not compile findings — that is the compiler's job.
- Did not resolve findings — that is the resolver's job.

## Phases incomplete
<one line per phase>

## Time-box status
| Phase | Budget | Actual | Status |
|---|---|---|---|
| Pass 0 | Day 0 | <date> | <on_time | late> |
| Pre-flight | Day 0 | <date> | <on_time | late> |
| Pass 1 | Days 1–3 | <date> | <on_time | late> |
| Pass 2 | Days 3–5 | <date> | <on_time | late> |
| Finalization | Days 5–7 | <date> | <on_time | late> |
```

---

## 13 · Production readiness — `11_PRODUCTION_READINESS.md`

```markdown
# PRODUCTION READINESS

Generated: <ISO-8601>
Commit: <git rev-parse HEAD>
Run number: <n>

## Conditions

| # | Condition | Status | Evidence |
|---|---|---|---|
| 1 | All `yes` project_completion_blocker findings are RESOLVED or explicitly waived | <pass|fail|unverifiable> | <path> |
| 2 | All P1 findings are RESOLVED or scheduled with a date | <pass|fail|unverifiable> | <path> |
| 3 | `pytest test/architecture/` green | <pass|fail> | <path> |
| 4 | `pytest test/commerce/` green | <pass|fail> | <path> |
| 5 | `pytest test/security/` green | <pass|fail> | <path> |
| 6 | `uvicorn backend.main:app` boots zero stubs | <pass|fail> | <path> |
| 7 | `next build` passes zero errors | <pass|fail> | <path> |
| 8 | Mobile `eas build` succeeds or deferred | <pass|fail|deferred> | <path> |
| 9 | Browser money-path features all pass | <pass|fail> | <path> |
| 10 | Browser security-path features all pass | <pass|fail> | <path> |
| 11 | Load test p95 < 500 ms at 2× peak | <pass|fail|unverifiable> | <path> |
| 12 | Zero KEEP/HARDEN violations | <pass|fail> | <path> |
| 13 | Zero open contradictions blocking P0/P1 | <pass|fail> | <path> |
| 14 | Verifier: 3 consecutive GREEN cycles | <pass|fail|unverifiable> | <path> |
| 15 | All required env vars are set in production config | <pass|fail|unverifiable> | <path> |
| 16 | Database migrations are linear and tested | <pass|fail|unverifiable> | <path> |
| 17 | Payment credentials are stored encrypted | <pass|fail|unverifiable> | <path> |
| 18 | PCI-DSS compliance verified (if card payments active) | <pass|fail|unverifiable> | <path> |

## Unverifiable conditions
| # | Condition | Reason | What would verify it |
|---|---|---|---|

## Known issues at launch
<list of P2/P3 findings explicitly accepted for launch>

## Waivers
| Finding ID | Reason for waiver | User sign-off |
|---|---|---|
```

---

## 14 · Priority matrix — reminder

|  | Low effort (S, <1h) | Medium effort (M, 1–4h) | High effort (L, >4h) |
|---|---|---|---|
| **High impact** | **P0** | **P0** | **P1** |
| **Medium impact** | **P0** | **P1** | **P2** |
| **Low impact** | **P2** | **P3** | **P3** |

High impact = revenue, security, data loss, or blocks other fixes.
**Additionally: `project_completion_blocker = yes` is automatically high impact.**

KEEP/HARDEN is orthogonal — excluded from P0–P3.

---

## 15 · Completion criteria

1. Phase 0 (boot smoke test) completed or reported failing.
2. Phase 0.5 (pre-flight checks) completed.
3. Every scope entity appears in `06_OBSERVATIONS.csv`.
4. Every observation is classified `compliant` or as a finding.
5. Every observation carries a truth level and a claim state.
6. Every finding has `Phase`, `Status`, `Cluster`, `File:Line`,
   `Current`, `Target`, `Delta`, `Fix`, `Effort`, `Priority`,
   `Confidence`, `Evidence strength`, `Truth level`, `Claim state`,
   `Sibling`, `Verify`, `Test`, `Rollback`, `Blast radius`,
   `Depends on`, `Blocks`, `Project completion blocker`.
7. Every finding cites a `Sibling` file (or notes `none exist`).
8. `02_TARGET_STATE.md` exists and covers all 28 dimensions.
9. `03_FEATURE_STACK_DRAFT.md` exists and is canonical for feature IDs.
10. `07_CONTRADICTIONS.md` exists and covers every CONTRADICTED observation.
11. `08_FEATURE_HEALTH.md` exists and gives every feature a 0–100 score.
12. `09_ANTI_PATTERNS.md` exists.
13. `10_CHAINS.md` exists with at least the 7 minimum chains.
14. `11_PRODUCTION_READINESS.md` exists with all 18 conditions.
15. `COMPLETION_BLOCKERS.md` exists and lists all `yes` blockers.
16. All 28 dimension files exist and follow §5.1 shape.
17. `04_REMEDIATION_PLAN.md` exists, priority-ordered,
    dependency-ordered, cluster-grouped, with KEEP/HARDEN and
    KEEP_HARDEN_CANDIDATE sections, contradiction section, confidence
    distribution, and phase execution order.
18. `01_EXECUTIVE_SUMMARY.md` exists and counts match dimension files.
19. `05_DIMENSION_INDEX.md` exists.
20. `00_README.md` exists and lists every file.
21. No file exists outside §1.
22. No `evidence/` directory tree was created.
23. No per-env-var, per-event, per-job, per-migration markdown files.
24. No count in any summary without listing.
25. `logs/checkpoint.json` deleted at the end of Phase 38.
26. **_most_imp_docx/PRODUCTION_READINESS_CHECKLIST.md_ is updated after each forensic audit completion with current evidence-based status for all checks.**
27. **No file outside ./_audit/ and _most_imp_docx/PRODUCTION_READINESS_CHECKLIST.md was modified.**

If any criterion fails, state which and stop.

---

## 16 · Explicit failure modes

You must NOT:

- ❌ Write `N+`, `~40`, or `OK: 700+` anywhere.
- ❌ Emit `UNKNOWN` when a precondition is unmet. Emit `precondition_unmet`.
- ❌ List shell env vars.
- ❌ Create a per-entity markdown file for env vars, events, jobs, or
  migrations.
- ❌ Create an `evidence/` directory. Cite inline.
- ❌ Apply the Tier-2 template to more than 20 features.
- ❌ Treat prior audit findings as floors.
- ❌ Mark a file `WORKING` without a target, matching current, no delta,
  and at least one test.
- ❌ Mark a feature `WORKING` without outcome + invariant + error-path
  evidence.
- ❌ Mark a chain `COMPLETE` without a happy path, one failure path, and
  one rollback path evidenced.
- ❌ Emit a finding without the mandatory fields.
- ❌ Emit a P0 without a money/security/data/completion-blocker rationale or an unblocking chain.
- ❌ Emit a KEEP/HARDEN finding into P0–P3.
- ❌ Mark a component KEEP/HARDEN unless it meets all six §0.13 criteria.
- ❌ Resolve a contradiction silently.
- ❌ Infer a technology, architecture, feature, or behavior from a folder
  name, README, package name, comment, variable name, or documentation
  alone.
- ❌ Promote an L3 recommendation into an L0 assumption.
- ❌ Produce a summary count that does not match the underlying file.
- ❌ Skip a dimension because "there's nothing there." Absence is a
  finding.
- ❌ Modify any source file outside `./_audit/`.
- ❌ Ignore `_browser_test/` when producing dimension 24.
- ❌ Invent browser findings when `_browser_test/` is absent.
- ❌ Re-invent feature IDs outside `03_FEATURE_STACK_DRAFT.md`.
- ❌ Define chains outside `10_CHAINS.md`.
- ❌ **Compile findings.** That is the compiler's job.
- ❌ **Resolve findings.** That is the resolver's job.
- ❌ **Produce a per-file worklist.** That is the compiler's job.
- ❌ **Write `TO_BE_RESOLVE.md`.** That is the compiler's job.
- ❌ **Dispatch sub-agents.** That is the resolver's job.
- ❌ **Amend a finding to `COMPILED` or `RESOLVED` yourself.** The
  compiler and resolver do that.
- ❌ Exceed the time-box. Write what you have by Day 7 and freeze.
- ❌ Omit `project_completion_blocker` from any finding.
- ❌ Mark a completion blocker as `no` when it prevents the app from booting, building, or passing critical tests.

---

## 17 · Final instruction

Output one line:

- `REMEDIATION AUDIT COMPLETE — run <n> — artifacts in ./_audit/ — 28 dimensions — <n> findings (<n> NEW, <n> COMPILED, <n> RESOLVED, <n> DEFERRED, <n> INVALID) — <n> clusters — coverage <n>% — <n> completion blockers`

If blocked:

- `REMEDIATION AUDIT PARTIAL — blocked on <precondition> — phase <N> not completed`

If timed out:

- `REMEDIATION AUDIT PARTIAL — time-box expired at day <n> — phases <list> incomplete — artifacts in ./_audit/`

Begin with Pass 0, Phase 0 (Boot smoke test), then Phase 0.5 (Pre-flight checks).

**Enumerate. Observe. Diff. Cluster. Bridge the browser audit. Flag completion blockers. Produce the production-readiness gate. Stop at Day 7. Do not compile. Do not resolve.**

---

<!-- 
# What changed — v4 → v5

## Project completion focus

- Added `project_completion_blocker` field to every finding (`yes` / `no` / `partial`).
- Added Phase 0.5: Pre-flight checks (env vars, DB connectivity, Valkey, test collection, type check, lint, migration status, lockfile sync).
- Added `COMPLETION_BLOCKERS.md` as a top-level artifact.
- Added dimension 27: `project_completion_blockers.md` — the single source of truth for what must be fixed before deployment.
- Added dimension 28: `supply_chain_security.md` — SBOM, licenses, CVE scanning, lockfile integrity.

## Expanded security coverage

- Dimension 18 (security) now explicitly includes:
  - Payment security (credential storage, webhook verification, idempotency, 3DS/SCA, PCI-DSS scope)
  - Compliance (GDPR, data residency, audit retention, key rotation)
- New phase values: `payment`, `compliance`, `testing`, `infra`, `docs`

## Stricter production-readiness gate

- Added conditions 15–18:
  - All required env vars set in production
  - Database migrations linear and tested
  - Payment credentials stored encrypted
  - PCI-DSS compliance verified

## Enhanced executive summary

- Added "Completion Blockers" section (top 10 yes blockers).
- Added completion blocker counts to headline numbers.
- Added `Completion blocker` column to top 20 findings table.
- Added per-dimension headlines for payment and compliance.

## Improved compiler output

- `04_REMEDIATION_PLAN.md` now has a "Completion blockers" section at the top.
- Priority matrix rules updated: `project_completion_blocker = yes` is automatically high impact.
- Cluster table and KEEP/HARDEN tables include completion blocker column.

## Phase structure update

- Added new phases: `payment`, `compliance`, `testing`, `infra`, `docs`
- Updated phase execution order table to include new phases
- Added Phase 33 (Project completion blockers), Phase 34 (Supply chain security)

## Anti-failure modes

- Added explicit prohibitions:
  - ❌ Omit `project_completion_blocker` from any finding.
  - ❌ Mark a completion blocker as `no` when it prevents the app from booting, building, or passing critical tests.
-->









