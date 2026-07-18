# Supplier Product Upload — Complete Reference

> Source of truth reverse-engineered from the codebase (the page `supplier/products/add`
> and the backend `/supplier/products` + `/supplier/upload*` endpoints).
> Last reviewed against `frontend/.../supplier/products/add/page.tsx`,
> `backend/routers/supplier.py`, `backend/controllers/supplier_controller.py`,
> `backend/models/products.py`.

---

## 1. Overview / User Flow

1. Supplier opens **`/supplier/products/add`** → the Add Product form.
2. Fills Basic Info, Category, conditional spec fields, Pricing/Inventory, Variants,
   Image Tools, uploads an image (drag-drop / camera / file), optionally runs
   **AI Auto-Fill**, **Background Removal**, **AI angle generation**.
3. Selects **target countries** (multi-country publishing) and fills **logistics** data.
4. On submit, the page `POST`s a `multipart/form-data` body to **`/supplier/products`**.
5. Backend `create_supplier_product` validates, processes the image through the
   enabled free-image tools, resolves shipping tier + content moderation, persists the
   `Product` (+ variants), and returns the product payload.
6. On success the page clears the local draft and redirects to `/supplier/products`.

> Note: the page calls **`POST /supplier/products`** (the "products" route), NOT
> `POST /supplier/upload`. The `/supplier/upload` route is the alternative
> single-shot uploader (used by `supplier/upload/page.tsx`), with a slightly different
> field set. The image-processing helpers (`remove-background`, `ai-analyze`,
> `generate-angles`) are separate `POST /supplier/upload/*` calls made interactively
> before submit.

---

## 2. File Inventory

### Frontend

| File | Role |
|------|------|
| `frontend/web_app/src/app/supplier/products/add/page.tsx` | **The Add Product page.** Entire form, state, image/AI handling, variants, submit. ~2000+ lines. |
| `frontend/web_app/src/components/SupplierLayout.tsx` | Page shell / nav wrapper. |
| `frontend/web_app/src/lib/api.ts` | `apiFetch` — used for every `/supplier/*` call. |
| `frontend/web_app/src/lib/currencyStore.ts` | `useCurrencyStore().format` — price preview formatting. |
| `frontend/web_app/src/lib/icons.ts` | Icon imports used by the page. |
| `frontend/web_app/src/app/supplier/products/page.tsx` | Product list — redirect target after create. |
| `frontend/web_app/src/app/supplier/products/[id]/page.tsx` | Product detail/edit — shares the same payload shape. |
| `frontend/web_app/src/app/supplier/upload/page.tsx` | Separate single-shot uploader (uses `POST /supplier/upload`). |

### Backend — endpoints called by the Add page

| File | Endpoint | Handler (controller fn) |
|------|----------|-------------------------|
| `backend/routers/supplier.py` | `POST /supplier/products` (L336) | `create_supplier_product` → `ctrl.create_supplier_product` |
| `backend/routers/supplier.py` | `POST /supplier/upload` (L243) | `upload_product` → `ctrl.create_supplier_product_upload` |
| `backend/routers/supplier.py` | `POST /supplier/upload/remove-background` (L470) | returns processed PNG bytes (preset: general/handheld/wood/texture_gap/marketing/cloth_lite/auto) |
| `backend/routers/supplier.py` | `POST /supplier/upload/ai-analyze` (L494) | `analyze_product_image` (heuristic + optional Ollama vision) |
| `backend/routers/supplier.py` | `POST /supplier/upload/generate-angles` (L537) | `process_product_image(generate_angles=True)` |
| `backend/routers/supplier.py` | `POST /supplier/upload/translate` (L514) | EN→AR text translation |
| `backend/routers/supplier.py` | `POST /supplier/upload/moderate` (L526) | GCC content moderation |
| `backend/controllers/supplier_controller.py` | — | `create_supplier_product` (L1704), `create_supplier_product_upload` (L1570), `_persist_supplier_product` (L155), `_parse_product_variants_payload` (L597), `_replace_product_variants` (L682), `_build_supplier_product_payload` (L774), `_save_upload` (L1467), `_process_image_with_tools` |
| `backend/controllers/products_controller.py` | — | variant serialization / product-code generation helpers |
| `backend/services/free_image_tools.py` | — | the 12-tool image pipeline (denoise → … → webp_convert) |
| `backend/services/bg_removal_presets.py` | — | `remove_background_preset`, `VALID_PRESETS` |
| `backend/services/ai_variant_config.py` | — | `analyze_product_image` (AI auto-fill) |
| `backend/services/shipping_tier.py` | — | `resolve_shipping_tier` |
| `backend/services/content_service.py` | — | `moderate_content`, `translate_en_to_ar` |
| `backend/models/products.py` | — | `Product` (L32), `ProductVariant` (L140), `ProductVideo` (L165) ORM models |
| `backend/models/suppliers.py` | — | supplier lookup for `current_user` |

