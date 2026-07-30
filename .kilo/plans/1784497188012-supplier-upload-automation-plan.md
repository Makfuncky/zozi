# Supplier Product Upload — Automation & Voice Flow Plan

## Context

The supplier upload page (`/supplier/products/add`) already has a near-complete implementation:
a canvas studio (left) + a 5-step `ProductUploadWizard` (right). The 6 background-removal
models (br_05–br_13) are **correctly wired** (frontend `BG_MODELS` keys =
`clean_commercial|precision_geometry|birefnet_production|ultimate_gaps|marketing_variants|
lite_variants` exactly match `VALID_STRATEGIES` in `backend/services/bg_removal_service.py`).
Config-driven variant logic exists in `variantEngine.ts` / `categoryVariantBridge.ts` (sourced from
`zozi_variant_config.json`).

The remaining gaps are about **voice → auto-fill** and **multi-axis variants**, gathered by reading
the actual code (not assumptions):

### Verified bugs / gaps
1. **Voice 404 (real).** `frontend/.../VoiceProductInput.tsx:121` POSTs to
   `/supplier/upload/voice-extract`, which **does not exist** in `backend/routers/supplier.py`.
   The backend exposes `/upload/voice-transcribe` (audio→text) and `/upload/nlp-extract`
   (text→structured). `VoiceProductInput` survives via its `localParse` fallback, but AI
   extraction never runs.
