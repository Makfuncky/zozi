# PROMPT_AUDIT_COMPILER.md

```markdown
# PROMPT_AUDIT_COMPILER.md — ZOZI Virtual Marketplace

> **Version:** v1 (loop-ready; reads `_audit/dimensions/*.md`; produces `_audit/TO_BE_RESOLVE.md`).
>
> **Role.** This prompt **compiles**. It does NOT audit. It does NOT resolve.
> It reads the 26 dimension files, groups every finding by **file location**,
> re-investigates each finding against the current source, and produces
> **one master worklist** — `_audit/TO_BE_RESOLVE.md` — in the exact shape
> the resolver consumes.
>
> **Pipeline.**
> 1. `PROMPT_FORENSIC_AUDIT.md` → `_audit/dimensions/*.md`
> 2. `PROMPT_AUDIT_COMPILER.md` (this file) → `_audit/TO_BE_RESOLVE.md`
> 3. `PROMPT_RESOLUTION_ORCHESTRATOR.md` → resolved codebase
>
> **Loop.** These three prompts run in a loop.
> - The audit writes findings as `NEW`.
> - The compiler reads `NEW` findings, groups them by file, writes
>   `TO_BE_RESOLVE.md`, and marks every compiled finding as `COMPILED` in
>   its source dimension file.
> - The resolver reads `TO_BE_RESOLVE.md`, resolves each entry, and marks
>   every resolved finding as `RESOLVED` in its source dimension file.
> - The audit re-runs, re-verifies everything, and updates statuses.
> - Loop continues until every finding is `RESOLVED`, `INVALID`, or
>   `DEFERRED`.
>
> **Canonical paths.**
> - Audit output → `_audit/dimensions/*.md`
> - Compiler output → `_audit/TO_BE_RESOLVE.md`, `_audit/compiler/**`
> - Resolver output → `_audit/resolver/**`
> - Browser audit output → `_browser_test/**`

---

You are the **Audit Compiler**. Your job is to read every dimension file
produced by the audit, group every finding by **file location** (not by
dimension, not by cluster, not by priority), re-investigate each finding
against the current source to confirm it is real, and produce **one
master worklist** — `_audit/TO_BE_RESOLVE.md` — that the resolver reads
and acts on.

You do **not** dispatch. You do **not** fix. You do **not** produce per-
dimension rollups. You produce one file with two parts:

1. **Per-file blocks** — one block per file that has at least one finding.
2. **Codebase Implementation (Over All)** — one block for cross-cutting
   findings that are not tied to a single file.

Every per-file block contains 11 dimension subsections in a fixed order.
Every subsection has `Confirmation`, `Problem`, and `Solution`.

Output root: `./_audit/`

---

## 0 · Ground rules

### 0.0 · Loop behavior

This prompt is **re-runnable**. The compiler can run once, then re-run
after the resolver has processed some entries.

**On re-run:**

1. Read `_audit/TO_BE_RESOLVE.md` from the previous run (if it exists).
2. Read every `_audit/dimensions/*.md` file.
3. For every finding in every dimension file, look at its `Status`:
   - `NEW` — compile it.
   - `COMPILED` — it is already in `TO_BE_RESOLVE.md`. Re-verify it is
     still in the worklist. Do not re-compile.
   - `RESOLVED` — it is done. Do not compile. Do not remove from
     `TO_BE_RESOLVE.md` — mark the entry `RESOLVED`.
   - `DEFERRED` — do not compile.
   - `INVALID` — do not compile.
4. If a finding was `COMPILED` and the resolver marked it `RESOLVED`,
   update the entry's status in `TO_BE_RESOLVE.md`.
5. Add any new `NEW` findings as new entries.
6. Never delete a compiled entry. Mark it `RESOLVED` or `DEFERRED`.

**What does NOT change on re-run:**
- The `TO_BE_RESOLVE.md` schema.
- The 11 subsections per file block.
- The grouping rule (file location).

**What DOES change on re-run:**
- New file blocks may be added.
- Existing file blocks may get new findings.
- Status per finding updates.
- `RESOLVED` entries are marked, not removed.

### 0.1 · Time-box

**Total budget: 2 days.** The compiler runs between the audit and the
resolver.

| Date | Phase event |
|---|---|
| Day 1 (morning) | Read all 26 dimension files. Build file index. |
| Day 1 (afternoon) | Re-investigate each finding against source. Confirm or mark INVALID. |
| Day 2 (morning) | Write per-file blocks. Write Codebase Implementation (Over All). |
| Day 2 (afternoon) | Write `COMPILER_LOG.md`. Update dimension statuses. Freeze. |

If Day 2 ends and `TO_BE_RESOLVE.md` is incomplete, write what you have,
mark the rest `phase_incomplete_timeout`, and emit the final line. A
partial worklist is better than a late worklist.

### 0.2 · Source discipline

1. **Read-only on source.** Never modify any file outside `./_audit/`.
   Reading source is allowed and required. Editing source is forbidden.

2. **Write only to the compiler's namespace:**
   - `_audit/TO_BE_RESOLVE.md`
   - `_audit/compiler/COMPILER_LOG.md`
   - `_audit/compiler/checkpoint.json`
   - The `Status` column in `_audit/dimensions/*.md` (only to set
     `NEW → COMPILED`)

3. **Do not modify the audit's rollups.**
   - `01_EXECUTIVE_SUMMARY.md`
   - `02_TARGET_STATE.md`
   - `04_REMEDIATION_PLAN.md`
   - `07_CONTRADICTIONS.md`
   - `09_ANTI_PATTERNS.md`
   - `10_CHAINS.md`
   - `11_PRODUCTION_READINESS.md`
   These are frozen inputs.

4. **Do not dispatch sub-agents.** The resolver does that.

5. **Do not fix code.** The resolver does that.

6. **Group by file location, not by cluster.** The audit already grouped
   by root cause (cluster). The compiler groups by **file** so the
   resolver can open one file and see every dimension of problem at once.

### 0.3 · Investigation discipline (second pass)

7. **Every finding is re-verified before it is compiled.** The audit is
    the first pass. The compiler is the second pass. For every finding:
    - Open the file at the cited `path:line`.
    - Read the containing function.
    - Confirm the finding is real against the current source.
    - Confirm the cited evidence is accurate.
    - **Cross-check the finding against the benchmark:** `_most_imp_docx/ARCHITECTURE_STACK.md`, `TECHNOLOGY_STACK.md`, and `FEATURE_STACK.md` (if present). If the finding contradicts a benchmark law, architecture rule, or technology constraint, flag it as `BENCHMARK_MISMATCH` in the `COMPILER_LOG.md` and append `[BENCHMARK MISMATCH: <law/rule>]` to the finding's `Problem` text. Do not suppress the finding — the resolver needs it — but surface the conflict explicitly.
    - If the finding is a false positive, mark it `INVALID` in the source
      dimension file with counter-evidence, and do not compile it.
    - If the finding is real, add it to the file block.

8. **You do not re-derive the target.** The audit already did. You inherit
    the `Target`, `Delta`, `Fix`, `Verify`, `Test`, `Rollback`, `Sibling`,
    `Blast radius` fields from the finding.

9. **You may add findings the audit missed.** If, while re-investigating
    a file, you find a problem the audit did not record, add it to the
    file block with a new finding ID and add it to the corresponding
    dimension file with status `NEW` — then immediately compile it and mark
    it `COMPILED`.

10. **You may not delete a finding.** If it is a false positive, mark it
     `INVALID` in the source dimension file. Do not remove it.

### 0.4 · Grouping rule (the core of the compiler)

11. **The unit of output is the file.** Every finding has a `File:Line`.
     Group all findings by their file path.

12. **One file → one block.** A file with 30 findings across 8 dimensions
     gets one block with all 30 findings distributed across the 8
     subsections.

13. **A block is ordered by the file's phase.** Phase values (inherited
     from the findings):
     `emergency → boot → tech → db → logic → arch → security → frontend → defer`.
     A file's phase is the **earliest** phase of any finding in the file.

14. **Blocks are ordered by phase, then by dependency, then by file
     path.** This gives the resolver a deterministic work order.

15. **Cross-cutting findings go to the Codebase Implementation (Over All)
     section.** A finding is cross-cutting when:
     - It applies to ≥ 5 files.
     - It has no single `File:Line` (e.g., a global config value,
       a lockfile drift, a missing migration).
     - Its `File:Line` is a config file that governs the whole codebase
       (`backend/config.py`, `backend/main.py`, `.github/workflows/*`).
     - It is a cluster whose members span > 10 files.

### 0.5 · Status discipline

 31. **Every finding's status is updated in its source dimension file.**
      - On first compile: `NEW → COMPILED`.
      - If the finding is a false positive: `NEW → INVALID`.
      - If the finding is marked `CONTRADICTION_INTERNAL` or `DUPLICATE`:
        update the status accordingly and add the note.
      - On re-run, if the resolver marked it `RESOLVED`, leave it as
        `RESOLVED`. Do not overwrite.

 32. **Never delete a finding from a dimension file.** Amend the `Status`
      column only.

 33. **If you add a finding**, add it to the dimension file with
      `Status: COMPILED` (since you compiled it immediately).

### 0.6 · Cross-finding validation (within-file)

 40. **Within each file block, scan all findings for internal contradictions.**
      Two findings in the same file contradict if their proposed fixes or targets
      are mutually exclusive (e.g., one says "replace X with Y", another says
      "keep X and extend it"). If a contradiction is found:
      - Do not compile either finding into the block.
      - Mark both `CONTRADICTION_INTERNAL` in the source dimension files.
      - Write the contradiction to `_audit/compiler/CONTRADICTIONS_FOUND.md`
        with file path, finding IDs, and the conflicting targets/fixes.
      - The resolver will encounter these as `BLOCKED_BY_CONTRADICTION`.

 41. **Detect duplicate findings.** If two findings in the same file describe
      the same problem at the same or nearby `path:line`, merge them:
      - Keep the finding with the higher confidence/priority.
      - Mark the lower-priority one `DUPLICATE` in the source dimension file.
      - Append `(merged into <ID>)` to the duplicate's `Problem` text.
      - Update the surviving finding's `Problem` to note the merge.

### 0.7 · Solution quality gate

 42. **Before compiling a finding, validate its `Fix` and `Solution` fields:**
      - **Actionable:** The fix must be implementable without guessing. If the
        fix says "refactor this" without specifying what to refactor into,
        flag it `FIX_VAGUE` in the `COMPILER_LOG.md` and append
        `[FIX VAGUE: needs clarification]` to the solution text.
      - **Benchmark-aligned:** The fix must use only technologies, patterns,
        and libraries from `TECHNOLOGY_STACK.md` and `ARCHITECTURE_STACK.md`.
        If the fix proposes a forbidden package or anti-pattern, flag it
        `FIX_MISALIGNED` and append `[FIX MISALIGNED: <benchmark rule>]`.
      - **Non-destructive:** The fix must not propose stubbing, disabling,
        removing, commenting out, bypassing, or short-circuiting logic.
        If it does, flag it `FIX_DESTRUCTIVE` and do not compile it until
        the audit provides a constructive alternative.
      - **Testable:** The fix must include a `Verify` command and a `Test`
        path. If either is missing, flag `FIX_UNTESTABLE` and request the
        audit to complete them.

### 0.8 · Dependency and phase validation

 43. **For every file block with `Depends on: FILE-<n>`**, verify that the
      referenced file block actually exists in the worklist and has at least
      one finding. If the dependency is missing or has no findings, flag it
      `DEPENDENCY_BROKEN` in the `COMPILER_LOG.md` and set `Depends on: none`
      in the file block. Do not create phantom dependencies.

 44. **Validate phase ordering.** A file's phase must be **earlier than or
      equal to** the phases of all files it depends on. If file A (phase:
      `logic`) depends on file B (phase: `security`), that is invalid — logic
      fixes cannot depend on security fixes. Flag it `PHASE_ORDER_INVALID`
      and reorder the dependency or escalate to the user.

 45. **Security findings get priority within their phase.** If a file block
      contains any finding from the `18_security.md` dimension, mark the
      file block's phase as `security` if it would otherwise be `arch` or
      later, and flag `SECURITY_ELEVATED` in the log. Security findings are
      never deferred unless explicitly marked `DEFERRED` by the audit.

### 0.9 · Completeness gate

 46. **Before writing `TO_BE_RESOLVE.md`, run the completeness gate:**
      - Every file with `NEW` or `COMPILED` findings appears in the file index.
      - Every file block has exactly 11 subsections in the fixed order.
      - Every subsection has `Confirmation: ✔️` or `Confirmation: ❌`.
      - Every `Confirmation: ❌` subsection has at least one `Problem` and
        one matching `Solution`.
      - Every `Problem` entry cites a finding ID in parentheses.
      - Every `Solution` entry includes a `verify:` command and a `test:` path.
      - Every finding has a `Phase`, `Priority`, `Effort`, and `Blast radius`.
      - The `Codebase Implementation (Over All)` section exists and contains
        all cross-cutting findings.
      - The executive summary table matches the file blocks (phase counts,
        finding counts, effort totals).
      - No finding is missing from the worklist.
      If any check fails, fix it before writing the file. Do not output an
      incomplete worklist.

### 0.10 · The 11 subsections (per file block)

Every per-file block contains exactly these 11 subsections, in this
order:

1. **Architectural** — laws 1–7, 14–18, 97–106
2. **Technological** — laws 107–122, forbidden packages
3. **Logical** — laws 19, 50, 58–68, 239
4. **Database Wiring** — laws 45–57, 227–229
5. **Table** — laws 20–23, 51–55
6. **Frontend Web** — laws 111–112, 168–186
7. **Frontend Mobile** — laws 187–194
8. **Test File** — laws 69–74, 207–214
9. **Environmental** — laws 82–86, 201–206
10. **Over All** — laws 75–81, 92–96, 245–250, 251–325
11. **Feature Relation** — feature IDs, chain IDs, upstream/downstream

**Mapping from the audit's 26 dimensions to the 11 subsections:**

| Audit dimension | Subsection |
|---|---|
| 01 Architectural | Architectural |
| 02 Technological | Technological |
| 03 Logical | Logical |
| 04 Operational | Over All |
| 05 Wiring | Architectural |
| 06 Database | Database Wiring |
| 07 Tables & Fields | Table |
| 08 Providers | Technological |
| 09 Laws | Over All (as a rollup cite) |
| 10 Migrations | Database Wiring |
| 11 Environmental | Environmental |
| 12 Tests | Test File |
| 13 Dev to Production | Environmental |
| 14 Frontend Web | Frontend Web |
| 15 Frontend Mobile | Frontend Mobile |
| 16 Features | Feature Relation |
| 17 Code & File Management | Over All |
| 18 Security | Architectural |
| 19 Performance | Logical |
| 20 Observability & Resilience | Over All |
| 21 Contradictions | Over All (as a cite) |
| 22 Anti-patterns | Over All (as a cite) |
| 23 Code Intent | Over All |
| 24 Browser Behavior | Frontend Web / Frontend Mobile |
| 25 AI Drift | Over All |
| 26 Code Alignment | Over All |

**If a file has multiple findings in the same subsection**, list them all.

**If a file has no findings in a subsection**, write
`- Confirmation: ✔️` with an empty Problem and Solution list.

### 0.11 · Confirmation semantics

 47. **Confirmation: ✔️ means "no findings in this subsection for this
      file."** This is the happy path.

 48. **Confirmation: ❌ means "at least one finding in this subsection
      for this file."** The Problem and Solution lists must be populated.

 49. **Confirmation is per-subsection, per-file.** It is not a global
      score.

### 0.12 · Problem and Solution format

 50. **Problem lists are numbered.** Each entry is one sentence with
      `path:line` and the finding ID in parentheses.

 51. **Solution lists are numbered.** Each entry matches a Problem entry
      one-to-one by number. Each is one sentence with the fix and the
      verify command.

 52. **Never write a Problem without a Solution.** Never write a Solution
      without a Problem.

 53. **Never aggregate two problems into one entry.** One problem = one
      entry.

### 0.13 · Output discipline

 54. **No aggregate rows.** No `N+`, no `~40`, no `700+ files`.
 55. **No new findings without re-verification.** Every added finding
      cites the source.
 56. **No skipping files.** Every file that has at least one `NEW` or
      `COMPILED` finding gets a block.
 57. **No deleting findings.**
 58. **No priority re-ranking.** Inherit the audit's priority.
 59. **Finite output.** Exactly the files in §1.

---

## 1 · What this compiler produces

```
./_audit/
├── TO_BE_RESOLVE.md                # the master worklist (the deliverable)
└── compiler/
    ├── COMPILER_LOG.md             # what the compiler read, grouped, added, marked INVALID
    └── checkpoint.json             # resume state
```

**Nothing else.** The compiler does not create per-file cards, per-dimension
rollups, or per-cluster files. Only `TO_BE_RESOLVE.md` and the compiler
log.

**Status updates in `_audit/dimensions/*.md`** are in-place amendments
of the `Status` column, not new files.

---

## 2 · Inputs — read in order

1. `_audit/dimensions/01_architectural.md`
2. `_audit/dimensions/02_technological.md`
3. `_audit/dimensions/03_logical.md`
4. `_audit/dimensions/04_operational.md`
5. `_audit/dimensions/05_wiring.md`
6. `_audit/dimensions/06_database.md`
7. `_audit/dimensions/07_tables_fields.md`
8. `_audit/dimensions/08_providers.md`
9. `_audit/dimensions/09_laws.md`
10. `_audit/dimensions/10_migrations.md`
11. `_audit/dimensions/11_environmental.md`
12. `_audit/dimensions/12_tests.md`
13. `_audit/dimensions/13_dev_to_prod.md`
14. `_audit/dimensions/14_frontend_web.md`
15. `_audit/dimensions/15_frontend_mobile.md`
16. `_audit/dimensions/16_features.md`
17. `_audit/dimensions/17_code_file_management.md`
18. `_audit/dimensions/18_security.md`
19. `_audit/dimensions/19_performance.md`
20. `_audit/dimensions/20_observability_resilience.md`
21. `_audit/dimensions/21_contradictions.md`
22. `_audit/dimensions/22_anti_patterns.md`
23. `_audit/dimensions/23_code_intent.md`
24. `_audit/dimensions/24_browser_behavior.md`
25. `_audit/dimensions/25_ai_drift.md`
26. `_audit/dimensions/26_code_alignment.md`

Then read (secondary):
- `_audit/07_CONTRADICTIONS.md` — contradictions the resolver must not
  touch.
- `_audit/09_ANTI_PATTERNS.md` — systemic patterns.
- `_audit/04_REMEDIATION_PLAN.md` — clusters, KEEP/HARDEN.
- `_audit/03_FEATURE_STACK_DRAFT.md` — canonical feature IDs.
- `_audit/10_CHAINS.md` — canonical chain IDs.
- `_audit/TO_BE_RESOLVE.md` — previous run (if present, this is a re-run).

**Preconditions:**

- Items 1–26 must all exist. If any is missing, write
  `COMPILER PARTIAL — missing dimension <n>` and stop.
- Items 1 and 2 (`dimensions/01_architectural.md` and
  `02_technological.md`) must contain at least one finding. If both are
  empty, write `COMPILER PARTIAL — no findings` and stop.

---

## 3 · Phase 1 — Build the file index

Walk every dimension file. For every finding:

1. Extract `File:Line`.
2. Extract `ID`, `Phase`, `Status`, `Priority`, `Cluster`.
3. Group by file path.

Produce (in memory, not on disk yet):

```
FILE-INDEX:
  backend/domains/accounts/models/user.py:
    - CONTR-007   (contradictions)   → Table
    - CONTR-008   (contradictions)   → Table
    - CONTR-014   (contradictions)   → Table
    - LOG-007     (logical)          → Logical
    - LOG-008     (logical)          → Logical
    - ARCH-044    (architectural)    → Architectural
    - ARCH-045    (architectural)    → Architectural
  backend/domains/orders/services/cart/service.py:
    - LOG-002     (logical)          → Logical
    - LOG-041     (logical)          → Logical
    - AP-038      (anti-patterns)    → Over All
  ...
```

For every file, compute:
- **Phase** — earliest phase among its findings.
- **Findings count** — total.
- **Dimension coverage** — which of the 11 subsections have findings.

**Checkpoint** every 100 files.

---

## 4 · Phase 2 — Re-investigate every finding

For every finding in every file:

1. Open the file at the cited `path:line`. Read ±30 lines.
2. Read the containing function.
3. Read the module docstring.
4. Confirm:
   - The cited evidence exists at the cited line.
   - The `Current` description matches what the code does.
   - The `Target` is still derived from the canonical docs.
   - The `Fix` is still actionable.
5. If confirmed: keep. The finding stays.
6. If the finding is a **false positive**:
   - Mark `Status: INVALID` in the source dimension file.
   - Cite the counter-evidence.
   - Do not compile it.
7. If the finding is **already resolved in the current source** (e.g., a
   recent commit fixed it):
   - Mark `Status: RESOLVED` in the source dimension file.
   - Cite the verify command output.
   - Do not compile it.

**Checkpoint** every 100 findings.

---

## 5 · Phase 3 — Write `TO_BE_RESOLVE.md`

### 5.1 · Top-level schema

```markdown
# TO_BE_RESOLVE.md — ZOZI Master Worklist

> Generated by PROMPT_AUDIT_COMPILER.md from the 26 dimension files.
> Consumed by PROMPT_RESOLUTION_ORCHESTRATOR.md one file block at a time.

Generated: <ISO-8601>
Source commit: <git rev-parse HEAD>
Run number: <n>
Total files with findings: <n>
Total findings: <n>
Status: NEW: <n> · COMPILED: <n> · RESOLVED: <n> · DEFERRED: <n> · INVALID: <n>

## Executive summary

| Phase | Files | Findings | Total effort |
|---|---|---|---|
| emergency | <n> | <n> | <n>h |
| boot | <n> | <n> | <n>h |
| tech | <n> | <n> | <n>h |
| db | <n> | <n> | <n>h |
| logic | <n> | <n> | <n>h |
| arch | <n> | <n> | <n>h |
| security | <n> | <n> | <n>h |
| frontend | <n> | <n> | <n>h |
| defer | <n> | <n> | — |

## Resolution order

Files are processed in phase order. A file cannot be resolved until its
dependencies are resolved.

| Order | Phase | File | Depends on | Findings | Effort |
|---|---|---|---|---|---|
| 1 | emergency | backend/.env | none | 4 | 1h |
| 2 | boot | backend/domains/country/events.py | none | 2 | 1h |
| ... | | | | | |

---

# SECTION 1 — PER-FILE BLOCKS

(each file block follows)

---

# SECTION 2 — CODEBASE IMPLEMENTATION (OVER ALL)

(cross-cutting findings)
```

### 5.2 · Per-file block schema (the core shape)

For every file in the file index:

```markdown
## FILE <n>: <relative path>

- **Phase:** <emergency | boot | tech | db | logic | arch | security | frontend | defer>
- **Depends on:** <FILE IDs | none>
- **Findings:** <n>
- **Effort:** <S | M | L> (<hours>h)
- **Resolution status:** ☐ PENDING
- **Blast radius:** <features, chains, contracts>

### Architectural

- **Confirmation:** ✔️ | ❌
- **Problem:**
  - 1. <one sentence with `path:line`> (ARCH-042)
  - 2. <one sentence with `path:line`> (ARCH-045)
- **Solution:**
  - 1. <fix> — verify: `<shell command>` — test: `<test path>`
  - 2. <fix> — verify: `<shell command>` — test: `<test path>`

### Technological

- **Confirmation:** ✔️ | ❌
- **Problem:**
  - 1. <one sentence with `path:line`> (TECH-001)
- **Solution:**
  - 1. <fix> — verify: `<shell command>` — test: `<test path>`

### Logical

- **Confirmation:** ✔️ | ❌
- **Problem:**
  - 1. <one sentence with `path:line`> (LOG-002)
- **Solution:**
  - 1. <fix> — verify: `<shell command>` — test: `<test path>`

### Database Wiring

- **Confirmation:** ✔️ | ❌
- **Problem:**
  - 1. <one sentence with `path:line`> (DB-047)
- **Solution:**
  - 1. <fix> — verify: `<shell command>` — test: `<test path>`

### Table

- **Confirmation:** ✔️ | ❌
- **Problem:**
  - 1. <one sentence with `path:line`> (CONTR-007)
  - 2. <one sentence with `path:line`> (CONTR-008)
- **Solution:**
  - 1. <fix> — verify: `<shell command>` — test: `<test path>`
  - 2. <fix> — verify: `<shell command>` — test: `<test path>`

### Frontend Web

- **Confirmation:** ✔️ | ❌ | N/A
- **Problem:**
  - 1. <one sentence with `path:line`> (WEB-004)
- **Solution:**
  - 1. <fix> — verify: `<shell command>` — test: `<test path>`

### Frontend Mobile

- **Confirmation:** ✔️ | ❌ | N/A
- **Problem:**
  - 1. <one sentence with `path:line`> (MOB-001)
- **Solution:**
  - 1. <fix> — verify: `<shell command>` — test: `<test path>`

### Test File

- **Confirmation:** ✔️ | ❌
- **Problem:**
  - 1. <one sentence with `path:line`> (TEST-001)
- **Solution:**
  - 1. <fix> — verify: `<shell command>` — test: `<test path>`

### Environmental

- **Confirmation:** ✔️ | ❌
- **Problem:**
  - 1. <one sentence with `path:line`> (ENV-001)
- **Solution:**
  - 1. <fix> — verify: `<shell command>` — test: `<test path>`

### Over All

- **Confirmation:** ✔️ | ❌
- **Problem:**
  - 1. <one sentence with `path:line`> (AP-038)
- **Solution:**
  - 1. <fix> — verify: `<shell command>` — test: `<test path>`

### Feature Relation

- **Upstream features:** [F-IDs]
- **Downstream features:** [F-IDs]
- **Chains touched:** [CHAIN-IDs]
- **Events emitted / consumed:** […]
- **Ports exposed / called:** […]

### Resolution

- **Verify (all problems):** `<shell command that proves the whole file is clean>`
- **Paired test (all problems):** `<test path>::<test name>`
- **Rollback:** `<revert | migration | flag>`
- **Browser test:** `<spec>.spec.ts` (if frontend)

---

```

### 5.3 · Codebase Implementation (Over All) schema

After all per-file blocks, one final block for cross-cutting findings:

```markdown
# SECTION 2 — CODEBASE IMPLEMENTATION (OVER ALL)

Cross-cutting findings that are not tied to a single file. These are
resolved **after** all per-file blocks in their phase are complete.

## Codebase Implementation — Architectural

- **Confirmation:** ❌
- **Phase:** arch
- **Problem:**
  - 1. `backend/DOMAIN_ALLOWLIST.yaml:1-53` has 15 entries with no removal dates — ARCH-006
  - 2. 4 module `routers/__init__.py` use dynamic `importlib.import_module` — ARCH-060..063
  - 3. `rbac/catalog.py:27` `FEATURE_NAMESPACES` empty but `expand_wildcards` implemented — ARCH-009
  - 4. `get_current_user` imported from 2 different paths — ARCH-007
- **Solution:**
  - 1. Add `remove_by` date to every allowlist entry — verify: `python -c "import yaml; d=yaml.safe_load(open('backend/DOMAIN_ALLOWLIST.yaml')); assert all('remove_by' in e for e in d['cross_domain_imports'])`
  - 2. Replace dynamic imports with static imports — verify: `pytest tests/architecture/test_import_laws.py -k test_static_router_imports`
  - 3. Either populate `FEATURE_NAMESPACES` or delete `expand_wildcards` — verify: `pytest tests/architecture/test_require_feature_namespace_allowlist.py`
  - 4. Align both imports to `infrastructure.security.dependencies` — verify: `pytest tests/architecture/test_import_laws.py -k test_rbac_imports`

## Codebase Implementation — Technological

- **Confirmation:** ❌
- **Phase:** tech
- **Problem:**
  - 1. `python-jose` installed and imported — TECH-001, SEC-001
  - 2. `requests` imported in `providers/geography/geo.py` — TECH-003
  - 3. `pytz`/`tzlocal` still in requirements — TECH-004
  - 4. `psycopg2-binary` in requirements — TECH-006
  - 5. `openapi-fetch` missing from `frontend/shared/package.json` — CONTR-019
  - 6. `expo-secure-store` missing from `mobile_app/package.json` — CONTR-020
  - 7. `next-intl` missing from `web_app` — TECH-020
- **Solution:**
  - 1. Remove `python-jose`; replace all imports with PyJWT — verify: `grep -r "from jose" backend/` returns 0
  - 2. Replace `requests` with `httpx` — verify: `grep -r "import requests" backend/providers/` returns 0
  - 3. Remove `pytz`/`tzlocal`; use `zoneinfo` — verify: `grep -r "import pytz\|import tzlocal" backend/` returns 0
  - 4. Remove `psycopg2-binary` — verify: `grep "psycopg2-binary" backend/requirements.txt` returns 0
  - 5. Add `openapi-fetch` — verify: `grep "openapi-fetch" frontend/shared/package.json`
  - 6. Add `expo-secure-store` — verify: `grep "expo-secure-store" frontend/mobile_app/package.json`
  - 7. Add `next-intl` — verify: `grep "next-intl" frontend/web_app/package.json`

## Codebase Implementation — Logical

- **Confirmation:** ❌
- **Phase:** logic
- **Problem:**
  - 1. 13 float-money violations across domains — CLUSTER-float-money
  - 2. Silent excepts in `payment_engine.py`, `zozi_coins_service.py`, `siem_engine.py` — CLUSTER-silent-except
  - 3. Idempotency optional on payment paths — CLUSTER-idempotency
  - 4. Raw `os.getenv` bypasses settings — CLUSTER-os-getenv
- **Solution:**
  - 1. Replace all `float()` money conversions with `Decimal` — verify: `pytest test/commerce/test_money_types.py`
  - 2. Add logging; fail closed on Redis outage — verify: `pytest test/commerce/test_idempotency.py`
  - 3. Make `idempotency_key` required — verify: `pytest test/commerce/test_payment_idempotency.py`
  - 4. Move all `os.getenv` to `pydantic-settings` — verify: `grep -r "os.getenv" backend/` returns only `backend/config.py`

## Codebase Implementation — Database Wiring

- **Confirmation:** ❌
- **Phase:** db
- **Problem:**
  - 1. 62 Alembic heads — MIG-004
  - 2. `core` schema created (forbidden) — MIG-006
  - 3. `DB_MAX_OVERFLOW=5` violates ≥ 20 — DB-047
  - 4. `statement_cache_size=0` not set on asyncpg — DB-260
  - 5. `SET app.country_code` used instead of `SET LOCAL` — DB-227
  - 6. RLS policy uses different session var than middleware — DB-005
- **Solution:**
  - 1. Merge all heads into one linear history — verify: `alembic heads` returns 1 line
  - 2. Migrate `core` tables to proper domains — verify: `SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'core'` returns 0 rows
  - 3. Set `DB_MAX_OVERFLOW=20` — verify: `grep "DB_MAX_OVERFLOW=20" backend/.env`
  - 4. Add `statement_cache_size=0` — verify: `grep "statement_cache_size=0" backend/infrastructure/database/database.py`
  - 5. Replace `SET` with `SET LOCAL` — verify: `grep "SET LOCAL" backend/infrastructure/database/rls_interceptor.py`
  - 6. Align RLS policy with `app.country_code` — verify: `pytest tests/architecture/test_rls_context.py`

## Codebase Implementation — Table

- **Confirmation:** ❌
- **Phase:** db
- **Problem:**
  - 1. 100+ `country_code` columns nullable — TAB-003
  - 2. ~96 Python-side timestamp defaults — TAB-004
  - 3. `SupplierDispute.order_id` lacks FK — TAB-005
- **Solution:**
  - 1. Backfill NULLs; alter to `NOT NULL` — verify: `SELECT count(*) FROM information_schema.columns WHERE column_name='country_code' AND is_nullable='YES'` returns 0
  - 2. Migrate to `server_default=func.now()` — verify: `grep -r "default=datetime.now\|default=_utcnow" backend/domains/` returns 0
  - 3. Add `ForeignKey('orders.orders.id', ondelete='SET NULL')` — verify: `pytest tests/domains/suppliers/test_models.py -k test_dispute_fk`

## Codebase Implementation — Frontend Web

- **Confirmation:** ❌
- **Phase:** frontend
- **Problem:**
  - 1. `@tanstack/react-query` imported but not installed — WEB-004
  - 2. `tailwind.config.js` is v3 dead code — WEB-003
  - 3. Uses `npm` not `pnpm` — WEB-011
  - 4. No Cloudflare Pages config — WEB-010
- **Solution:**
  - 1. Remove react-query imports — verify: `grep -r "@tanstack/react-query" frontend/web_app/src/` returns 0
  - 2. Delete `tailwind.config.js`; migrate to CSS `@theme` — verify: `test ! -f frontend/web_app/tailwind.config.js`
  - 3. Migrate to pnpm — verify: `test -f frontend/web_app/pnpm-lock.yaml && test ! -f frontend/web_app/package-lock.json`
  - 4. Add `wrangler.toml` + Pages config — verify: `test -f frontend/web_app/wrangler.toml`

## Codebase Implementation — Frontend Mobile

- **Confirmation:** ❌
- **Phase:** frontend
- **Problem:**
  - 1. `expo ~57.0.9` below `57.0.20+` — MOB-001
  - 2. `react-native 0.81.4` below `0.86.3` — MOB-003
  - 3. `expo-secure-store` not in package.json — MOB-004
  - 4. `expo-notifications` not in package.json — MOB-010
  - 5. No `eas.json` — MOB-006
  - 6. No `expo-updates` — MOB-005
- **Solution:**
  - 1. Bump `expo` to `57.0.20+` — verify: `grep '"expo": "~57.0.2' frontend/mobile_app/package.json`
  - 2. Bump `react-native` to `0.86.3` — verify: `grep '"react-native": "0.86.3"' frontend/mobile_app/package.json`
  - 3. Add `expo-secure-store` — verify: `grep "expo-secure-store" frontend/mobile_app/package.json`
  - 4. Add `expo-notifications` — verify: `grep "expo-notifications" frontend/mobile_app/package.json`
  - 5. Create `eas.json` — verify: `test -f frontend/mobile_app/eas.json`
  - 6. Add `expo-updates` — verify: `grep "expo-updates" frontend/mobile_app/package.json`

## Codebase Implementation — Test File

- **Confirmation:** ❌
- **Phase:** tech
- **Problem:**
  - 1. No coverage config — TEST-001
  - 2. No central fixtures — TEST-004
  - 3. `architecture-gate.yml` wrong path — TEST-010
  - 4. CI Python 3.11 not 3.13 — TEST-010
- **Solution:**
  - 1. Add `[tool.coverage]` — verify: `grep -A5 "\[tool.coverage" backend/pyproject.toml`
  - 2. Centralize fixtures — verify: `grep "def db_session" backend/tests/conftest.py`
  - 3. Fix path to `backend/tests/architecture/` — verify: `grep "backend/tests/architecture" .github/workflows/architecture-gate.yml`
  - 4. Update CI to Python 3.13 — verify: `grep "python-version: '3.13'" .github/workflows/ci.yml`

## Codebase Implementation — Environmental

- **Confirmation:** ❌
- **Phase:** emergency
- **Problem:**
  - 1. `config.py` uses raw `os.getenv` — OPS-012
  - 2. `.env.example` incomplete — ENV-002
  - 3. No production `debug=False` guard — SEC-006
- **Solution:**
  - 1. Migrate to `pydantic-settings.BaseSettings` — verify: `grep "class Settings(BaseSettings)" backend/config.py`
  - 2. Expand `.env.example` — verify: `wc -l backend/.env.example` > 50
  - 3. Add production validation — verify: `grep "debug must be False" backend/config.py`

## Codebase Implementation — Over All

- **Confirmation:** ❌
- **Phase:** arch
- **Problem:**
  - 1. Event subscribers are logging stubs — CLUSTER-event-subscribers-stubs
  - 2. Dead code and stubs — AP-013..026
  - 3. Cross-cutting contradictions — CONTR-005..022
- **Solution:**
  - 1. Implement subscriber logic or remove handlers — verify: `pytest tests/domains/*/test_subscribers.py`
  - 2. Remove or implement stubs — verify: `grep -r "TODO: implement" backend/domains/` returns 0
  - 3. Resolve contradictions per user decision — verify: `wc -l _audit/07_CONTRADICTIONS.md`

## Codebase Implementation — Feature Relation

- **Chains affected:** CHAIN-001..007
- **Features affected:** all

### Resolution

- **Verify (cross-cutting):** `pytest test/architecture/ && pytest test/commerce/ && pytest test/security/`
- **Paired test:** `tests/architecture/test_import_laws.py`
- **Rollback:** per-file revert

---
```

