# BG Removal & Product Detection Improvement Plan

## Context

The ZOZI supplier upload system has two critical pain points identified through testing and code review:

1. **BG Removal is slow and unreliable**: The `/supplier/upload/remove-background` endpoint takes >30s per image on CPU. The `PhotoEditModal.tsx` and `ProcessingModal.tsx` explicitly pass `timeoutMs: 300000` (5 min) to `apiFetch`, but the backend `rembg` CPU inference can exceed this for large images. The `api.ts` `AbortController` fires when the timeout expires, causing `signal is aborted without reason` errors. The backend uses `rembg` (CPU-based) with models like `isnet-general-use` and `birefnet-general`, which are slow and memory-intensive.

2. **Product detection is inaccurate**: The `analyze_product_image` function in `providers/ai/vision.py` uses filename-based keyword matching as the primary candidate, with CV color analysis as a secondary signal. Ollama vision (moondream) is gated behind `AI_USE_VISION` env flag (off by default on VPS). When vision is off, the fallback produces generic names like "Teal Brown Clothing" with wrong categories. The `upload_auto_05.py` test script relies on this same pipeline.

## System Architecture (Corrected)

### BG Removal Pipeline
- **Frontend**: `ProcessingModal.tsx` (primary, runs on image upload) → `api.ts` (fetch with `timeoutMs: 300000`) → backend `/supplier/upload/analyze-parallel`
- **Frontend**: `PhotoEditModal.tsx` (manual BG preset editing after upload) → `api.ts` → backend `/supplier/upload/remove-background`
- **Backend**: `reference_data/routers/suppliers/supplier.py` → `reference_data/services/ai/bg_removal_service.py` (shim re-export) → `providers/bg_remover.py` (real impl) → `rembg` library
- **Models available**: `isnet-general-use`, `birefnet-general`, `birefnet-general-lite`, `u2net`, `u2net_cloth_seg`, `briaai-rmbg-1.4`, `silueta`, `birefnet-massive`, `birefnet-hrsod`
- **Session cache**: LRU with max 2 models, heavy models disabled by default on low RAM
- **Resolution caps**: Heavy models capped at 768px, lite at 1024px, others at 2048px
- **Post-processing already integrated**: `GlobalBackgroundBleeder`, `FloatingArtifactRemover`, `BottomTextEraser` are already in `bg_remover.py` (lines 630, 679, 705) and in the `bg_removal_service.py` shim

### Product Detection Pipeline
- **Primary**: `analyze_product_image()` in `providers/ai/vision.py` — uses filename candidate + CV color analysis + optional Ollama vision (moondream) + phi3:mini text structuring
- **Endpoint**: `/supplier/upload/analyze-parallel` runs BG removal + AI analysis concurrently via `asyncio.gather`
- **Endpoint**: `/supplier/upload/ai-analyze` returns instant heuristic result (filename + CV), with background job for copy generation
- **Variant selection**: JSON-driven config (`zozi_variant_config.json`) with category→variant mapping via `variant_config_service.py`
- **AI_USE_VISION env flag**: OFF by default on VPS — this is the root cause of poor detection quality

## Issues Identified (Root Causes)

### BG Removal Issues
1. **Speed**: `rembg` CPU inference is slow (30s+ per image). The `isnet-general-use` model is the default but takes long. `birefnet-general-lite` is faster but still CPU-bound.
2. **Memory**: Heavy models (birefnet-massive, birefnet-hrsod) are disabled by default due to OOM on low-RAM VPS.
3. **Frontend timeout**: `api.ts` default timeout is 30s (`DEFAULT_API_TIMEOUT_MS`). The modal components override to 300s, but the `apiFetch` retry mechanism creates a new `AbortController` with the same timeout. If backend processing exceeds 300s, the request still fails.
4. **No model selection by image type**: The `auto` strategy in `bg_remover.py` uses a simple heuristic (edge density, texture, color variance) that may not pick the best model for product images specifically.
5. **Fake progress bars**: `ProcessingModal.tsx` progress bars jump from 40%→90%→100% without actual progress tracking.

