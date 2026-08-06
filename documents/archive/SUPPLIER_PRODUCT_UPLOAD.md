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



# __________________________________________________________________________________________
# __________________________________________________________________________________________


There is just 5 steps actually. 
Process 1:
1. upload or capture image.
2. image process by bg removal.
3. image detection and filling details and variant selection and popup generation
4. variant wise quantity filling.
5. User will complete the popups of variant and finish everything and publish the product.

---
Process 2:
1. upload or capture image.
2. image process by bg removal.
3. voice note and voice recognition. 🎤 Voice Note: Record a natural sentence (e.g., "A cotton T-shirt, 4 colors: blue, yellow, black, white, with 'I love Oman' print, price 5 Rials").
4. filling all details and popup of variant wise for quantity filling.
5. User will complete the popups of variant and finish everything and publish the product.



Make a better Automation step wise plan which will successfully complete all the variant and category of product upload but make it faster to execute and max complete upload system must be complete in 30 sec.

---

```

## Supplier/ upload product 
	```
		1. Add Product by Upload, Take Photo.
		2. Process of cleaning photo 	
			"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_05.py"
			"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_06.py"
			"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_08.py"
			"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_11.py"
			"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_12.py"
			"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_13.py"
		3. Category + Sub-Category + Variant Check 	
			"zozi\Working_API\zozi_ai_upload_session\upload_auto_05.py"
			"zozi\Working_API\zozi_ai_upload_session\zozi_variant_config.json"
	```

	http://localhost:3000/supplier/products/add
	Supplier-Panel/ Upload Product Page:

	Automation should take place more rather then typing.

	Supplier/ click button `ADD PRODUCT`
		1. Popup of image file upload or capture, [ Once Supplier will upload the image one by one and video or capture ] then
		2. Popup will have icon of [ Mic ~ for voice Detail, 
	    							Magic Photo Editing Icon ~ for Photo Editing ]
			2a. if Supplier will press on `Mic` then 
				Voice recognition and distribution of data according to the voice note will be handle. 
				Suppose, Supplier said : "A T-shirt - 4 color = blue, yellow, black, white, having print [I love Oman] "
					Then system will handle everything from here by automation 
						Description: automatic detected
						Tag: automatic detected
						Name of product: automatic
						Cloth Fabric : ask by supplier by popup - [giving all kind of cloths which can be able for ticking anyone]
						Quantity: ask by supplier by popup 
							1st popup : 
											Blue S = [ ? ], 
											Blue M = [ ? ],
											Blue L = [ ? ],
											Blue XL = [ ? ],
							2nd popup : 
											Yellow S = [ ? ], 
											Yellow M = [ ? ],
											Yellow L = [ ? ],
											Yellow XL = [ ? ],
							
						Total Quantity: System will detect by itself
						Price: Popup will come and Supplier will enter.	
			
					Popup: for verification of all details then at bottom there is 3 button [ Edit Details, Upload, Edit Images]
						if Supplier selects `Edit Detail` 
							then he can edit by himself
						if Supplier selects `Upload` 
							then upload product and give finish message `Thank You to using ZOZI`
						if Supplier selects `Edit Images` then Popup appear of canvas of Image Editing.
							all the option will be appear on it of the Canvas 
								When the supplier will satisfy then he will press 'Done' button
									Popup: for verification of all details then at bottom there is 3 button [ Edit Details, Upload, Edit Images]
										Supplier will press `Upload` and Finish everything and upload will process.

			2b. if Supplier will press on `Magic Photo Editing` then 
				all the option will be appear on it of the Canvas 
					when supplier will done `Edit Photo` then 
						automatically detected and there is also option of voice details.
							Description: 	automatic detected
							Tag: 		automatic detected
							Name of product: automatic detected
							Color: 		automatic-detected 
								Popup appeared for more color to select, and type also

							Cloth Fabric : ask by supplier by popup - [giving all kind of cloths which can be able for ticking anyone]
							Quantity: ask by supplier by popup 
							1st popup : 
											Blue S = [ ? ], 
											Blue M = [ ? ],
											Blue L = [ ? ],
											Blue XL = [ ? ],
							2nd popup : 
											Yellow S = [ ? ], 
											Yellow M = [ ? ],
											Yellow L = [ ? ],
											Yellow XL = [ ? ],
							
						Total Quantity: System will detect by itself
						Price: Popup will come and Supplier will enter.	
			
					Popup: for verification of all details then at bottom there is 3 button [ Edit Details, Upload, Edit Images]
						if Supplier selects `Edit Detail` 
							then he can edit by himself
						if Supplier selects `Upload` 
							then upload product and give finish message `Thank You to using ZOZI`
						if Supplier selects `Edit Images` then Popup appear of canvas of Image Editing.
							all the option will be appear on it of the Canvas 
								When the supplier will satisfy then he will press 'Done' button
									Popup: for verification of all details then at bottom there is 3 button [ Edit Details, Upload, Edit Images]
										Supplier will press `Upload` and Finish everything and upload will process.
				

it should to handle all the variant of all category. we will have bueaty product, cosmetic, electronic items, laptop, phones, cloths, shoes, bages, household and everything. you need to make a diversify plan which can handle all kind of product with all variants, category, sub-category.

	read in detail more and make the process more faster to complete for uploading the product. 
	and check all the automation.

	- for category and variant management you can check the file `D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_upload_session\zozi_variant_config.json` to add into the system for faster adding the product.
	- you can take reference of flow of work also from "zozi\Working_API\zozi_ai_upload_session\upload_auto_05.py".
```





