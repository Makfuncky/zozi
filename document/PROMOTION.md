# Promotion System

Promotions cover **order-tier discounts**, **flash sales**, **promotion engine config**, and **coupon/banner country management**. This doc focuses on the promotion engine and flash-sale subsystems.

---

## Architecture

```
frontend/web_app/src/app/admin/promotions/
  PromotionBuilderPanel.tsx   â† engine config + tiers
  FlashSalesPanel.tsx         â† flash sale CRUD
  CouponsPanel.tsx            â† coupon CRUD (see DISCOUNT_SYSTEM.md)
  BannersPanel.tsx            â† banner CRUD (see BANNER_PROMOTION_DISCOUNT_CODE.md)
        â”‚
        â–¼
/api/admin/promotions/
  â”œâ”€â”€ config          â† promotion engine settings
  â”œâ”€â”€ tiers           â† order-tier discount bands
  â”œâ”€â”€ flash-sales     â† flash sale campaigns
  â”œâ”€â”€ coupons         â† coupon CRUD + country scope
  â”œâ”€â”€ banners         â† banner CRUD + country scope
  â””â”€â”€ /{code}/promotions/  â† country-router sub-routes
        â”‚
        â–¼
backend/controllers/
  promotion_controller.py     â† engine config + tiers logic
  flash_sale_controller.py    â† flash sale CRUD logic
  coupons_controller.py       â† coupon validation + CRUD
        â”‚
        â–¼
backend/models/
  marketing.py    â† FlashSale, FlashSaleItem, EmailCampaign...
  payments.py     â† Coupon, Banner, PromotionEngineConfig, PromotionOrderTier, PromotionLedgerEntry
```

---

## Models

### PromotionEngineConfig (`promotion_engine_config` table)

Singleton table (1 row). Controls the promotion engine globally.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `engine_enabled` | bool | false | Master switch |
| `allow_product_coupons` | bool | true | |
| `allow_category_coupons` | bool | true | |
| `allow_order_tier_discounts` | bool | true | |
| `allow_referral_rewards` | bool | true | |
| `allow_supplier_promotions` | bool | true | |
| `allow_global_coupons` | bool | true | |
| `stacking_mode` | str | "best_only" | `"best_only"`, `"stack_all"`, `"custom"` |
| `max_combined_discount_percent` | Decimal | 50.00 | Cap on combined discount % |
| `max_combined_discount_amount` | Decimal | 0.000 | Cap on combined discount amount (0 = none) |
| `show_savings_line_item` | bool | true | Show savings line on checkout |
| `tier_discount_visible` | bool | true | Show tier discount to customer |
| `points_per_omr` | int | 1000 | Points earned per 1 OMR spent |
| `referral_referrer_points` | int | 100 | |
| `referral_referee_points` | int | 100 | |
| `points_expiry_months` | int | 12 | |
| `referral_monthly_cap` | int | 20 | |
| `referral_verification_delay_days` | int | 7 | |
| `min_points_redeem` | int | 1000 | Minimum points to redeem |
| `allow_partial_points_redemption` | bool | true | |

### PromotionOrderTier (`promotion_order_tiers` table)

Order-value bands that trigger automatic discounts.

| Field | Type | Description |
|-------|------|-------------|
| `id` | PK | |
| `tier_name` | String | Display name (e.g. "Tier A") |
| `min_order_amount` | Numeric | Lower bound (inclusive) |
| `max_order_amount` | Numeric | Upper bound (inclusive), nullable = no max |
| `discount_type` | String | `"fixed"` or `"percent"` |
| `discount_value` | Numeric | Amount or percent |
| `stacking_allowed` | Bool | Can this tier stack with coupons? |
| `is_active` | Bool | |
| `sort_order` | Int | Display order |
| `updated_by` | FK users.id | |

### PromotionLedgerEntry (`promotion_ledger_entries` table)

Audit trail for each discount applied at checkout.

| Field | Type | Description |
|-------|------|-------------|
| `id` | PK | |
| `order_id` | FK | |
| `user_id` | FK | Customer |
| `promotion_type` | String | `"order_tier"`, `"coupon"`, etc. |
| `promotion_code` | String | Human-readable code |
| `tier_id` | FK | |
| `discount_amount` | Numeric | |
| `points_awarded` | Int | |
| `points_redeemed` | Int | |
| `stacking_flag` | Bool | |
| `source` | String | `"checkout"`, etc. |
| `metadata_json` | JSON | |

### FlashSale (`flash_sales` table)

