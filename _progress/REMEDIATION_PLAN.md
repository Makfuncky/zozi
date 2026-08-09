# ZOZI Remediation Plan — Clearing Audit Violations (CURRENT STATE)

> Last updated: 2026-08-06 · Source of truth: `SYSTEM_AUDIT_REPORT.md` (read-only, DO NOT regenerate)
> Scope decision (user): clear all 🔴 REDs, then execute the user-selected 🟡 MEDIUM area **"Circuit/structure hygiene"**.

## 0. Current state (verified this session)
- Audit snapshot: 🔴 **3** violations · 🟡 **~3507** advisories · 🟢 49 info.
- **DBA06 cross-schema FKs: 0** (`out/cross_schema_fk_analysis.json` → `total_count: 0`). Fully cleared in prior sessions.
- `import main` → **1421 routes**. App boots; country + DBA06 regression tests green.
- ⚠️ Governance note: the report's headline numbers changed since the prior plan (was 🔴221/🟡3902). The report appears to have been **regenerated** at some point despite the "read-only" rule. We treat its current contents as authoritative and do NOT regenerate it ourselves.

## 1. RED inventory (3 total) — ALL RESOLVED (no code change required)
| Code | Sev | Count | Verdict (evidence) |
|---|---|---:|---|
| F5 | 🔴 | 1 | `backend/.env` — `git status` shows **untracked**; `git check-ignore` confirms **gitignored**. No secret in VCS. **Resolved.** |
| DBA02 | 🔴 | 2 | `2026_08_06_0001_add_analytics_audit_columns.py:22` — `create_all` appears **only inside a docstring** (no call). `2026_08_06_0001_media_add_audit_softdelete_mixins_and_rename_ai_result.py` — `create_all` appears **nowhere**. Both **FALSE POSITIVES**. |
| — | — | — | The one migration with a real `create_all()` (`2026_07_26_baseline_canonical_...`) is gated behind `_database_has_tables()` (fresh-DB only) — which is exactly why the audit did NOT flag it. |

**Net: 0 actionable REDs.** The 3 reported REDs are gitignore/triage + docstring false positives.

## 2. MEDIUM area — "Circuit/structure hygiene" (user-selected)
Families involved: **API2 (100), DG2 (25), CA2 (100), CIR2 (106), W4 (30), DOM2 (13)** = ~374 advisory findings.

### 2.1 Diagnosis (evidence-based, this session)
| Family | Count | Reality on inspection | Safe to bulk-fix? |
|---|---:|---|---|
| **API2** | 100 | Audited "leaks" are **local redefinitions**, not cross-module imports. e.g. `_ALLOWED_TABLES` is defined in `chat_enrichment.py` **and** separately in `api_comms_console.py`; `_BACKEND_ROOT` is defined in `utils/schema_audit.py` **and** `tests/conftest.py`. The audit's "used in N external modules" is a **false heuristic** (matches the symbol name anywhere, incl. local redefs). | ❌ No — renaming would be cosmetic churn + breakage risk, zero real benefit. |
| **DG2** | 25 | Benign `__init__.py` re-export cycles (`models.geography -> models.geography.country_basics -> models.geography`). Python tolerates these; "fixing" risks import regressions. | ❌ No — deferred; only act if a real import error appears. |
| **CA2** | 100 | Heuristic multi-domain "split candidates" (e.g. `cash_management_service.py` touches 7 keyword-domains). Splitting is a large, risky refactor. | ❌ No — deferred to a deliberate per-file program. |
| **CIR2** | 106 | Router→service / controller→controller calls. The audit **explicitly permits** these during the bounded-context migration (routers may call controllers/services/utils). | ❌ No — systemic/deferred. |
| **W4** | 30 | Controller→controller calls, same migration-permitted exemption. | ❌ No — systemic/deferred. |
| **DOM2** | 13 | Concrete file-move suggestions (e.g. `models/communication/suppliers.py` → `models/supplier/`). Keyword heuristics are sometimes weak (`services/commerce/cross_border_tracker.py` → `geography` b/c "border"). Moves need import-graph updates. | ⚠️ Partial — only the *unambiguous* ones, with `import main` gate. |

### 2.2 Conclusion
The MEDIUM "Circuit/structure hygiene" field is **dominated by heuristic noise and systemic/migration-permitted items**. There is **no safe mechanical bulk remediation** that wouldn't risk the 1421-route app. The only genuinely actionable, low-risk slice is a **subset of DOM2** (unambiguous wrong-folder moves), executed one file at a time behind the validation gate.

### 2.3 Recommended execution (scoped, human-reviewed)
1. **DOM2 — unambiguous moves only** (per-file, validate after each):
   - `backend/models/communication/suppliers.py` → `backend/models/supplier/` (clear: suppliers belong to supplier domain).
   - `backend/models/communication/core.py` → `backend/models/core/` (clear).
   - `backend/providers/catalog/text.py` → `backend/providers/ai/` (clear: text/AI provider).
   - `backend/services/customer/customer_router_service.py` → `backend/services/commerce/` (clear).
   - *Defer ambiguous ones* (`cross_border_tracker`, `geo_*` services that legitimately touch geography) pending review.
2. **Everything else (API2/DG2/CA2/CIR2/W4)**: leave as-is; document as systemic/heuristic in triage. Address only via a future, deliberate per-feature refactor program — not in a single pass.