### Tests / verification scripts (affected by amendments)

- `backend/tests/test_supplier.py`
- `backend/scripts/audit_supplier_products.py` (exercises `POST /supplier/products` with variants + axes + bg_preset)
- `backend/scripts/test_photo_processing.py`, `test_api_image_tools.py`, `test_image_tools.py`, `test_new_tools.py`

---

## 3. Submit Payload — Field Reference (`POST /supplier/products`)

### Fields the page sends (from `page.tsx` `handleSubmit`)

| Form field | Source (page state) | Accepted by `/products` route? | Persisted to |
|-----------|---------------------|-------------------------------|--------------|
| `name` | `formData.name` | ✅ required | `Product.name` |
| `description` | `formData.description` | ✅ required | `Product.description` |
| `price` | `formData.price` | ✅ required | `Product.price` |
| `category` | `formData.category` | ✅ required | `Product.category`, `category_id` |
| `stock_quantity` | variant total or `formData.stock_quantity` | ✅ required | `Product.stock` |
| `is_active` | `formData.is_active` | ✅ | `Product.is_active` |
| `subcategory` | `formData.subcategory` | ✅ | `Product.subcategory` |
| `brand` | `formData.brand` | ✅ | `Product.brand` |
| `color` | `formData.color` | ✅ | `Product.color` |
| `tags` | `formData.tags` | ✅ | `Product.tags` |
| `compare_price` | `formData.comparePrice` | ✅ | `Product.compare_price` |
| `variants_json` | `buildVariantsJson()` | ✅ | `ProductVariant` rows |
| `variant_axes_json` | axes array | ✅ | `Product.variant_axes` |
| `countries` | `selectedCountries.join(',')` | ✅ → `visibility_regions` | `Product.visibility_regions` |
| `weight_kg` | `conditionalFields.weight_kg` | ✅ → `weight` | `Product.weight` (+ shipping tier) |
| `weight` | `conditionalFields.weight` (Home/Garden) | ✅ | `Product.weight` |
| `dimensions` | `conditionalFields.dimensions` | ✅ | `Product.dimensions` |
| `saso_cert` | `conditionalFields.saso_cert` | ✅ | `Product.attributes` JSON |
| `halal_compliance` | `conditionalFields.halal_compliance` | ✅ | `Product.attributes` JSON |
| `bg_preset` | `activeBgPreset` | ✅ | `Product.bg_preset` |
| **`warranty`** | `conditionalFields.warranty` (Electronics) | ❌ **NOT accepted** | **dropped** |
| **`battery_capacity`** | `conditionalFields.battery_capacity` | ❌ **NOT accepted** | **dropped** |
| **`voltage`** | `conditionalFields.voltage` | ❌ **NOT accepted** | **dropped** |
| **`fabric_type`** | `conditionalFields.fabric_type` (Clothing) | ❌ **NOT accepted** | **dropped** |
| **`care_instructions`** | `conditionalFields.care_instructions` | ❌ **NOT accepted** | **dropped** |
| **`size_chart`** | `conditionalFields.size_chart` | ❌ **NOT accepted** | **dropped** |
| `image` | processed/selected `File` | ✅ | `Product.image_url` (via `_save_upload`) |
| `process_*` (12 flags) | `formData.process_*` | ✅ | applied to image before save |

> Also note: `conditionalFields` declares `expiry_date` and `ingredients` but the page
> never renders or sends them.

### ⚠️ Key gap (amendment candidate)

The **Electronics** (warranty, battery_capacity, voltage) and **Clothing**
(fabric_type, care_instructions, size_chart) conditional fields are collected in the UI
but the `POST /supplier/products` route does **not** read them, and
`_persist_supplier_product` does **not** write them into `Product.attributes`. They are
silently lost on submit. To persist them, see §6.

---

## 4. The 12 Free Image Tools

Toggled on the **"Free Image Tools"** card. Sent as `process_<tool>=true` flags.
Mapped in the router to a `image_tools` dict and applied by
`_process_image_with_tools` → `services/free_image_tools.py` (order:
denoise → white_balance → color_enhance → auto_levels → magic_erase → smart_crop →
rotate → auto_light → sharpen → upscale → compress → webp_convert).

| Page toggle key | Router arg | Service function |
|-----------------|-----------|------------------|
| `process_magic_erase` | `magic_erase` | `magic_erase()` (rembg + CleanEdgeRefiner) |
| `process_smart_crop` | `smart_crop` | `smart_crop()` |
| `process_rotate` | `rotate` | `auto_rotate()` |
| `process_auto_light` | `auto_light` | `auto_lighting()` |
| `process_white_balance` | `white_balance` | `auto_white_balance()` |
| `process_denoise` | `denoise` | `denoise()` |
| `process_sharpen` | `sharpen` | `sharpen()` |
| `process_color_enhance` | `color_enhance` | `color_enhance()` |
| `process_auto_levels` | `auto_levels` | `auto_levels()` |
| `process_upscale` | `upscale` | `upscale()` |
| `process_compress` | `compress` | `compress()` |
| `process_webp_convert` | `webp_convert` | `webp_convert()` |