| Field | Type | Description |
|-------|------|-------------|
| `id` | PK | |
| `title` | String | |
| `description` | Text | |
| `starts_at` | DateTime | |
| `ends_at` | DateTime | |
| `discount_pct` | Numeric(5,2) | 0-100 |
| `is_active` | Bool | |
| `is_deleted` | Bool | Soft-delete |
| `deleted_at` | DateTime | |
| `deleted_by_id` | FK users.id | |
| `product_ids` | JSON | Array of product IDs |
| `country_code` | String(10) FK | Nullable = global; set = country-only |
| `created_at` | DateTime | |

### FlashSaleItem (`flash_sale_items` table)

| Field | Type | Description |
|-------|------|-------------|
| `id` | PK | |
| `flash_sale_id` | FK flash_sales.id | |
| `product_id` | FK products.id | |
| `original_price` | Numeric(10,2) | |
| `discounted_price` | Numeric(10,2) | |
| `quantity_limit` | Integer | Per-customer cap |
| `country_code` | String(10) FK | Mirrors parent flash sale |

---

## Order Tier Discount Algorithm

```
calculate_order_tier_discount(subtotal, db):
  1. Load PromotionEngineConfig singleton
  2. If engine_enabled=False OR allow_order_tier_discounts=False â†’ return (0, None)
  3. Find matching tier: subtotal âˆˆ [min_order, max_order] AND is_active
  4. Compute discount:
       - fixed:   discount_value
       - percent: subtotal Ã— discount_value / 100
  5. Clamp:
       - discount â‰¤ subtotal Ã— max_combined_discount_percent / 100
       - discount â‰¤ max_combined_discount_amount (if > 0)
       - discount â‰¤ subtotal (never exceed order)
  6. Return (discount, matched_tier)
```

**Tier matching**: ordered by `sort_order ASC, min_order ASC`. First matching tier wins.

### Preview

`POST /admin/promotions/preview`

```json
{
  "order_subtotal": 100.00,
  "coupon_discount": 10.00
}
```

```json
{
  "engine_enabled": true,
  "stacking_mode": "best_only",
  "subtotal": 100.00,
  "coupon_discount": 10.00,
  "after_coupon": 90.00,
  "tier_discount": 4.50,
  "final_discount": 14.50,
  "final_payable_before_tax_shipping": 85.50,
  "matched_tier": { "tier_name": "Tier D", ... }
}
```

---

## Flash Sales

### Lifecycle

1. **Create** `POST /admin/promotions/flash-sales`
   - `starts_at` must be < `ends_at`
   - `discount_pct` must be 0-100
   - `country_code` is set from path or body (optional)
2. **Update** `PUT /admin/promotions/flash-sales/{id}`
3. **Archive** `POST /flash-sales/{id}/archive` â€” soft-delete
4. **Restore** `POST /flash-sales/{id}/restore`
5. **Bulk archive/restore** via `BulkActionRequest`

### Active-Sale Lookup (public)

`GET /admin/promotions/flash-sales` (active_only=true by default)

Filters: `is_active=True AND starts_at â‰¤ now AND ends_at â‰¥ now`, ordered by `ends_at ASC`.

**Cache**: TTL 45s, versioned, invalidated on create/update/delete.

---

## Country Management

All three systems (coupons, flash-sales, banners) support per-country scoping:

| Scope | `country_code` value | Effect |
|-------|---------------------|--------|
| Global | `null` / not set | Visible in all countries |
| Country-specific | `"AE"`, `"OM"`, etc. | Only visible when admin is scoped to that country |

### Admin Country Routes

Registered from `main.py` as a country-router under `/admin/{code}/promotions/...`:

| Method | Path | Action |
|--------|------|--------|
| GET | `/{code}/promotions/coupons` | List coupons for country |
| POST | `/{code}/promotions/coupons` | Create coupon for country |
| GET | `/{code}/promotions/flash-sales` | List flash sales for country |
| GET | `/{code}/promotions/banners` | List banners for country |
| POST | `/{code}/promotions/banners` | Create banner for country |
| PUT | `/{code}/promotions/banners/{id}` | Update banner |
| DELETE | `/{code}/promotions/banners/{id}` | Delete banner |

`enforce_country_access(code, db=db)` is called on every country-router handler to ensure the requesting admin has access to that country.

---

## Frontend Components

### PromotionBuilderPanel.tsx