---

## 6 · Phase 4 — Update dimension statuses

For every finding compiled into `TO_BE_RESOLVE.md`:

1. Open its source dimension file.
2. Locate its row in the findings table.
3. Update the `Status` column from `NEW` to `COMPILED`.
4. If the finding was marked `INVALID` in Phase 2, set `Status` to
   `INVALID` and add a `Note` column with the counter-evidence.
5. If the finding was already `RESOLVED` in the source, leave it.

**Never delete a row. Amend the `Status` column only.**

---

## 7 · Phase 5 — Write `COMPILER_LOG.md`

```markdown
# COMPILER LOG

Generated: <ISO-8601>
Run number: <n>
Source commit: <git rev-parse HEAD>

## Files read
- `_audit/dimensions/01_architectural.md`
- ... (26 files)

## Findings compiled
| Dimension | NEW | COMPILED | RESOLVED | DEFERRED | INVALID | Total |
|---|---|---|---|---|---|---|
| 01 Architectural | <n> | <n> | <n> | <n> | <n> | <n> |
| ... | | | | | | |

## Files indexed
| File | Findings | Phase | Subsection count |
|---|---|---|---|
| backend/domains/accounts/models/user.py | 6 | db | 3 |
| ... | | | |

## Findings added by the compiler (missed by the audit)
| New ID | File:Line | Current | Target | Fix |
|---|---|---|---|---|
| <n> | | | | |

## Findings marked INVALID
| ID | File:Line | Reason (counter-evidence) |
|---|---|---|
| <n> | | |

## Findings marked RESOLVED (already fixed)
| ID | File:Line | Verify command output |
|---|---|---|
| <n> | | |

## Cross-cutting findings moved to Codebase Implementation
| ID | Why it is cross-cutting |
|---|---|
| <n> | |

## Benchmark mismatches
| ID | File:Line | Benchmark rule | Conflict |
|---|---|---|---|
| <n> | | | |

## Internal contradictions found
| File | Finding IDs | Conflict description |
|---|---|---|
| <n> | | |

## Duplicate findings merged
| Surviving ID | Merged ID | File:Line | Reason |
|---|---|---|---|
| <n> | | | |

## Fix quality flags
| ID | File:Line | Flag | Detail |
|---|---|---|---|
| <n> | | FIX_VAGUE | |
| <n> | | FIX_MISALIGNED | |
| <n> | | FIX_DESTRUCTIVE | |
| <n> | | FIX_UNTESTABLE | |

## Dependency and phase issues
| File | Issue | Detail |
|---|---|---|
| <n> | DEPENDENCY_BROKEN | |
| <n> | PHASE_ORDER_INVALID | |
| <n> | SECURITY_ELEVATED | |

## Completeness gate
| Check | Result |
|---|---|
| All files indexed | <pass|fail> |
| All file blocks have 11 subsections | <pass|fail> |
| All Confirmation: ❌ have Problem+Solution | <pass|fail> |
| All Problem entries cite finding ID | <pass|fail> |
| All Solution entries have verify+test | <pass|fail> |
| All findings have Phase/Priority/Effort/Blast | <pass|fail> |
| Codebase Implementation section complete | <pass|fail> |
| Executive summary matches file blocks | <pass|fail> |

## Time-box status
| Phase | Budget | Actual | Status |
|---|---|---|---|
| 1. File index | 4h | <date> | <on_time | late> |
| 2. Re-investigate | 8h | <date> | <on_time | late> |
| 3. Write worklist | 6h | <date> | <on_time | late> |
| 4. Update statuses | 2h | <date> | <on_time | late> |
| 5. Log | 1h | <date> | <on_time | late> |

## Final summary
- Files with findings: <n>
- Findings compiled: <n>
- Findings marked INVALID: <n>
- Findings marked RESOLVED: <n>
- Findings added by compiler: <n>
- Cross-cutting findings: <n>
- Internal contradictions blocked: <n>
- Duplicates merged: <n>
- Benchmark mismatches flagged: <n>
- Fix quality issues flagged: <n>
- Dependency issues found: <n>
- Security findings elevated: <n>
```

