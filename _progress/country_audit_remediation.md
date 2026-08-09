## Goal
- Accumulate all `country`-management problems from the 4 audit reports, verify each against the codebase, then resolve the real ones sequentially (DB04, QUAL1, DB07/DB08, DB31, REG1, HL302-remaining done; structural/governance deferred).

## Constraints & Preferences
- NEVER modify files inside `scripts/` (audit scripts read-only).
- NEVER modify the four audit report `.md` files (regenerate via scripts only).
- NEVER delete a file before confirming zero imports reference it.
- NEVER rename/move a file without updating ALL imports atomically.
- NEVER break an import chain.
- Avoid `git add -A && git commit -m` unless asked.
- Run app + tests after each change.
- Report false-positive audit detections in detail instead of editing scripts.

## Progress
### Done
- HEALTH RED 0 (score 70): SEC101 fixed earlier in misc_write_service.py + command_center_service.py.
- ARCHITECTURE RED 0; deleted gitignored runtime DB backend/zozi.db.
- Cleaned orphan F4 artifacts (cross_schema_fk_analysis.json git rm + relocate to out/; deleted _verify.db).
- Re-ran audits: ARCHITECTURE 🔴0/🟡1006, HEALTH 🔴0/🟡1205, DESIGN 🔴0, DATABASE 🔴172 (all DB06).
- Accumulated + verified ALL country findings across DATABASE/HEALTH/ARCHITECTURE reports; DESIGN had no country matches.
- **DB04 RESOLVED**: payments.py:229 PayrollRecord.country_code String(10)→String(3).
- **DB07/DB08 RESOLVED**: country_control.py all 9 country_code FKs + 3 user FKs → index=True, ondelete="RESTRICT".
- **QUAL1 + HL302 RESOLVED (all swallowed exceptions in country files now logged)**:
  - country_detection.py (service): GeoIP2 :98, ipapi :109, default_country :123, coordinate :142 — all logger.debug (prior).
  - country_detection.py (middleware) :46 — db.close finally logged (prior).
  - country_context.py: RLS setup :191, Redis get :361, Redis set :369, RLS session :197, RLS scope :272, JWT decode :85 (logs generic warning) — all logger.debug / warning.
  - country_ai_research.py: gdp parse :469 (prior), JSON parse :515 + fallback :520 → logger.debug (this turn).
  - country_controller.py: fallback city parser :1430 (prior), _country_public_payload city count :231 → logger.debug (this turn); _to_decimal :164 re-raises HTTPException (not swallowed).
  - Added `logging`+`logger` to country_controller.py (also OB101).
- **DB31 RESOLVED**: composite `Index("ix_*_country_created", "country_code", "created_at")` on 23 country-domain tables (8 in countries.py, 15 in country_enhancements.py); schema dict placed LAST in __table_args__ (7 blocks fixed for ordering).
- **REG1 RESOLVED (this turn)**: added `country_read_service` domain to documents/scope/domains.yaml (owner @zozi/country_read_service, depends_on country). Mirrors existing `@zozi/...` owner convention (PyYAML rejects `@` but audit tool tolerates it).
- **API1 RESOLVED (this turn, user-selected)**: added docstrings to the 3 flagged country classes — CountryAIResearchService (country_ai_research.py:336), CountryDetectionService (country_detection.py:33), CountryProviderSettings (providers/country/country.py:12). All three py_compile OK.
- Verified false-positive country findings + documented (HL601/HL602, A2, API2, PERF4, HL204:85).
- Validated country models load cleanly: all 23 targeted `_country_created` indexes present in Base.metadata; edited Python files py_compile OK.

### In Progress
- (none)

### Blocked
- (none) — all low-risk/verifiable country findings resolved; remaining items are structural/architectural (await ADR / user direction).

## Key Decisions
- F4 artifacts: cross_schema_fk_analysis.json generated only by analyze_fks.py (no imports) → git rm + relocate output to out/.
- DATABASE DB06 (172 RED) = cross-schema FKs intentional per ADR-019 (documents/scope/05_ORDERS.md:86) → kept, not edited.
- HL601/HL602 FALSE POSITIVE: country_ai_research.py has httpx.Timeout(30.0, connect=10.0); country_data_orchestrator.py has aiohttp.ClientTimeout(total=30); country_detection.py/context.py use urllib urlopen(timeout=5).
- A2 (country_auto_populate.py) FALSE POSITIVE: runtime entrypoint.
- API2 (_country_public_payload, _extract_ip) FALSE POSITIVE: intentional cross-module reuse.
- PERF4 (.all() in country_read_service.py) FALSE POSITIVE: bounded admin helpers.
- HL204 (country_context.py:85) FALSE POSITIVE: logs generic warning "Failed to decode JWT…", no secret/PII leaked.
- country_controller.py:164 (_to_decimal) HL302 FALSE POSITIVE: re-raises HTTPException(422) — propagates, not swallowed.
- **SQLAlchemy __table_args__ ordering**: `{"schema": ...}` dict MUST be LAST; first position raises ArgumentError.
- **`backend/tests/test_orders.py` ERRORs with `ModuleNotFoundError: services.orders.order_payment_functions`** — PRE-EXISTING + UNRELATED to country work: file moved to services/finance/order_payment_functions.py in DOM3 refactor (commit 5f67971) but services/orders/__init__.py:9 still imports old path. git status confirms only countries.py + country_enhancements.py + the 3 country files + domains.yaml touched by me.
- Validation needs env `SECRET_KEY`; FIELD_ENCRYPTION_KEY warning benign.
- domains.yaml `@zozi/...` owner values are invalid per strict PyYAML but the audit generator writes them and the audit tool reads them; my REG1 addition follows the same convention.