`bg_preset` (general/handheld/wood/texture_gap/marketing/cloth_lite/auto) is applied via
`services/bg_removal_presets.py` and stored on `Product.bg_preset`.

---

## 5. Variants structure

Built by `buildVariantsJson()` and sent as `variants_json` (array) + `variant_axes_json`
(array of `{key,label,options}`).

```jsonc
// variants_json
[
  {
    "is_active": true,
    "size": "M",            // standard axis → top-level column
    "color": "Red",         // standard axis → top-level column
    "attributes": { "size": "M", "color": "Red" }, // all axes
    "title": "M / Red",
    "stock": 10,
    "price": 50.0           // optional
  }
]

// variant_axes_json
[ { "key": "size", "label": "Size", "options": ["S","M","L"] },
  { "key": "color", "label": "Color", "options": ["Red","Blue"] } ]
```

Standard axes written to top-level variant columns: `size, color, material, pattern, gender`.
All axes are also stored in `ProductVariant.attributes_json`. Parsed by
`_parse_product_variants_payload` and persisted by `_replace_product_variants`.

---

## 6. How to Amend

### A. Add a brand-new form field (simple → no DB column)

1. **Frontend state**: add the key to `formData` (or `conditionalFields`) in
   `page.tsx` and a controlled `<input>` in the relevant `<Section>`.
2. **Submit**: append `formDataToSend.append('my_field', value)` in `handleSubmit`
   (around L1055).
3. **Backend route**: add `my_field: Optional[str] = Form(None)` to
   `create_product` in `backend/routers/supplier.py` (L336).
4. **Controller**: pass `my_field=my_field` into `ctrl.create_supplier_product(...)`
   and add it as a param on `create_supplier_product` (L1704) and
   `_persist_supplier_product` (L155).
5. **Persist**: if no dedicated column, merge into `extra_attributes` so it lands in
   `Product.attributes` JSON (see `saso_cert`/`halal_compliance` handling L432-435 +
   L245).

### B. Fix the dropped Electronics/Clothing conditional fields (recommended)

Currently `warranty`, `battery_capacity`, `voltage`, `fabric_type`,
`care_instructions`, `size_chart` are sent but ignored.

1. In `backend/routers/supplier.py` `create_product`, read each field:
   `warranty: Optional[str] = Form(None)`, etc. (mirror `saso_cert`/`halal_compliance`).
2. In the route, add each to `extra_attributes`, e.g.
   `if warranty: extra_attributes["warranty"] = warranty`.
3. `create_supplier_product` already stores `extra_attributes` into `Product.attributes`
   (L245) — no model/migration change needed (it's a JSON column).
4. (Optional) surface these in `_build_supplier_product_payload` /
   `supplier/products/[id]` so they're visible after save.

### C. Add a dedicated DB column (persistent, queryable)

1. Add `Column(...)` to `Product` in `backend/models/products.py`.
2. Add an Alembic migration (note: Alembic is currently broken — use direct `ALTER TABLE`
   SQL / `scripts/` as the rest of the repo does, or `backend/data/pg_*` scripts for Postgres).
3. Set it in `_persist_supplier_product` `Product(...)` constructor (L216).
4. Return it from `_build_supplier_product_payload` (L774).

### D. Add a new image tool

1. Add the toggle in `IMAGE_TOOLS` (page.tsx L122) + `formData` key (L170).
2. Add `process_new_tool: bool = Form(False)` to both `/products` (L370) and `/upload`
   (L280) routes, and add it to the `image_tools={...}` dict in both.
3. Implement the function in `backend/services/free_image_tools.py` and wire it into the
   pipeline order constant + `_process_image_with_tools`.

### E. Add a new target country

Edit `AVAILABLE_COUNTRIES` in `page.tsx` (L229) with `{code,name,currency,flag,rate,tax}`.
Backend stores the selection as a comma-joined `countries` string → `visibility_regions`.

---

## 7. Validation rules (current)

- Required: `name`, `description`, `category`; if variants disabled → `price` (positive)
  and `stock_quantity` (≥0).
- Variants enabled → at least one option value (`variantCombos.length > 0`).
- Image: JPG/PNG/WebP/GIF, max 5 MB (`MAX_IMAGE_SIZE`, `ALLOWED_TYPES` in page.tsx).
- Backend rejects if `name/price/stock_quantity/category` missing → 422.
- Country restriction check: `_persist_supplier_product` blocks restricted categories per
  supplier country (422).
- Variant combos capped at `MAX_VARIANT_COMBOS = 100` in the UI.
