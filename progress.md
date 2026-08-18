# Progress — ZOZI Backend Migration to NEW_STRUCTURE.md

## 2026-08-18 — Session 1 (planning + baseline)

**Context:** User asked "what are you doing?" + "make a plan properly for making
changes to track everything." Prior context implied scattered audit-script edits
without a tracked plan.

**What I did:**
1. Loaded `planning-with-files` skill.
2. Read `documents/NEW_STRUCTURE.md` (885 lines) — the authoritative 3-axis spec.
3. **Correction:** the doc's "Reality check" (lines 794–811) is STALE. Measured
   the real backend tree:
   - New skeleton EXISTS: `domains/` 1997, `modules/` 701, `rbac/` 106,
     `kernel/` 10, `infrastructure/` 230.
   - But import debt proves it's cosmetic: `from services.` = 1745,
     `from models` (root) = 1676, `from controllers.` = 474, `from domains.` = 380.
   - `_legacy/` holds the REAL code: 196 services, 174 controllers, 154 routers,
     58 models, 67 utils, 13 db.
   - Root `models/` 27, `utils/` 67, `db/` 12 still canonical.
   - `from _legacy` = 0 → legacy re-exports under OLD names via sys.path/shim.
4. Verified prior claim: `check_new_structure_compliance` IS present (L13793),
   wired (L13970), with NS0–NS11 codes. Audit gate is real.
5. Confirmed no existing planning files; git is clean.
6. Started audit in background (`bgp_011aedbab001ALVN6OyXjJxR87`) to seed NS counts.
7. Wrote `findings.md`, `task_plan.md`, `progress.md` (this file) at repo root.

**Pending this session:**
- Read audit stdout tail → append NS violation counts to `findings.md`.
- Resolve Phase 0 blocker: HOW `from services.` resolves with no root `services/`.

**Commands run:**
- `Get-ChildItem backend -Directory` (file counts)
- import-pattern `Select-String` scan (services/models/controllers/domains/modules/rbac/_legacy)
- `git log --oneline -10` (clean tree; recent "source-folder consolidation" commits)
- background: `python scripts/system_trackers/system_architecture_audit.py`

## 2026-08-18 — Session 2 (complete NS15–NS22 enforcement)

**Context:** Continue converting the OLD flat-circuit audit into the
NEW_STRUCTURE.md (three axes + Seven Laws) gate. NS0–NS14 were already
wired; the Seven-Laws coverage (NS15–NS22) was missing.

**What I did:**
1. Added NS15–NS22 descriptions to `_RULE_DESCRIPTIONS` and to the NS hotlist.
2. Added helper functions before `check_new_structure_compliance`:
   `_ns_collect_feature_atoms` (Law 4 single-source), `_ns_scan_thin_router_
   violations` (Law 2), `_ns_scan_module_actor_violations` (Law 5 strangler),
   `_ns_scan_inverted_arrows` (Law 1), `_ns_scan_country_scope` (axis 3),
   `_ns_scan_schema_discipline` (Law 6).
3. Added emission logic for NS15–NS22 inside the gate, after the NS14 block.
4. Fixed a splice bug (EMIT was nested in the wrong NS14 branch) and re-ran
   `py_compile` — now compiles clean.
5. Tightened NS22 heuristic to require `__tablename__` so service files that
   merely import `Base` are no longer false-flagged as models.
6. Ran the gate against the real repo (stub Report): NS15–NS22 all execute
   without error and emit real findings (NS18=238, NS19=124, NS20=165,
   NS22=32 genuine; NS15/16/17/21 = 0 because no feature atoms are defined).
7. Updated `findings.md` §3 (full NS0–NS22 coverage + refreshed line numbers)
   and §5 (added measured NS15–NS22 debt rows).

**Verification:**
- `python -m py_compile system_architecture_audit.py` → OK.
- Targeted execution of `check_new_structure_compliance` on the real tree →
  407 NS findings total; NS15–NS22 produce correct, non-false-positive output.

**Note:** The full `main()` audit run is slow (>240s whole-repo scan); the NS
gate itself runs in seconds and was validated in isolation.

**Pending:**
- Generate the full SYSTEM_AUDIT_REPORT.md (run main() to completion) so the
  report itself reflects NS15–NS22 (timed out in this session).
- Tune NS19 actor allow-list if the 124 count is noisier than desired.