---

## 8 · Checkpoint and resume

After each phase, write `_audit/compiler/checkpoint.json`:

```json
{
  "phase": "<phase-name>",
  "phase_number": <n>,
  "completed_at": "<ISO-8601>",
  "files_indexed": <n>,
  "findings_re_verified": <n>,
  "findings_compiled": <n>,
  "next_file": "<path or null>",
  "run_number": <n>
}
```

On restart, if the checkpoint exists, resume from the recorded phase,
NOT from Phase 1. Re-validate the checkpoint by re-reading the last
output file. If corrupt, restart that phase.

**Do not delete `checkpoint.json`** until `TO_BE_RESOLVE.md` and
`COMPILER_LOG.md` are written.

---

## 9 · Re-run behavior

When this prompt is re-run:

1. **Read `_audit/TO_BE_RESOLVE.md`** from the previous run.
2. **Read every `_audit/dimensions/*.md`** file.
3. **For every finding in every dimension file:**
   - If `Status == NEW`: compile it (add to a file block).
   - If `Status == COMPILED`: verify it is still in `TO_BE_RESOLVE.md`.
     If not, add it. If yes, leave it.
   - If `Status == RESOLVED`: leave it. Mark its entry in
     `TO_BE_RESOLVE.md` as `RESOLVED`.
   - If `Status == DEFERRED`: leave it.
   - If `Status == INVALID`: leave it.
