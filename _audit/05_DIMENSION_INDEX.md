# ZOZI Forensic Audit — Dimension Index

**Compiled:** 2026-10-01
**Source:** `_audit/dimensions/*.md` (28+ dimension files present)
**Scope of this file:** index only. No source files were read outside `_audit/**` and none were modified.

---

## 1. Coverage Status

| # | Dimension | File | Findings | Schema | Completion |
|---|-----------|------|----------|--------|------------|
| 01 | Architectural | `dimensions/01_architectural.md` | 14 | tabular | COMPLETE |
| 02 | Technological | `dimensions/02_technological.md` | 53 | tabular | COMPLETE |
| 03 | Logical | `dimensions/03_logical.md` | 18 | tabular | COMPLETE |
| 04 | Operational | `dimensions/04_operational.md` | 10 | tabular | COMPLETE |
| 05 | Wiring | `dimensions/05_wiring.md` | 8 | tabular | COMPLETE |
| 06 | Database | `dimensions/06_database.md` | 8 | tabular | COMPLETE |
| 07 | Tables & Fields | `dimensions/07_tables_fields.md` | 272 | tabular | COMPLETE |
| 08 | Providers | `dimensions/08_providers.md` | 8 cross-cutting | narrative | COMPLETE |
| 09 | Laws | `dimensions/09_laws.md` | 23 law violations | law table | COMPLETE |
| 15 | Frontend Mobile | `dimensions/15_frontend_mobile.md` | 9 | tabular | COMPLETE |
| 16 | Features | `dimensions/16_features.md` | 42 | tabular | COMPLETE |
| 18 | Security | `dimensions/18_security.md` | 12 | tabular | COMPLETE |
| 19 | Performance | `dimensions/19_performance.md` | 9 | tabular | COMPLETE |
| 27 | Project Completion Blockers | `dimensions/27_project_completion_blockers.md` | 9 | tabular | COMPLETE |

All dimension files present on disk are complete: each carries a populated findings section and a summary declaring `COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0`. No file contains a pending/placeholder/draft marker.

---

## 2. Aggregate Totals

Counts below are summed from the 12 tabular-schema dimensions (464 rows), which is the only set with a uniform row schema.

| Metric | Value |
|--------|-------|
| Tabular findings | **464** |
| P0 | 55 |
| P1 | 154 |
| P2 | 233 |
| P3 | 22 |
| Completion blockers (yes) | 134 |
| Completion blockers (partial) | 11 |
| Not blockers | 319 |

Verified: P0+P1+P2+P3 = 464 = findings; blockers yes+partial+no = 464 = findings.

**Non-tabular findings are excluded from the totals above** to preserve a single consistent counting basis:

- `09_laws.md` — 23 law violations across 325 laws (5 flagged as project completion blockers)
- `08_providers.md` — 8 cross-cutting provider findings (0 blockers)

---

## 3. Per-Dimension Detail