# _______________________________________________________________________________________

# Implementation Plan: ZOZI Supplier Product Upload — Speed-First Redesign

## Goal
Re-engineer the supplier product-upload flow into a modal-popup-driven, automation-first 5-step system
that completes a full product upload (including BG removal, AI analysis, all variant quantity fills,
and publish) **in under 30 seconds** for an experienced supplier.

---

## Overview of the Two Processes

| | Process A — Photo-First | Process B — Voice-First |
|---|---|---|
| Step 1 | Upload / Capture image | Upload / Capture image |
| Step 2 | BG Removal (auto-select best model) | BG Removal (auto-select best model) |
| Step 3 | AI detect → auto-fill all fields | 🎤 Voice note → NLP parse → auto-fill |
| Step 4 | Variant-per-color quantity popups | Variant-per-color quantity popups |
| Step 5 | Verify popup → Publish | Verify popup → Publish |

---

## Design Principles
- **Zero typing** wherever automation can fill it (name, description, tags, category, color).
- **Modal-popup-driven** — every step is a focused bottom-sheet / center modal, not a multi-page wizard.
- **Parallel processing** — BG removal fires simultaneously with AI analysis; both finish before Step 3.
- **Quantity popups per color** — one popup per color, looping through colors, each showing all sizes.
- **Universal variant support** — driven by `zozi_variant_config.json`: apparel (color/size), electronics
  (storage/RAM), beauty (volume/scent), jewelry (karat/plating), etc.

---

## Step-by-Step UI Flow