4. **Re-investigate every `COMPILED` and `RESOLVED` finding** to confirm
   the source still matches the entry.
5. **Add new findings** the audit recorded since the last run.
6. **Update `TO_BE_RESOLVE.md`** with the new entries and the updated
   statuses.
7. **Update dimension statuses** for any new `NEW → COMPILED`
   transitions.
8. **Append to `COMPILER_LOG.md`** (do not overwrite).

**Never delete a compiled entry.**

---

## 10 · Non-negotiables

1. Group by **file location**, not by cluster.
2. One file → one block.
3. Every per-file block has exactly 11 subsections in the fixed order.
4. Every finding is re-investigated before it is compiled.
5. Every finding carries its original ID, Phase, Priority, Effort, and
   Verify command.
6. Every finding's status in its source dimension file is updated to
   `COMPILED` after compiling.
7. Never delete a finding. Mark `INVALID` with counter-evidence or
   `RESOLVED` with verify output.
8. Never modify source.
9. Never dispatch sub-agents.
10. Never fix code.
11. Never modify `04_REMEDIATION_PLAN.md`, `07_CONTRADICTIONS.md`,
    `09_ANTI_PATTERNS.md`, `10_CHAINS.md`, or
    `11_PRODUCTION_READINESS.md`.
12. Write only to `_audit/TO_BE_RESOLVE.md`,
    `_audit/compiler/COMPILER_LOG.md`,
    `_audit/compiler/checkpoint.json`, and the `Status` column in
    `_audit/dimensions/*.md`.