## 3. Validation gate (EVERY change)
1. `python -c "import main"` succeeds → **1421 routes** (unchanged).
2. `out/cross_schema_fk_analysis.json` stays `{"total_count": 0}`.
3. `pytest tests/` regression green (at minimum country + DBA06 rescue tests).
4. No import chain broken; file moves update `models/__init__.py`, domain `__init__.py`, and all importers (grep the old path → 0 hits).

## 4. Constraints (from AGENTS.md)
- NEVER modify `scripts/`, `SYSTEM_AUDIT_REPORT.md`, or `backend/main.py` router registration.
- NEVER delete a file before confirming zero imports; NEVER break an import chain.
- Do NOT regenerate the audit report (it is the source of truth as-is).
- No hardcoded values — config from environment.
- Do NOT `git add -A && git commit`; git tree is heavily modified.

## 5. Definition of done (this phase)
- 3 reported REDs documented as resolved (gitignore/triage + false positives).
- DOM2 unambiguous moves applied with validation gate green.
- MEDIUM heuristic/systemic families explicitly deferred with evidence.
- `import main` stays 1421 routes; cross-schema FK count stays 0.

## 6. Execution log (this session)
- **RED triage (all 3):** verified resolved, no code change.
  - F5 `backend/.env`: untracked + gitignored (git check-ignore confirmed).
  - DBA02 ×2: `create_all` only in docstring / absent (grep-proven); baseline migration's real `create_all` is fresh-DB gated.
- **DOM2 — MOVE #1 executed & validated:** `backend/models/communication/suppliers.py` → `backend/models/supplier/suppliers.py`.
  - Edits: `models/_exports.py` (`from .communication.suppliers import *` → `from .supplier.suppliers import *`); `models/__init__.py` shim tuples — dropped `"suppliers"` from `communication` list, added to `supplier` list so `models.supplier.<SupplierModel>` stays populated.
  - Validation gate: `import main` → **1421 routes (unchanged)**; `models.<Supplier*>` and `models.supplier.<Supplier*>` both resolve; **0** stale `communication.suppliers` references; country model tests 115 passed.
  - Note: 4 `test_country_auto_populate.py` *Integration* tests FAIL, but are **pre-existing** — they patch `country_auto_populate._get_redis` which does not exist in that module (redis code removed). Unrelated to this move; out of scope.
- **DOM2 — RESOLUTION #2 (this session):** `services/customer/customer_router_service.py`.
  - Discovered BOTH `services/customer/` and `services/commerce/` held **byte-identical** copies; only importer (`routers/api_customer_routes.py`) uses the `commerce/` copy. Deleted the stale `customer/` duplicate.
  - ⚠️ Lesson: `git checkout -- <file>` on an uncommitted working-tree file reverts to HEAD (which can be a stale/short version). After a failed delete of `providers/catalog/text.py` dropped routes to 1400, `git checkout` restored a truncated shim; clearing `__pycache__` + re-import confirmed HEAD's version was actually sufficient (1421). Prefer reconstructing/verifying over blind `git checkout`.
  - Validation: `import main` → **1421 routes**.
- **DOM2 — RESOLUTION #3 (this session):** `providers/catalog/text.py` (required compat shim, NOT redundant).
  - `providers/catalog/parcel_verification.py:42` did `from .text import ollama_vision_chat, _extract_json` (relative import — missed by `catalog\.text` grep). Repointed to `from providers.ai.text import ollama_vision_chat, _extract_json`, then deleted the shim. Real module `providers.ai.text` already in correct domain.
  - Validation: `import main` → **1421 routes**; `parcel_verification` imports resolve.
- **DOM2 — RESOLUTION #4 (this session):** `models/communication/core.py` (pure 2-line shim → `models.comms.core`).
  - Repointed `models/_exports.py` (`from .communication.core import *` → `from .comms.core import *`) and `models/__init__.py` shim: `_cross_exports` `("core", ("communication.core",))` → `("core", ("comms.core",))`, and dropped `"core"` from the `communication` shim list. Deleted the shim.
  - Validation: `import main` → **1421 routes**; `models.<model>` and `models.core.<core-domain model>` (Address/Cart/etc.) both resolve; **0** stale `communication.core` references.
  - Note: `models.comms.core` holds core-domain models (Address, Cart…), not `Message` (a communication model) — so `models.core.Message` was never set; no regression.
- **DOM2 status:** 4 of 13 findings resolved (all "unambiguous" ones from the plan's queue). Remaining 9 are **ambiguous/weak-keyword** (e.g. `services/commerce/cross_border_tracker.py` flagged as geography, `services/logistics/geo_fence_service.py` as geography) — each needs individual investigation; several are likely legitimate placements or shims. Deferred to a per-file review pass.
- **Deferred (heuristic/systemic, no safe mechanical fix):** API2 (local redefinitions misread as cross-module leaks — grep-proven), DG2 (`__init__` re-export cycles, benign), CA2 (keyword split candidates), CIR2/W4 (migration-permitted). Do NOT bulk-edit.

## 7. Triage log (false-positives / systemic)
- **F5**: untracked + gitignored → no committed secret.
- **DBA02 ×2**: docstring-only / absent `create_all` → false positive.
- **API2**: local redefinitions misread as cross-module leaks → false positive on inspection (grep proves no external import).
- **DG2**: `__init__.py` re-export cycles → benign.
- **CIR2 / W4**: migration-permitted router/controller calls → systemic/deferred.
- **CA2**: keyword-based split candidates → heuristic/deferred.