## Next Steps
- Pick next structural/quality country item (see Blocked/In Progress). Candidates:
  - DB32 — cursor-based pagination in 6 country services (country_dropdown_service, country_maps_service, country_router_service, country_staff_service, country_tax_service, cross_border_service). Changes return types → API contract change.
  - DB05 — RLS consolidation: keep ONE canonical enforcer (L1), cover 12 missing country-scoped tables in pg_rls_policies.sql. Security; needs RLS runtime test.
  - SYM1 — dead-code symbols (CountryDetectionMiddleware, CountryRLSService, CountryProviderSettings, ExternalAPIFetcher, ConfidenceScoringEngine, CountryAccessScope, EnhancedGeoBlockingMiddleware, CountryScopedRepository, etc.). MUST verify usages first — many likely dynamically registered (partial FPs).
  - SYM2 — rename colliding `add_country_city` (2 mods) / `add_to_session` (4 mods) to avoid confusion (breaks imports if renamed).
  - CA2 — split CA2-flagged country files by domain (large refactor, import churn).
  - CIR2 — wire routers→controllers (remove router→service bypass).
  - DOM7 — rename country/ → geography/ across models/providers/services/controllers (massive; needs ADR + mass import update + migration).
  - DG2 — break models → _exports → country_basics → country → models circular import.
  - MR104 — global mutable state (likely module constants; verify FP).
  - HL801 — add timing/metrics to hot country functions (nice-to-have).
  - API1 — add docstrings to 3 country classes (zero-risk, minor).
  - FE6/FE7 — frontend console.debug cleanup + component import-from-ui (frontend).
- Fix pre-existing dangling import in services/orders/__init__.py (point to services.finance.order_payment_functions) — NOT a country task; only if asked.
- Optionally re-run DATABASE/HEALTH/ARCHITECTURE audits to confirm DB04/QUAL1/HL302/DB07/DB08/DB31/REG1 cleared (regenerates reports + touches _extra_files/; not committed).
- Final commit only if user requests (avoid git add -A && git commit -m).

## Critical Context
- Current audit results: DATABASE 🔴172 (all DB06) / 🟡1156; DESIGN 🔴0 / 🟡158; HEALTH 🔴0 / 🟡1205 (score 70); ARCHITECTURE 🔴0 / 🟡1006.
- Country model files: backend/models/country/countries.py (8 index tables), backend/models/country/country_enhancements.py (15 index tables).
- DB31: 23 composite indexes `Index("ix_<table>_country_created", "country_code", "created_at")`; schema dict LAST. Validation counted 26 total (incl. 3 pre-existing other-schema tables: customs_entries, import_shipments, landed_cost_allocations) — all 23 targeted present.
- HEALTH country codes: HL204 (FP), HL302 (resolved), HL601 (FP), HL602 (FP), HL801 (metrics), MR104 (global state).
- Test command: `cd backend; python -m pytest tests\test_orders.py -q` (PowerShell `;` not `&&`; `> log 2>&1` + large timeout). Currently fails pre-existing ModuleNotFoundError at services/orders/__init__.py:9.
- Model import validation: `cd backend; $env:SECRET_KEY="test-secret-key-for-validation-only"; python -c "from models.country import countries, country_enhancements; ..."`.
- domains.yaml: human-overridable registry (comment line 3); REG1 entry added at lines 115-118.
- git status shows audit side-effects (HEALTH_AUDIT_REPORT.md, DESIGN_AUDIT_REPORT.md, .governance/*, _extra_files/ deletions) + a big orders DOM3 refactor with renames (routers/orders.py → routers/api_orders_routes_2.py, etc.) — not my changes, NOT committed.
- Running audits regenerates reports + side-effect deletions in _extra_files/.

## Relevant Files
- documents/scope/domains.yaml:115: REG1 fixed (added country_read_service domain, depends_on country).
- backend/services/country/country_ai_research.py:515,520: HL302 fixed (JSON parse logging); :469 gdp parse (prior); HL601/HL602 FP.
- backend/controllers/country/country_controller.py:231: HL302 fixed (city count logging); :1430 prior; :164 re-raises (HL302 FP); logger at :12.
- backend/services/country/country_detection.py:98,109,123,142: HL302 already logged (prior).
- backend/middleware/country_context.py:85 (HL204 FP, generic warning), :191/:197/:272/:361/:369 (HL302 logged).
- backend/models/finance/payments.py:229: DB04 fixed.
- backend/models/logistics/country_control.py: DB07/DB08 fixed.
- backend/models/country/countries.py + country_enhancements.py: DB31 fixed (23 indexes).
- backend/services/country/country_data_orchestrator.py: HL601/HL602 FP (aiohttp.ClientTimeout).
- backend/services/country/country_auto_populate.py: ARCH A2 FP (runtime entrypoint).
- backend/services/supplier/supplier_countries_service.py:163: API2 FP.
- backend/services/country/country_detection.py:60: API2 FP.
- backend/services/country_read_service.py: PERF4 FP; MV1/DOM6 candidate.
- services/orders/__init__.py:9: PRE-EXISTING dangling import (ModuleNotFoundError) — unrelated to country work.
- services/finance/order_payment_functions.py: moved target of above (DOM3 refactor commit 5f67971).
- documents/scope/05_ORDERS.md:86: ADR-019 (DB06 intentional cross-schema FKs).
- DATABASE_AUDIT_REPORT.md, HEALTH_AUDIT_REPORT.md, ARCHITECTURE_AUDIT_REPORT.md, DESIGN_AUDIT_REPORT.md: country findings source (not modified).
- backend/tests/test_orders.py: regression suite; currently ERRORs on pre-existing ModuleNotFoundError (not from country edits).