| # | Dimension | Inspected | Compliant | w/ findings | Findings | P0 | P1 | P2 | P3 | Clusters | Conf. | Evidence | Blockers (y/p/n) |
|---|-----------|-----------|-----------|-------------|----------|----|----|----|----|----------|-------|----------|------------------|
| 01 | Architectural | 240+ files | N/A | 18+ | 14 | 4 | 6 | 3 | 1 | 4 | 4.5 | triangulated | 4 / 0 / 10 |
| 02 | Technological | 12 files | 0 | 12 | 53 | 15 | 35 | 3 | 0 | 8 | 4.8 | triangulated | 15 / 0 / 38 |
| 03 | Logical | 47 files | 12 | 35 | 18 | 4 | 6 | 5 | 3 | 3 | 4.4 | multiple | 4 / 2 / 12 |
| 04 | Operational | 18 files | 6 | 12 | 10 | 2 | 3 | 3 | 2 | 2 | 4.5 | multiple | 2 / 0 / 8 |
| 05 | Wiring | 18 files | 6 | 12 | 8 | 2 | 2 | 2 | 2 | 2 | 4.5 | multiple | 2 / 2 / 4 |
| 06 | Database | 12 files | 4 | 8 | 8 | 3 | 2 | 2 | 1 | 3 | 4.5 | multiple | 4 / 0 / 4 |
| 07 | Tables & Fields | 343 tables | 142 | 201 | 272 | 1 | 77 | 194 | 0 | 0 | 5.0 | triangulated | 78 / 0 / 194 |
| 08 | Providers | ~55 modules / 17 subpackages | n/a | n/a | 8 | — | — | — | — | — | — | — | 0 / 0 / 8 |
| 09 | Laws | 325 laws | 302 | 23 | 23 | — | — | — | — | — | — | — | 5 / 0 / 18 |
| 15 | Frontend Mobile | 18 files | 9 | 9 | 9 | 0 | 2 | 4 | 3 | 2 | 4.0 | single | 1 / 0 / 8 |
| 16 | Features | 42 files | 0 | 42 | 42 | 8 | 14 | 12 | 8 | 6 | 4.0 | multiple | 8 / 6 / 28 |
| 18 | Security | 47 files | 12 | 35 | 12 | 5 | 4 | 2 | 1 | 2 | 4.6 | multiple | 5 / 1 / 6 |
| 19 | Performance | 30 files | 18 | 12 | 9 | 2 | 3 | 3 | 1 | 2 | 4.0 | multiple | 2 / 0 / 7 |
| 27 | Completion Blockers | 14 files | 3 | 11 | 9 | 9 | 0 | 0 | 0 | 0 | 5.0 | triangulated | 9 / 0 / 0 |

Every dimension with a confirmation verdict reports **FAIL**. No dimension passed.

---

## 4. Finding ID Prefix Map

| Prefix | Dimension | Count | ID range |
|--------|-----------|-------|----------|
| `ARCH` | 01 Architectural | 14 | ARCH-001…014 |
| `TECH` | 02 Technological | 53 | TECH-001…053 |
| `LOGIC` | 03 Logical | 18 | LOGIC-001…018 |
| `OPS` | 04 Operational | 10 | OPS-001…010 |
| `WIRE` | 05 Wiring | 8 | WIRE-001…008 |
| `DB` | 06 Database | 8 | DB-001…008 |
| `TF` | 07 Tables & Fields | 272 | TF-001…272 |
| `FIND-09` | 09 Laws | 23 | FIND-09-001…023 |
| `MOB` | 15 Frontend Mobile | 9 | MOB-001…009 |
| `FEAT` | 16 Features | 42 | FEAT-001…042 |
| `SEC` | 18 Security | 12 | SEC-001…012 |
| `PERF` | 19 Performance | 9 | PERF-001…009 |
| `BLOCKER` | 27 Completion Blockers | 9 | BLOCKER-001…009 |

Dimension 08 (Providers) uses narrative `Finding 1`…`Finding 8` headings with severity labels, not an ID series.

`CHAIN` IDs are **not owned by any dimension file**. They originate in `_audit/10_CHAINS.md` and appear as cross-references inside dimensions 03, 04, 05, 06, 16, 18, 19.

---

## 5. Supporting Artifacts (outside `dimensions/`)

| File | Role |
|------|------|
| `00_README.md` | Directory README — **stale**, still describes Phase 0 only (3 PASS / 2 FAIL, 9 blockers) and lists only one dimension file |
| `03_FEATURE_STACK_DRAFT.md` | Feature stack draft (62 KB) |
| `07_CONTRADICTIONS.md` | Contradiction log |
| `09_ANTI_PATTERNS.md` | Anti-pattern catalog |
| `10_CHAINS.md` | End-to-end chain audit; source of `CHAIN-*` IDs |
| `logs/` | Per-dimension JSONL execution logs, `phase0_results.md`, `checkpoint.json` |

All 14 dimension files have a matching `logs/<name>.jsonl`. Files `anti_patterns.jsonl`, `chains.jsonl`, `contradictions.jsonl`, `feature_stack.jsonl` back the root-level artifacts above.

