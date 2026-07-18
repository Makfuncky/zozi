# Discount System — Addendum: Country & Supplier Management

> Companion to `document/DISCOUNT_SYSTEM.md`. Appended here because the main doc was file-locked at edit time.

## Country scoping (country to country)
- `Coupon.country_code` is a nullable FK to `country_configs.code`. `NULL` = global (every country); a specific code = country-only.
- Admin CRUD lives in `backend/routers/coupons.py` (public validate + admin) and `backend/routers/admin_promotions.py` (`/admin/{code}/promotions/coupons`), which enforces country access via `enforce_country_access`. This lets an admin manage discounts per assigned country.

## Supplier-wise
- `Coupon` currently has **no `supplier_id`** column. Supplier-level discount control is achieved today through **Flash Sales** (each `FlashSale` carries `product_ids`; products are supplier-owned, so the supplier scope is derived from the product set) and via the promotion engine flag `allow_supplier_promotions`.
- To support per-supplier coupon codes, add a nullable `supplier_id` to `Coupon` (model column + migration). The router/controller already forward arbitrary fields through `model_dump(exclude_none=True)`, so no other code change is required.

## Discount application & stacking
- Validation + stacking happen in `coupons_controller.validate_coupon` and `promotion_controller` (order-tier preview + ledger). Combined-discount caps are enforced by `PromotionEngineConfig.max_combined_discount_percent` / `_amount` and `stacking_mode` (`best_only` | `stack_all` | `custom`).