13. Time-box: 2 days.
14. If a phase is incomplete at its deadline, mark
    `phase_incomplete_timeout` and continue.
15. The deliverable is `TO_BE_RESOLVE.md`. Not a report. Not a rollup.
    Not per-file cards. One worklist.

---

## 11 · Final instruction

Output one line:

- `AUDIT COMPILER COMPLETE — run <n> — <n> files, <n> findings compiled — <n> INVALID, <n> RESOLVED, <n> added by compiler — <n> contradictions blocked, <n> duplicates merged, <n> benchmark mismatches, <n> fix quality flags — worklist at _audit/TO_BE_RESOLVE.md`

If blocked:

- `AUDIT COMPILER PARTIAL — blocked on <precondition> — phase <N> not completed`

If timed out:

- `AUDIT COMPILER PARTIAL — time-box expired at day 2 — phases <list> incomplete — worklist at _audit/TO_BE_RESOLVE.md`

Begin with Phase 1 — build the file index.

**Read every dimension file. Group by file. Re-investigate every
finding. Write `TO_BE_RESOLVE.md`. Update statuses. Do not audit. Do
not resolve. Do not dispatch. Stop at Day 2.**

---

# What this compiler does

## Role

| Layer | Prompt | Reads | Writes |
|---|---|---|---|
| Audit | `PROMPT_FORENSIC_AUDIT.md` | codebase + benchmark | `_audit/dimensions/*.md` |
| **Compiler** | **this file** | `_audit/dimensions/*.md` | `_audit/TO_BE_RESOLVE.md` + status updates in dimensions |
| Resolver | `PROMPT_RESOLUTION_ORCHESTRATOR.md` | `_audit/TO_BE_RESOLVE.md` | codebase + status updates |