### Product Detection Issues
1. **AI_USE_VISION is off by default**: The `vision.py` provider gates Ollama vision behind `AI_USE_VISION` env flag, which defaults to off for VPS safety. This means the system relies on filename keywords + CV color analysis instead of actual image understanding.
2. **Generic fallback names**: When vision is off and filename provides no clues, `_build_fallback_name()` generates generic names like "Teal Brown Clothing" instead of actual product names.
3. **Filename keyword matching**: `_candidate_from_filename()` uses keyword matching which is unreliable for arbitrary product images (e.g., "IMG_1234" → no useful candidate).
4. **No image-content-based detection**: The detection doesn't analyze the actual image content when vision is disabled — it only uses color histograms and edge density from CV.
5. **Variant axes mismatch**: The `_refine_variant_suggestions()` function caps and filters variants, but the filtering logic may strip relevant axes for certain product types.

## Plan

### Phase 1: BG Removal Speed (Backend)

**Goal**: Reduce BG removal latency from >30s to <10s per image.

1. **Switch primary model to `birefnet-general-lite`** — it's 213MB vs 900MB for full BiRefNet, significantly faster on CPU, and already available in the provider. Update the `auto` strategy in `bg_remover.py` to prefer lite for product images.
2. **Add model warm-up on server startup** — load `birefnet-general-lite` and `u2net` into the session cache at startup so they're ready for the first request.
3. **Implement resolution-adaptive processing** — downscale images >1024px before BG removal, upscale result back. This is the single biggest speed improvement for large images.
4. **Add per-model latency tracking** — log inference time per model per image size; use this data to auto-select the fastest model for a given image size range.

### Phase 2: BG Removal Reliability

**Goal**: Eliminate timeout failures and make BG removal robust for all image sizes.

1. **Increase `DEFAULT_API_TIMEOUT_MS` in `api.ts` from 30000 to 300000** (or make it configurable per endpoint) — the current 30s default is too low for BG removal calls even though the modal components override it.
2. **Add a dedicated `/supplier/upload/remove-background` timeout header** — the backend can check the requested timeout and adjust processing strategy (e.g., use faster model for large images when timeout is tight).
3. **Fix `ProcessingModal.tsx` progress bars** — replace fake progress (40%→90%→100%) with actual progress tracking based on backend processing stages (model loading, inference, post-processing).
4. **Add retry with different preset on failure** — if `general` preset fails, automatically retry with `auto` or a lighter preset.

### Phase 3: Product Detection Accuracy

**Goal**: Improve product name, category, and variant detection accuracy by enabling vision and improving CV analysis.