---

## 6. Cross-Dimension Law Overlap

37 laws are implicated in more than one dimension, indicating shared root causes rather than independent defects.

**Implicated in 3 dimensions:**

| Law | Dimensions |
|-----|-----------|
| L-3 | 01, 05, 16 |
| L-5 | 05, 07, 16 |
| L-19 | 03, 07, 16 |
| L-30 | 02, 04, 16 |
| L-45 | 06, 16, 19 |
| L-53 | 06, 07, 19 |
| L-55 | 06, 07, 16 |
| L-96 | 03, 16, 27 |

**Implicated in 2 dimensions:** L-1, L-2, L-6, L-14, L-23, L-34, L-37, L-40, L-41, L-42, L-44, L-46, L-47, L-48, L-49, L-50, L-54, L-56, L-60, L-84, L-87, L-88, L-90, L-102a, L-123, L-228, L-229, L-248, L-291.

**Cluster overlap across dimensions:** only `idempotency` and `silent-except` (both 03 ↔ 16) use identical cluster names in two dimensions. Other clusters are dimension-local even where the underlying defect looks the same (e.g. N+1 lazy-loading appears as `CLUSTER-n1-relationships` in 06 and `CLUSTER-n-plus-1-lazy` in 19; migration divergence as `CLUSTER-migration-divergent` in 06 and `CLUSTER-divergent-migration` in 27).

---

## 7. Data-Quality Notes and Internal Contradictions

Flagged for the compiler phase; not resolved here.

1. **Divergent migration head count disagrees.** `06_database.md` DB-001 reports **62** divergent heads (parsed from `down_revision` tuples); `27_project_completion_blockers.md` BLOCKER-007 reports **5** heads, with specific revision IDs (`20260930_0002/0003/0006/0007`, `20261001_0001`). Both are P0, both cite Law 49. One figure is wrong.
2. **"Files with findings" exceeds finding count.** `18_security.md` declares 35 files with findings but only 12 findings; `19_performance.md` declares 12 files with findings but 9 findings. Most likely multiple findings collapse onto the same file, but the summaries read as if one finding per file.
3. **FEAT-008 records a compliant item as a finding.** In `16_features.md`, FEAT-008 states a feature gate is *present* and its Delta is "Feature gate present — compliant", Fix "None", Effort "—", Priority "—", yet it is counted in the 42 total with `Status: NEW`. Effective feature finding count is likely 41, and P0/P1/P2/P3 (8/14/12/8 = 42) may be similarly inflated.
4. **README status is stale.** `00_README.md` reports 9 completion blockers; the dimension files declare 134 blocker-yes (tabular) plus 5 in `09_laws.md`.
5. **Dimension numbering has gaps** (10–14, 17, 20–26), but per the §1 warning these are **working-tree deletions of previously committed reports**, not deferred or out-of-scope dimensions. Coverage totals in §2 and §3 are therefore incomplete with respect to the original audit scope. The same applies to the 5 other root artifacts and `_audit/resolver/`.
6. **Cluster naming is not normalized across dimensions**, so cluster counts cannot be aggregated into a project-wide figure (§6).
7. **`09_laws.md` has no priority breakdown** (no P0–P3 split for its 23 violations), unlike the 12 tabular dimensions.

---

## 8. Compilation Basis

- Row counts for each of the 12 tabular dimensions were recounted from the files and match each file's declared `Findings:` total exactly.
- Priority and blocker totals were summed per file from the `## Summary` blocks and reconcile to the finding count in both cases.
- Files 08 and 09 are indexed but excluded from numeric rollups (§2), as their schemas differ.
- Working-tree state was checked against git HEAD (`6666d435`); 19 dimension files and 12 other `_audit/` artifacts are deleted on disk and are excluded from this index.
- No file in `_audit/dimensions/` was created, edited, or deleted in producing this index. `_audit/DIMENSION_INDEX.md` is the only file written.
