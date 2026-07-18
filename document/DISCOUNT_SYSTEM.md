# Discount System

Discounts are customer-facing savings applied at checkout. The system supports **coupon codes** (percentage or fixed-amount), which are country-scoped and admin-managed.

---

## Architecture

```
frontend/web_app/src/app/admin/promotions/CouponsPanel.tsx
        â”‚
        â–¼
apiFetch("/admin/promotions/coupons")
        â”‚
        â–¼
backend/routers/coupons.py          â† public validate + admin CRUD
backend/routers/admin_promotions.py â† country-admin CRUD (/admin/{code}/promotions/coupons)
        â”‚
        â–¼
backend/controllers/coupons_controller.py  â† validation + CRUD helpers
backend/controllers/promotion_controller.py â† order-tier preview + ledger
        â”‚
        â–¼
backend/models/payments.py   â† Coupon, CouponUsage
```

---

## Database Model (`backend/models/payments.py`)

### Coupon (`coupons` table)

| Column | Type | Notes |
|--------|------|-------|
| `id` | PK | |
| `code` | String unique | Uppercase-normalized |
| `discount_type` | String `default="percentage"` | `"percentage"` or `"fixed"` |
| `discount_value` | Numeric(5,2) | Percent (0-100) or fixed amount |
| `minimum_order` / `min_order` | Numeric(10,2) | Alias-compatible read |
| `maximum_discount` / `max_uses` | Numeric/Integer | Optional caps |
| `usage_limit` / `usage_count` | Integer | Tracked usage |
| `starts_at` / `expires_at` | DateTime | Validity window |
| `is_active` | Boolean | Soft active flag |
| `is_deleted` | Boolean `default=False` | Soft-delete |
| `deleted_at` | DateTime | |
| `deleted_by_id` | FK users.id | |
| `country_code` | String(10) FK `country_configs.code` | Nullable â†’ global; set â†’ country-only |
| `created_at` | DateTime | |

### CouponUsage (`coupons_usage` table)

| Column | Type | Notes |
|--------|------|-------|
| `id` | PK | |
| `coupon_id` | FK coupons.id | One use per row |
| `user_id` | FK users.id | Customer who used it |
| `order_id` | FK orders.id | Order where redeemed |
| `discount_amount` | Numeric | Amount taken at time of use |
| `created_at` | DateTime | |

A coupon with usage history **cannot be hard-deleted**; archive/disable instead.

---

## Backend Routes

### Public

| Method | Path | Description |
|--------|------|-------------|
| POST | `/validate` | Validate coupon + return discount quote |

### Admin (global, no country prefix)

`backend/routers/coupons.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List all coupons |
| POST | `/` | Create coupon (no country_code via this route) |
| DELETE | `/{coupon_id}` | Hard-delete (fails if usage exists) |

### Admin (country-scoped)

`backend/routers/admin_promotions.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/{code}/promotions/coupons` | List coupons filtered by country |
| GET | `/promotions/coupons?country=X` | Same via query param |
| POST | `/admin/{code}/promotions/coupons` | Create coupon scoped to country |
| POST | `/coupons/{id}/archive` | Soft-archive |
| POST | `/coupons/{id}/restore` | Restore archived |
| POST | `/coupons/bulk-archive` | Bulk archive |
| POST | `/coupons/bulk-restore` | Bulk restore |

---

## Coupon Validation Flow (`controllers/coupons_controller.py`)

1. Normalize code: `code.strip().upper()`
2. Look up by code where `is_active=True`
3. Check expiry (`expires_at < now` â†’ 410 Gone)
4. Check usage count vs limit
5. Check `minimum_order` against order total
6. Calculate discount:
   - **percentage**: `total Ã— discount_value / 100`
   - **fixed**: `min(discount_value, total)`
7. Cap at `maximum_discount` if set
8. Return `{valid, discount_amount, new_total, coupon}`

---

## Soft-Delete / Archive Pattern

- `is_deleted = True`, `is_active = False`
- `deleted_at = utcnow()`, `deleted_by_id = admin.id`
- List endpoints default to `is_deleted == False`
- `include_deleted=true` query param reveals all
- **Hard delete is blocked** if `CouponUsage` rows exist

---

## Country Scoping

- `country_code = None` â†’ coupon is **global** (visible in all countries)
- `country_code = "AE"` â†’ coupon is only valid/visible for UAE
- Admin lists accept `?country=*` (all) or `?country=AE` (filter)
- Country-router path: `/admin/{code}/promotions/coupons` â€” the `{code}` is the scope, not the coupon's country; the coupon's `country_code` is set from the path's `code` on creation

---

## Frontend

**Component**: `CouponsPanel.tsx`

- Uses `useAdminCountry()` to get `selectedCountry`
- API base: `/admin/promotions/coupons` (global route with country query)
- Displays code, discount type, value, min order, usage, expiry, status
- Form supports: code, type (percentage/fixed), value, max discount, min order, usage limit, start/end dates, active toggle
- Archive / restore actions via dedicated API endpoints
- Status badges: active, inactive, archived, expired

---

## Key Business Rules

- Codes are always normalized to **UPPERCASE** on creation
- A coupon code must be **globally unique** across all countries
- Expired coupons return HTTP 410
- Hard delete requires zero usage records
- Order-tier discounts and coupon discounts can stack (governed by `PromotionEngineConfig.stacking_mode`)
---

## Country & Supplier Management (consolidated)

### Country scoping (country to country)
- `Coupon.country_code` is a **nullable FK** to `country_configs.code`. `NULL` = global (every country); a specific code = country-only.
- Admin CRUD lives in `backend/routers/coupons.py` (public validate + admin) and `backend/routers/admin_promotions.py` (`/admin/{code}/promotions/coupons`), which enforces country access via `enforce_country_access`. An admin assigned to a country manages that country's coupons; the coupon's `country_code` is set from the route path.
- This same country-to-country pattern is shared by **Flash Sales** (`FlashSale.country_code`) and **Banners** (`Banner.country_code`).

### Supplier-wise management
- `Coupon` currently has **no `supplier_id`** column. Supplier-level discount control is achieved today through **Flash Sales**: each `FlashSale` carries `product_ids` (JSON); products are supplier-owned, so the supplier scope is derived from the product set. The promotion engine flag `allow_supplier_promotions` also gates supplier promotions.
- To support per-supplier coupon codes, add a nullable `supplier_id` to `Coupon` (model column + migration). The router/controller already forward arbitrary fields through `model_dump(exclude_none=True)`, so no other code change is required.

### Discount application & stacking
- Validation + stacking happen in `coupons_controller.validate_coupon` and `promotion_controller` (order-tier preview + ledger). Combined-discount caps are enforced by `PromotionEngineConfig.max_combined_discount_percent` / `_amount` and `stacking_mode` (`best_only` | `stack_all` | `custom`).

### Banner integration
- Banners drive a global animated **background effect** tied to the banner's celebration/season/occasion (see `document/PROMOTION.md` - Banner Canvas System). Coupon/promotion pages inherit that atmosphere automatically because `BannerCarousel` sets the effect store on mount.