1. **Enable `AI_USE_VISION` by default** — set `AI_USE_VISION=true` in the environment configuration so Ollama vision (moondream) is used for product detection. This is the single biggest improvement for detection quality.
2. **Improve `_candidate_from_filename()`** — add more product-type keywords and handle camera-generated filenames (IMG_, DSC_, etc.) by falling back to CV analysis instead of returning an empty candidate.
3. **Improve `_build_fallback_name()`** — use CV-derived product type hints (edge density → product vs. background ratio, color distribution → material type) to generate more specific fallback names instead of generic "Teal Brown Clothing".
4. **Add CV-based product type classification** — use the existing `_analyze_photo_cv()` output (edge density, texture, color variance) to classify product type before falling back to filename keywords. This provides a better initial candidate when the filename is unhelpful.
5. **Improve variant axis selection** — cross-check detected variants against the product category's allowed axes from the `variant-axes` endpoint; filter out axes that don't apply to the detected product type (e.g., don't suggest "size" for electronics).

### Phase 4: Frontend Integration

**Goal**: Make the frontend handle BG removal and detection results gracefully.

1. **Add BG removal progress tracking** — replace fake progress bars in `ProcessingModal.tsx` with real progress based on backend processing stages.
2. **Add preset selection UI** — `PhotoEditModal.tsx` already has BG presets (br05 Clean, br06 Geo, br08 Prod, br11 Gap) but doesn't show which preset is active or allow switching after initial processing. Add preset switching with a loading state.
3. **Add detection confidence indicator** — show the AI confidence level for product detection in `AIResultsModal.tsx` and allow manual override of category and variants.
4. **Add "Edit Image" button** in `AIResultsModal.tsx` — already exists (the Magic Edit Image button), but it should preserve the AI-detected values when returning to the photo edit phase.
5. **Fix test script bugs** — in `test_complete_upload.js`: fix `modelBtn.first.click` → `modelBtn.first().click` (same `.first` vs `.first()` bug that was fixed in the main test), and fix the ADD PRODUCT button retry logic for images 4+.

### Phase 5: Testing & Validation

1. **BG removal benchmark**: Run `test_bg_timing.js` on all 30 images with `birefnet-general-lite` as primary model; measure latency (target: <10s per image).
2. **Detection accuracy benchmark**: Run `upload_auto_05.py` on all 30 images with `AI_USE_VISION=true`; manually verify category + name accuracy for each (target: >85%).
3. **End-to-end test**: Run `test_complete_upload.js` for all 30 images and verify 100% success rate.
4. **Validate `upload_test_report.json`** — confirm all images processed successfully with correct BG removal and AI detection.
5. **Regression test**: Ensure existing functionality (login, product listing, variant axes, publish flow) is not broken.

## Key Files to Modify

| File | Change |
|------|--------|
| `backend/providers/bg_remover.py` | Switch auto strategy to prefer `birefnet-general-lite` for product images; add resolution-adaptive processing; add per-model latency tracking |
| `backend/providers/ai/vision.py` | Enable `AI_USE_VISION` by default; improve `_candidate_from_filename()` for camera filenames; improve `_build_fallback_name()` with CV hints |
| `frontend/web_app/src/lib/api.ts` | Increase `DEFAULT_API_TIMEOUT_MS` from 30000 to 300000 |
| `frontend/web_app/src/components/supplier/upload/ProcessingModal.tsx` | Replace fake progress bars with real stage-based progress |
| `frontend/web_app/src/components/supplier/upload/PhotoEditModal.tsx` | Add preset switching UI with loading state |
| `frontend/web_app/src/components/supplier/upload/AIResultsModal.tsx` | Add detection confidence indicator and manual override |
| `backend/tests/playwright/test_complete_upload.js` | Fix `modelBtn.first.click` → `modelBtn.first().click`; fix ADD PRODUCT button retry for images 4+ |

## Open Questions

1. Is GPU available on the server for faster rembg inference? (If yes, Phase 1 item 1 changes to GPU-accelerated rembg instead of model switch)
2. What is the acceptable latency SLA for BG removal? (Current: >30s, Target: <10s)
3. Should `AI_USE_VISION` be enabled by default given the CPU cost? (It adds ~60-90s per image for copy generation, but the `analyze-parallel` endpoint runs it in background)
4. Should the async BG removal approach use WebSockets or HTTP polling? (Current plan keeps synchronous endpoints; async is out of scope for this phase)
5. Should we invest in fine-tuning a custom BG removal model for product images? (Out of scope for this phase)

## Validation Steps

1. Run BG removal on all 30 test images with `birefnet-general-lite` and measure latency (target: <10s per image)
2. Verify no AbortController timeout errors in browser console during BG removal
3. Enable `AI_USE_VISION` and verify product detection accuracy on all 30 images (target: >85% correct category + name)
4. Run the full browser upload test (`test_complete_upload.js`) and verify 100% success rate
5. Validate `upload_test_report.json` shows all images processed successfully