2. **Voice data never reaches the wizard (real, bigger than #1).** The page's top-right
   **"Voice"** button (`page.tsx:184 startVoiceCommand`) only runs *keyword dictation*
   (bg/white/transparent/zoom/rotate/grid). `<VoiceProductInput>`'s `onDataExtracted`
   callback is **never consumed** by the page or the wizard. So today there is **no path**
   from a spoken description to the form fields — the request's "press Mic → system fills
   name/color/fabric/tags/price/variants" is not implemented.
3. **`nlp-extract` variant-key casing inconsistency.** Ollama path returns
   `variants: {"color":[...], "size":[...]}` (lowercase, `supplier.py:622`) but the heuristic
   fallback returns `{"Color":[...], "Size":[...]}` (caps, `supplier.py:657`). Downstream
   consumers must not depend on casing.
4. **Multi-axis matrix gap (real).** `ProductUploadWizard.tsx:VariantMatrixInline` (line 491)
   only handles two shapes: `color×size` grid, OR a **single** non-color/size axis (flat list).
   Categories with **2+ non-color/size axes** (e.g. electronics `storage×ram`, or
   `material×color×size`) fall through: `singleAxisKey = types[0]` drops every other axis.
   The Python reference `upload_auto_05.py` generates the full cartesian product.
5. **(Not a bug) AI Analyze variant fill works.** `ai_analyze` returns `suggested_variants`
   as a **string[] of axis keys** (`ai_variant_config.py:1231`), which `mapAIResultToFormState`
   (`variantEngine.ts:285`) correctly consumes. Photo→variant auto-fill is fine; leave it.

### What is already correct (do NOT rebuild)
- BG removal: 6 models ↔ br_05..br_13 via `bg_removal_service.VALID_STRATEGIES`. ✅
- `ai-analyze` → `mapAIResultToFormState` → wizard store (name/desc/category/color/tags/
  variants/matrix/price). ✅
- `categoryVariantBridge.getSpecGroupsForCategory` builds tick-box specs from config for every
  picker category (with `other` fallback). ✅
- Success screen ("Thank you for using ZOZI" + Product ID + score) exists. ✅
- Canvas studio with zoom/rotate/grid/12 image tools + angle generator exists. ✅

## Plan

### Phase 0 — Backend: fix voice endpoint + normalize casing
- `backend/routers/supplier.py`:
  - Add alias `@router.post("/upload/voice-extract")` that forwards `transcript` (and optional
    `audio`) to the **same** `_ollama_chat` + heuristic logic as `nlp_extract`. Keep `nlp-extract`.
  - In `nlp_extract`, **normalize variant keys to lowercase** before returning (map `Color→color`,
    `Size→size`, `Material→material`, `Print→print`, etc.). This removes the Ollama-vs-heuristic
    casing mismatch (#3).
- No change to `voice-transcribe` (used only if we later pipe audio→text→extract).

### Phase 1 — Frontend: one voice→store adapter
- `frontend/web_app/src/lib/variantEngine.ts`: add `mapVoiceResult(voice: ExtractedData)` that
  converts the **voice shape** (`product_name, category, colors[], fabric, print_text, description,
  suggested_tags[], variants{color:[],size:[],...}, stock_hints, quantity, price`) into the **same
  `mapped` shape** `mapAIResultToFormState` returns (`name, description, category, brand, price,
  tags, variantsType[], variantsOptions{}, variantsLabels{}, matrix, priceRange`). Reuse
  `buildMatrixFromVariants` for the matrix. Lower-case axis keys defensively.

### Phase 2 — Wire voice into the wizard (fixes #2)
- `ProductUploadWizard.tsx`:
  - Add a **"Describe by Voice"** button in `AiAnalyzeStep` that opens `<VoiceProductInput
    onDataExtracted={handleVoiceData} />`. `handleVoiceData` runs `mapVoiceResult(voice)`, then
    applies the same `store.setFormData / updateVariantTypes / updateVariantOptions /
    updateVariantMatrix` sequence already used at lines 145-167 for `ai-analyze`. If
    `voice.category` is set, resolve it to a `CATEGORIES` value (mirror lines 151-156).
  - After applying, `store.setAiFilled(true)` and advance to step 3 (Variants) so the matrix is
    pre-seeded — this satisfies the request's "Mic → everything handled, jump to verification".
- `page.tsx`:
  - Repurpose the top-right **"Voice"** button: when an image is selected it should open the
    same `<VoiceProductInput>` (or trigger wizard voice). Keep the keyword dictation as a secondary
    "Canvas voice shortcuts" toggle if desired, but the primary action must be data extraction.
  - Pass `onDataExtracted` from the page to the wizard (or lift `VoiceProductInput` into the
    wizard as above and call it from the page too via a shared store flag).

### Phase 3 — Multi-axis variant matrix (fixes #4)
- `ProductUploadWizard.tsx:VariantMatrixInline`: replace the 2-case logic with a **generic**
  renderer driven by `buildMultiAxisMatrix` (Phase 4):
  - `color×size` → keep the existing 2-D grid (most common, best UX).
  - 1 axis → flat list (existing).
  - **≥2 non-color/size axes** → render an **interactive combo editor**: checkboxes to pick
    which axis combinations to include (cap at 30 cells, show "showing first 30 of N"), each row
    with stock/price/SKU inputs. This reproduces `upload_auto_05.py` cartesian behaviour.
- Keep `store.updateVariantMatrix` as the single sink.

### Phase 4 — `variantEngine.ts` helper
- Add `buildMultiAxisMatrix(axes: {key:string; values:string[]}[], defaults)` →
  `Record<string, Record<string,{stock;price;sku}>>` keyed by a stable combo key
  (`"color:Red|size:M|storage:256GB"`), capped at 30 entries. `VariantMatrixInline` uses this for
  the combo editor (Phase 3). Reuse for `buildMatrixFromVariants` consolidation if practical.

### Phase 5 — Magic Photo Editing entry (already built, just surface)
- `page.tsx` canvas studio IS the Magic Photo Editing surface. Ensure:
  - After an image is chosen, the canvas is the default left pane (already true).
  - Add an explicit **"✨ Magic Photo Editing"** label/section header so it reads as a named entry.
  - Add a **"Done"** button on the canvas that jumps the wizard to **Publish** (verification)
    step — matches the request's "when satisfied press Done → verification".

### Phase 6 — Documentation
- Write `documents/SUPPLIER_PRODUCT_UPLOAD.md` (≤150 lines): 3 intake paths (Upload / Voice /
  Magic Photo Editing), how voice maps to fields, the 6 BG models ↔ br scripts, variant/spec
  config source (`zozi_variant_config.json`), and the happy path.

### Phase 7 — Playwright validation (explicitly fix-as-you-go)
Browser test (`frontend/web_app/__tests__` or `browser-tests/`):
1. Login as supplier → `/supplier/products/add`.
2. Upload `Working_API/zozi_ai_image_service/image/image_01.webp`.
3. Assert all 6 BG model buttons exist; click one → PNG blob returned (mock/real
   `/upload/remove-background`).
4. Click **"Describe by Voice"**; POST a transcript to `/upload/voice-extract` (or drive the
   component) asserting `variants` keys are lowercase and the wizard fields (name, color, tags)
   auto-populate + matrix seeded.
5. Verify multi-axis: pick a category with `storage×ram` (electronics) and assert the combo
   editor shows all combinations (≤30).
6. Walk Upload→AI→Variants→Pricing→Publish; assert success screen "Thank you for using ZOZI".
7. Fix any wiring found during the run (requested: "while test make changes also if anything not
   working").

## Affected files
- `backend/routers/supplier.py` — alias `/upload/voice-extract`; lowercase variant keys in `nlp-extract`.
- `frontend/web_app/src/lib/variantEngine.ts` — `mapVoiceResult`, `buildMultiAxisMatrix`.
- `frontend/web_app/src/components/supplier/ProductUploadWizard.tsx` — voice button + `handleVoiceData`; generic `VariantMatrixInline`.
- `frontend/web_app/src/components/supplier/VoiceProductInput.tsx` — already calls `voice-extract`; no change needed once backend alias exists (keep `localParse` fallback).
- `frontend/web_app/src/app/supplier/products/add/page.tsx` — repurpose "Voice" button; Magic Photo Editing label + Done→Publish.
- `documents/SUPPLIER_PRODUCT_UPLOAD.md` — new doc.

## Out of scope
- Rebuilding bg-removal (works). Reworking `ai-analyze` (works).
- Whisper/Ollama availability on the runner — tests must tolerate heuristic fallback output.

## Validation (definition of done)
- `frontend/web_app` typecheck/build passes.
- Backend boots; `curl -F 'transcript=red cotton tshirt 4 colors' /supplier/upload/voice-extract`
  returns JSON with **lowercase** variant keys (not 404).
- Playwright flow passes: 6 BG buttons reachable; voice auto-fills wizard + seeds matrix; multi-axis
  combos render; publish success shows "Thank you for using ZOZI".