```
[ADD PRODUCT button]
        ↓
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 1 — MEDIA UPLOAD                                         │
│  [ 📷 Take Photo ]  [ 🗂️ Upload File ]                          │
│  ┌────────────────┐                                             │
│  │  image preview │  (thumbnail once selected)                  │
│  └────────────────┘                                             │
│  [ 🎤 Voice Note ]  [ ✨ Magic Editing ]                         │
│                             [Next →]                            │
└─────────────────────────────────────────────────────────────────┘
        ↓ (Next fires PARALLEL: bg-removal + AI-analyze)
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 2A — PROCESSING (spinner)                                │
│  "Removing background…  ████████░░  80%"                        │
│  "Analyzing product…    ████░░░░░░  40%"                        │
│  (both run in parallel — typical total: 5-8 s)                 │
└─────────────────────────────────────────────────────────────────┘
        ↓ AI fills everything automatically
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 2B — PHOTO EDITING CANVAS (optional, tap ✨)             │
│  [ br05 Clean ][ br06 Geo ][ br08 Prod ][ br11 Gap ]           │
│  [ Sharpen ][ Denoise ][ White Balance ][ Auto Light ]          │
│  [ Done ✓ ]                                                     │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 3 — AI RESULTS + FIELD REVIEW                            │
│  Name:        [Auto-filled ✓]  [edit]                           │
│  Description: [Auto-filled ✓]  [edit]                           │
│  Category:    [Auto-filled ✓]  [change ▾]                       │
│  Tags:        [chip][chip][chip]  [+ add]                       │
│  Color(s):    [🔵 Blue][🟡 Yellow][➕ Add color]               │
│  Fabric/Type: [tap chips: Cotton / Polyester / Leather…]        │
│  Price:       [ OMR _____ ]  (AI suggests 5.000)               │
│                         [Next: Set Quantities →]                │
└─────────────────────────────────────────────────────────────────┘
        ↓ (one popup per color, cycling)
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 4A — QUANTITY: 🔵 BLUE                (1 of 4)           │
│  S  [____]   M  [____]   L  [____]   XL [____]                 │
│  XXL [____]  (only sizes relevant to category shown)            │
│  [ Fill All = 50 ]              [Next Color →]                  │
└─────────────────────────────────────────────────────────────────┘
│  MODAL 4B — QUANTITY: 🟡 YELLOW              (2 of 4)           │
│  …same layout…                  [Next Color →]                  │
└─────────────────────────────────────────────────────────────────┘
        ↓ (electronics: storage×RAM instead; beauty: volume/scent, etc.)
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 5 — FINAL REVIEW & PUBLISH                               │
│  ┌──────────┐   Product: "Blue T-Shirt I Love Oman"             │
│  │ image ✓  │   Category: Clothing → T-Shirts                   │
│  └──────────┘   Colors: Blue, Yellow, Black, White              │
│                 Sizes: S, M, L, XL   Total Stock: 320           │
│                 Price: 5.000 OMR                                 │
│  [ ✏️ Edit Details ] [ 🖼️ Edit Images ] [ ✅ Publish ]          │
│        ↓ on Publish                                             │
│  "✅ Published! Thank you for using ZOZI"                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Files to Create / Modify

### Frontend — New Components

---

#### [NEW] `src/components/supplier/upload/UploadModal.tsx`
Single-entry modal covering Step 1 (file/camera input + Voice/Edit buttons).
- Accepts `onImage(file)`, `onVoice()`, `onEdit()` callbacks.
- Native `capture="environment"` for mobile camera.
- Drag-and-drop zone for desktop.

#### [NEW] `src/components/supplier/upload/ProcessingModal.tsx`
Dual progress-bar overlay shown during parallel BG removal + AI analysis.
- Two `<progress>` bars driven by SSE or polling.
- Auto-closes when both complete; passes results up.

#### [NEW] `src/components/supplier/upload/PhotoEditModal.tsx`
Full-screen canvas panel (already partially exists as `PhotoEditorModal.tsx` — refactor/extend).
- Integrates all 6 BG models (br05–br13) as one-tap buttons.
- Image tool strip (sharpen, denoise, white balance, etc.).
- "Done ✓" closes and returns processed blob.

#### [NEW] `src/components/supplier/upload/AIResultsModal.tsx`
Step 3 field-review modal.
- Shows all AI-filled fields as editable inline items.
- Color chip selector (auto-detected + add more).
- Fabric/material chip grid (from `zozi_variant_config.json` categories).
- Price input with AI-suggested value pre-filled.
- "Next: Set Quantities →" button.

#### [NEW] `src/components/supplier/upload/QuantityModal.tsx`
Step 4 cycling quantity popup.
- Props: `colorName`, `colorIndex`, `totalColors`, `sizes[]`, `onComplete(qty: Record<size, number>)`.
- "Fill All = 50" shortcut button.
- Keyboard-friendly: Tab moves between size inputs, Enter advances to next color.
- For non-apparel: renders relevant variant axes (storage×RAM, volume, etc.).

#### [NEW] `src/components/supplier/upload/VerifyPublishModal.tsx`
Step 5 final review.
- Product image thumbnail + all details.
- Total stock auto-calculated.
- Three buttons: Edit Details → re-opens AIResultsModal; Edit Images → re-opens PhotoEditModal; Publish → POST + success screen.

#### [NEW] `src/components/supplier/upload/VoiceModal.tsx`
Dedicated voice-recording bottom sheet (Step 3 voice path).
- Waveform animation while recording.
- NLP parse result displayed as editable chips before confirming.

---

### Frontend — Core Logic

#### [NEW] `src/lib/uploadOrchestrator.ts`
Central state machine managing the entire 5-step flow.
```typescript
type UploadPhase =
  | 'idle' | 'media' | 'processing' | 'photo_edit'
  | 'ai_results' | 'quantity' | 'verify' | 'done';