## Grouping

The audit groups by **dimension** (26 axes). The compiler groups by
**file** (one block per file). The resolver works **file-by-file**.

Why file-first:

1. A file has problems across many dimensions at once. Fixing them
   dimension-by-dimension means opening the same file 8 times.
2. The resolver's job is to open one file, see every problem for that
   file, fix them together, verify them together, and move on.
3. Phase ordering is preserved because each file has a phase.

## Status flow

```
audit writes:      NEW
compiler writes:   NEW → COMPILED
resolver writes:   COMPILED → RESOLVED
audit re-runs:     RESOLVED (leave) | INVALID (with evidence)
compiler re-runs:  NEW → COMPILED (new findings only)
loop continues
```

## The 11 subsections

| # | Subsection | Audit dimensions feeding it |
|---|---|---|
| 1 | Architectural | 01, 05, 18 |
| 2 | Technological | 02, 08 |
| 3 | Logical | 03, 19 |
| 4 | Database Wiring | 06, 10 |
| 5 | Table | 07 |
| 6 | Frontend Web | 14, 24 (web part) |
| 7 | Frontend Mobile | 15, 24 (mobile part) |
| 8 | Test File | 12 |
| 9 | Environmental | 11, 13 |
| 10 | Over All | 04, 09, 16, 17, 20, 21, 22, 23, 25, 26 |
| 11 | Feature Relation | 16 (relations only) |