- Loads config (`/admin/admin/promotions/config`) and tiers (`/admin/admin/promotions/tiers`)
- Toggle engine switches, stacking mode, cap values
- Create/edit/delete order tiers via modal
- **Preview** panel: enter subtotal + coupon discount, see calculated tier discount and final payable

### FlashSalesPanel.tsx

- Uses `useAdminCountry()` to scope data
- Lists flash sales with status badges (Active / Upcoming / Expired / Inactive / Archived)
- Create/update form: title, description, discount_pct, start/end datetime, active toggle
- Duration shown as `Xd Yh`
- Archive/restore actions

---

## Tier Defaults

Seeded automatically on first config access:

| Tier | Min Order | Max Order | Type | Value |
|------|-----------|-----------|------|-------|
| Tier A | 10.00 | 24.99 | fixed | 0.50 |
| Tier B | 25.00 | 49.99 | fixed | 1.50 |
| Tier C | 50.00 | 99.99 | fixed | 4.00 |
| Tier D | 100.00 | â€” | percent | 5.00 |

---

## Key Business Rules

- Tier discount is computed on the **post-coupon** subtotal (stacking chain: coupon first, then tier)
- Tier discount cannot exceed `max_combined_discount_percent` of original subtotal
- Tier discount cannot exceed `max_combined_discount_amount`
- Points conversion: `points_per_omr Ã— order_value` (only if `allow_referral_rewards` is on)
- Referral monthly cap limits total points given per referrer per month
- Points expire after `points_expiry_months` from earning date
---

## Banner Canvas System & Background Effects

Banners are DB-backed (`backend/models/payments.py` -> `Banner`) and admin/employee-managed. A **complete free-form canvas** lets staff design any banner: add rectangles, ellipses, text, images, video, and buttons; drag them anywhere (inside or outside the banner bounds); resize from 8 handles; rotate; recolor; set opacity, border-radius, font size/weight; and wire buttons to a CTA URL. The scene is stored as `layout_json` (JSON string) on the `Banner` row.

### Components
- `components/BannerCanvasEditor.tsx` — interactive editor (`BannerCanvasEditor`) + read-only renderer (`BannerCanvasView`). Exports `BannerLayout`, `CanvasElement`, `CanvasEffect` types.
- `components/BannerCarousel.tsx` — on the public site; parses `banner.layout_json` and renders `<BannerCanvasView>` when present, else the legacy image/video layout. Pushes `banner.effect` to the global `effectStore`.
- `app/admin/dashboard/tabs/BannerTab.tsx` — embeds the canvas editor and persists `layout_json` (and `effect`) on save; keeps title/subtitle/badge/CTA/country fields for the legacy overlay; loads countries from `GET /countries`.
- `app/products/page.tsx` — `<BannerCarousel position="product" />` after the header and before `FilterSearchBar` (the main page placement).
- `app/HomeClient.tsx` — `<BannerCarousel position="hero" />`.
- `app/layout.tsx` — mounts `<BackgroundEffect />` globally.

### Country management (country to country)
- `Banner.country_code` is a nullable FK. `NULL` = global banner shown in every country; a specific code = country-only.
- `GET /banners` filters by `request.state.country_code`, returning `(country_code == X) OR (country_code IS NULL)`.
- `BannerTab` exposes a **Country** dropdown so admins target one country or leave it global.

### Background effects (celebration / season / occasion)
- Each banner carries an `effect`: `balloons`, `poppers`, `ramadan`, `eid`, `christmas`, `diwali`, `newyear`, `aurora`, or `""` (none). The effect is chosen **inside the banner canvas** (Background & Effect section).
- `BannerCarousel` calls `useEffectStore.setEffect(banner.effect)` when the active banner changes, driving the global `BackgroundEffect.tsx` overlay; it resets to `"none"` on unmount. The animated background is therefore tied directly to the banner's celebration/season/occasion.

### Video & appearance
- `Banner` supports `video_url` (autoplay/muted/loop background) plus `image_url`, gradient/`bg_color`, text/subtitle/button colors, `badge_text`/`badge_color`, and `cta_label`/`cta_url` — all editable in the canvas + `BannerTab`.

### Flash Sales - country & supplier
- `FlashSale.country_code` (nullable) scopes campaigns country to country. `FlashSale.product_ids` (JSON) defines the participating products; because products are supplier-owned, a flash sale is effectively **supplier-wise** through its product set.
- Admin routes: `backend/routers/flash_sales.py` (global admin) and `backend/routers/admin_promotions.py` (`/admin/{code}/promotions/flash-sales`).