```
- Fires parallel `Promise.all([removeBg(), analyzeImage()])` at end of Step 1.
- Caches results so re-opening any modal is instant.
- Tracks current color index for quantity loop.
- Computes `totalStock` reactively.

#### [MODIFY] `src/lib/variantEngine.ts`
Add `getVariantAxesForCategory(category, subcategory)` that reads the embedded
`zozi_variant_config.json` to return the correct variant axes and their default options
for every supported product type. This replaces the current hardcoded arrays.

#### [NEW] `src/lib/variantConfig.ts`
Typed wrapper around `zozi_variant_config.json` — exposes:
- `getAxesForCategory(cat, subcat)` → `VariantAxis[]`
- `getDefaultOptions(axisKey)` → `string[]`
- `detectAxesFromVoice(voiceResult)` → `VariantAxis[]`
- `getMaterialOptions(productType)` → `string[]`

#### [MODIFY] `src/lib/wizardStore.ts`
Add upload orchestrator state:
- `uploadPhase: UploadPhase`
- `currentColorIndex: number`
- `quantityMap: Record<color, Record<size, number>>`
- `detectedAxes: VariantAxis[]`

---

### Frontend — Page Update

#### [MODIFY] `src/app/supplier/products/add/page.tsx`
Replace the current inline two-column layout with a single **"Add Product" button**
that opens `UploadModal`. All subsequent steps are driven by the orchestrator modals,
not the scrollable page layout.

---

### Backend — AI & BG Removal

#### [MODIFY] `backend/routers/suppliers/supplier.py`
- `/supplier/upload/remove-background` — already exists ✓ (no change needed)
- `/supplier/upload/ai-analyze` — already exists ✓ (no change needed)
- `/supplier/upload/voice-transcribe` — already exists ✓

New endpoint needed:
#### `POST /supplier/upload/analyze-parallel`
Accepts multipart with `image` field. Runs BG removal **and** AI analysis in parallel
(using `asyncio.gather`) and returns combined JSON:
```json
{
  "bg_removed_url": "...",
  "name": "...", "category": "...", "tags": [...],
  "colors": [...], "variants": {...}, "price_suggestion": 5.0
}
```
This single call replaces two sequential round-trips, cutting Step 2 time by ~40%.

---

### Backend — Variant Config Integration

#### [NEW] `backend/services/suppliers/variant_config_service.py`
Loads `zozi_variant_config.json` at startup and exposes:
- `get_axes_for_category(category, subcategory)` — returns applicable axes
- `get_material_options(product_type)` — chips for the fabric/material picker

#### [NEW] `GET /supplier/upload/variant-axes?category=clothing&subcategory=t-shirts`
Returns the correct axes + default options for the frontend to render quantity modals
correctly for any product type (apparel, electronics, beauty, jewelry, etc.).

---

### Playwright Test Suite

#### [NEW] `backend/tests/playwright/conftest.py`
- `login_as_supplier` fixture (re-uses token for session).
- `backend_url` fixture reading from env.
- `cleanup_product(id)` fixture calling `DELETE /supplier/products/{id}`.

#### [NEW] `backend/tests/playwright/test_upload_flow.py`
Tests **both** Process A (photo) and Process B (voice):
```
test_photo_upload_flow   — uploads image_04.jpg, bg removal, AI fill, qty, publish
test_voice_upload_flow   — uploads image_05.jpg, voice transcribe, field fill, publish
test_all_category_axes   — verifies correct axes rendered for clothing/electronics/beauty/jewelry
```

#### [MODIFY] `backend/requirements.txt`
Add `playwright>=1.40.0` and `pytest-playwright>=0.4.0`.

#### [NEW] `backend/scripts/run_playwright_tests.py`
```python
subprocess.run(["playwright", "install", "chromium"])
subprocess.run(["pytest", "tests/playwright/", "-v", "--headed=false"])
```

---

## Speed Budget (target ≤ 30 s total)

| Step | Action | Time |
|---|---|---|
| 1 | Image selected | < 1 s |
| 2 | Parallel BG removal + AI analysis | 5–8 s |
| 3 | Review AI fields (pre-filled, just glance) | 3–5 s |
| 4 | Quantity popups × N colors (Fill All = 50) | 2 s × N colors |
| 5 | Verify + Publish click + server response | 2–3 s |
| **Total (2 colors)** | | **~18 s** |
| **Total (4 colors)** | | **~26 s** |

> [!IMPORTANT]
> The "Fill All = 50" button on each quantity popup fills all size inputs at once — a supplier
> with 4 colors can complete Step 4 in 4 × 1 tap = 4 seconds total.

---

## Verification Plan

### Automated Tests
```bash
cd backend
python scripts/run_playwright_tests.py
```
- All 3 test cases pass (exit 0).
- Product appears in `GET /supplier/products` after publish.
- Product is deleted by cleanup fixture.

### Manual Verification
- Open `http://localhost:3000/supplier/products/add`.
- Click "Add Product" → modal appears (Step 1).
- Upload `D:\Projects\10- E-COMMERCE WEBSITE\zozi\image\image_04.jpg`.
- Confirm processing modal shows dual progress bars.
- Confirm AI fills name, category, tags, colors automatically.
- Fill quantities via color popups using "Fill All = 50".
- Publish → "Thank you for using ZOZI" screen appears.
- Navigate to `/supplier/products` → product visible in list.