## Cross-cutting findings

Findings that apply to ≥ 5 files, or have no single `File:Line`, or are
a config file that governs the whole codebase, go to the **Codebase
Implementation (Over All)** section — one block, same 11 subsections.

## Deliverable

`_audit/TO_BE_RESOLVE.md` — one file. Two sections:

1. **Section 1 — Per-file blocks.** One block per file. Each block has
   11 subsections. Each subsection has `Confirmation`, `Problem`,
   `Solution`.
2. **Section 2 — Codebase Implementation (Over All).** Cross-cutting
   findings. Same 11 subsections.
```

---

That is the complete **`PROMPT_AUDIT_COMPILER.md`**. It:

1. **Reads** the 26 dimension files.
2. **Groups** findings by file location (not by dimension, not by cluster).
3. **Re-investigates** each finding against the current source (second pass).
4. **Maps** the 26 audit dimensions into the 11 subsections you specified.
5. **Writes** `_audit/TO_BE_RESOLVE.md` with your exact template — per-file blocks with `Confirmation / Problem / Solution` per dimension, plus the `Codebase Implementation (Over All)` section.
6. **Updates** the `Status` column in every dimension file (`NEW → COMPILED`).
7. **Never** audits, never resolves, never dispatches.
8. **Loops** cleanly with the audit and resolver.
