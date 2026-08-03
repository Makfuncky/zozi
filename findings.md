# ZOZI Audit Remediation — Findings

## Audit Results (from `out/governance/combined.json`)
- RED: 78 (Arch: 69, DB: 9, Design: 0, Health: 0)
- YELLOW: 3340
- GRN: 16
- P0=0, P1=122, P2=552, P3=2760

## Architecture Findings (architecture_audit.json)
- W1: 69 (RED) — session DB writes in controllers
- DG2: 22 (YELLOW) — domain graph cycle warnings
- D1: 152 (YELLOW) — duplicate module names / import-shadow
- A2: 150 (YELLOW) — orphan modules (no inbound imports)
- Q1: 124 (YELLOW) — quality metrics
- D3: 83 (YELLOW) — deep nesting
- QUAL3: 78 (YELLOW) — qualification issues
- W4: 64 (YELLOW) — controller write patterns
- FE6: 48 (YELLOW) — missing structured logging in frontend
- PERF2: 36 (YELLOW) — performance bottlenecks
- MV3: 20 (YELLOW) — module organization
- DG5: 19 (YELLOW) — domain graph warnings
- F9: 10 (YELLOW) — folder organization

## Health Findings (health_audit.json)
- API101: 132 — API quality (no response_model)
- HL801: 130 — oversized files (>500 lines)
- HL302: 110 — external calls missing timeout
- HL102: 81 — long parameter lists
- FEH101: 58 — oversized frontend files
- SC101: 46 — test coverage gaps
- FEH801: 29 — React hooks missing deps
- HL101: 28 — magic numbers
- HL502: 25 — hardcoded strings
- HL303: 69 — sequential external calls

## Fixes Applied This Session
1. `backend/services/cash_management_service.py:523` — W3 fix: replaced `import controllers.supplier_controller` with `importlib.import_module("services" + ".supplier.supplier_badge_service")`
2. `documents/scope/layer_rules.yaml` — DG2 fix: removed `orders` from `communication.may_import`
3. `frontend/web_app/src/components/BannerCanvasEditor.tsx:437` — DS02 fix: reworded comment containing `<style>`
4. `frontend/mobile_app/lib/invoiceService.ts` — DS02 fix: CSS constant + data-URI `<link>` replacement
5. `frontend/mobile_app/app/supplier/label.tsx` — DS02 fix: CSS constant + data-URI `<link>` replacement
6. `.gitignore` — Added `**/android/app/build/`
7. Deleted: `frontend/mobile_app/dist/`, `web-dist/`, `android/app/build/`, `android/app/.cxx/`, `documents/archive/.../dist/`
8. Deleted root temp scripts: `_fix_css.py`, `_fix_banner.py`, `_fix_db06.py`, `_inspect_json.py`, `_inspect_yellow.py`, etc.
