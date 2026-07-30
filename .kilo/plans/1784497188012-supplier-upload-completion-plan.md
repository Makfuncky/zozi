# Supplier Product Upload — Completion Plan (remaining work)

## Status of the original plan (`1784497188012-supplier-upload-automation-plan.md`)

Phases 0–6 were **implemented**. Verified in code on 2026-07-20:

- **Backend** (`backend/routers/supplier.py`): `voice_extract` alias (@L695) + `nlp_extract` (@L683) both call `_extract_from_transcript` (@L595); variant keys normalized to lowercase. Live API confirmed: `POST /supplier/upload/voice-extract` returns lowercase `variants:{"color":[...],"size":[...]}` with token auth (401 without token = endpoint exists).
- **`variantEngine.ts`**: `buildVariantsJson` (@L205), `buildMultiAxisMatrix` (@L297), `mapVoiceResult` (@L350) present; combo matrix wired into `mapVoiceResult` (@L417).
- **`ProductUploadWizard.tsx`**: `handleVoiceData` (@L135), "Describe by Voice" button + `<VoiceProductInput onDataExtracted>` (@L287-290), generic `VariantMatrixInline` (@L528) with multi-axis combo render.
- **`page.tsx`**: page-level `handleVoiceData` + `voiceOpen` modal (@L187-212), header "Voice" button (@L245), "✨ Magic Photo Editing" label (@L268), "Done — Verify" → `store.setStep(5)` (@L270-272).
- **6 BG models**: wired (`bg_removal_service.VALID_STRATEGIES`), present in UI as Clean·br05 / Geometry·br06 / Production·br08 / Gaps·br11 / Marketing·br12 / Lite·br13.

## What is NOT yet done

1. **Playwright suite is not green.** `frontend/web_app/e2e/supplier-wizard-upload.spec.ts` has 11 tests. `loginSupplier` + `mockBackend` (fixed `/supplier\/products(?!\/add)/` regex) pass the gate. `uploadFirstImage` (L80-92) still hits *"Execution context was destroyed, most likely because of a navigation"* right after `setInputFiles` under `channel:"chrome"`. The same native-file-setter approach worked reliably in isolated Chromium. Servers are warm (FE :3000 → 200 on `/supplier/products/add`; BE :8000 → 401 on `voice-extract`).
2. **Doc is stale.** `documents/SUPPLIER_PRODUCT_UPLOAD.md` is still 523 lines of the OLD flow (sequential popups, dropped-field analysis). It must be rewritten to the new automation-first flow (≤150 lines).
3. **Debug scripts left in tree** (must be deleted before finishing): `frontend/web_app/debug_wizard.mjs`, `debug_plain.cjs`, `debug_plain.mjs`, plus `e2e/_dbg_*.cjs` and `test-results/` artifacts.

## Completion tasks (ordered)

### T1 — Stabilize `uploadFirstImage` and get the suite green
- In `uploadFirstImage` (spec L80-92): before the native-file-setter `page.evaluate`, await `await page.waitForLoadState("networkidle")` (or a short `page.waitForTimeout(300)`) so the execution context isn't destroyed by an in-flight navigation right after `setInputFiles`.
- Keep `setInputFiles` on `input[data-testid="wizard-upload-input"]`; keep the post-condition asserting the AI Analyze button appears.
- Run: `cd frontend/web_app; npx playwright test e2e/supplier-wizard-upload.spec.ts --retries=0` (use `--retries=0` while debugging; restore config default after).
- Fix any additional wiring failures surfaced during the run (the request's "fix-as-you-go" mandate). Common suspects: step-2 "Analyze Photo" button name regex, "Describe by Voice" button presence, multi-axis combo editor render for electronics `storage×ram`, success screen text ("Published Successfully!").

### T2 — Add two missing e2e assertions (per plan Phase 7.4 / 7.5)
- **Voice→wizard field fill**: drive the mock `/voice-extract` route (already in `mockBackend`) to return a realistic payload with lowercase `variants` (e.g. `{"product_name":"Voice Product","category":"Electronics","price":99,"variants":{"color":["Black"],"storage":["256GB"]}}`); after clicking "Describe by Voice" → "Done — Extract", assert wizard fields (name/category) auto-populate AND the variant matrix is seeded. (Headless has no `SpeechRecognition`, so exercise the Apply path via the mock, not real mic.)
- **Multi-axis combo**: pick an electronics category (`storage×ram`) in step-2 and assert the combo editor renders all combinations (≤30 cap).

### T3 — Rewrite `documents/SUPPLIER_PRODUCT_UPLOAD.md` (≤150 lines)
Replace the 523-line file with the automation-first doc:
- 3 intake paths: **Upload** (photo/video), **Voice** (Mic → NLP → auto-fill), **Magic Photo Editing** (canvas studio, 6 BG models → Done → Verify).
- Voice→field mapping table (transcript → name/desc/category/color/tags/price/variants), referencing `mapVoiceResult` + backend `_extract_from_transcript`.
- 6 BG models ↔ `br_05.py`…`br_13.py` ↔ `bg_removal_service.VALID_STRATEGIES`.
- Variant/spec config source: `zozi_variant_config.json` via `categoryVariantBridge` + `variantEngine` (`buildMultiAxisMatrix`, combo keys `"color:Red|size:M|storage:256GB"`).
- 5-step happy path: Upload → AI Analyze → Variants & Specs → Pricing → Review & Publish ("Thank you for using ZOZI").
- Note the known dropped conditional fields (Electronics/Clothing) as an out-of-scope follow-up, not a fix.

### T4 — Cleanup
- Delete `frontend/web_app/debug_wizard.mjs`, `debug_plain.cjs`, `debug_plain.mjs`.
- Delete `frontend/web_app/e2e/_dbg_*.cjs` and `frontend/web_app/test-results/**` (regenerate is fine; keep nothing committed).
- Do NOT delete `supplier-wizard-upload.spec.ts` or `debug-upload.spec.ts` (keep as the green suite).

## Affected files
- `frontend/web_app/e2e/supplier-wizard-upload.spec.ts` — stabilize `uploadFirstImage`; add voice-fill + multi-axis assertions.
- `documents/SUPPLIER_PRODUCT_UPLOAD.md` — rewrite to ≤150 lines (automation-first).
- Delete: `frontend/web_app/debug_wizard.mjs`, `debug_plain.cjs`, `debug_plain.mjs`, `e2e/_dbg_*.cjs`, `test-results/**`.

## Validation (definition of done)
- `npx playwright test e2e/supplier-wizard-upload.spec.ts` → all 11 (or ~13 after T2) pass with config defaults (`channel:"chrome"`, `workers:1`, `retries:1`).
- `documents/SUPPLIER_PRODUCT_UPLOAD.md` ≤150 lines, describes the 3 paths + 6 BG models + happy path.
- `git status` shows no `debug_*` / `_dbg_*` / `test-results/` untracked files.

## Out of scope
- Persisting dropped conditional fields (warranty, battery_capacity, voltage, fabric_type, etc.) into `Product.attributes` — document only.
- Whisper/Ollama availability on the runner — tests must tolerate heuristic fallback.
- Rebuilding bg-removal or `ai-analyze` (both verified working).
