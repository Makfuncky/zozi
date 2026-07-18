

# Prompt - DISCOUNT SYSTEM | PROMOTIONS | FLASH SALES | SUPPLIER DISCOUNTS:

Read the below carefully and start implementation and test and run to ensure everything is integrated properly and running smoothly and also ensure that there should not be any hardcoded fallback which will block the actual functionality. 

After implementation update regarding implementation, integration and test into 
documents\CODEBASE_STATUS_MATRIX_DETAILED.md - `🎯 Component/Feature Status Matrix`

---

## Flash-Sales | Supplier Discounts | Promotions :-

There is 3 kind i told you 
1. Discounts which allowed by the Supplier on Product to Product which badge shoud be `Lime Green` 
2. Flash Sales which allowed by the Zozi Admin which is same Discounts thing but from Zozi on Product to Product which badge shoud be `Yellow`
3. Promotion/Deals which allowed by the Zozi Admin or Supplier both which is like buy `one get one free` or `bundle offer` which badge shoud be `Red`

and right now I can't see any badge even flash-sales is runing from all product by Zozi Admin 


- Flash Sales badge is not coming on the product and calculation of prices is also not reflecting with stricker on original price and showing new price. check the pasted image.
- All product-card should be reflect the discounted price and badge also of Flash-Sales like as I given you example Pasted Image.
- Admin just open the Flash Deal but it is not impacted on web_app and mobile_app.
- Check all the `web_app`, `backend`, `mobile_app` and fix it. 
- I marked in the Image pasted.
- `Flash Sales`, `Promotional Offers` should be announce by the admin and it should to show duration also.
- `Supplier Discounts` can be offer by the individual Supplier also and it should to show duration also.
- Please check all the code properly and connect backend to frontend and remove all the hardcode.



- Flash Sales badge is not coming on the product and calculation of prices is also not reflecting with stricker on original price and showing new price. check the pasted image.


- Admin just open the Flash Deal but it is not impacted on web_app and mobile_app.
- Check all the `web_app`, `backend`, `mobile_app` and fix it. 
- I marked in the Image pasted.
- `Flash Sales`, `Promotional Offers` should be announce by the admin and it should to show duration also.
- `Supplier Discounts` can be offer by the individual Supplier also and it should to show duration also.
- Please check all the code properly and connect backend to frontend and remove all the hardcode.

---

- Banner will also have 3 Slots for | Discounts | Flash-Sales | Promotion | as i marked into Banner into pasted image which should be flash if Admin alowed banner to run,

---

- Implement into both mobile_app and web_app properly and check also.
- After finishing implementation, test everything in detail to conclude it is done.

---




### Flash Offer Integration Delta

| Area | Implementation Status | Integration Notes | Validation |
|---|---|---|---|
| Backend flash sales | Live | Public `/flash-sales` serves active admin campaigns; `/products?sale_id=` filters sale-linked products; blank `product_ids` now correctly applies the flash sale to all active products, while targeted campaigns still override by product ID. **NEW:** Added `deals: bool = False` query param to `/products`; when `deals=True` and a global flash sale is active, the DB `min_discount` filter is skipped so flash-sale-only products (no stored `compare_price`) are correctly included | Existing backend flash-sale flow audited; `alembic upgrade head` applied migration `j1k2l3m4n5o6` (added `discount_starts_at` + `discount_ends_at` to `products`); 14/14 flash sale tests ✅ |
| Web promotional surfaces | Live | `SeasonalBanner.tsx` now renders **three distinct offer slots** inside the hero surface: Flash Sales, Promotional Offers, and Supplier Discounts. `offers/page.tsx` consumes admin promotional banners separately from supplier discounts so the channels do not overwrite each other. Supplier cards are filtered to `offer_type === "supplier_discount"` instead of accidentally showing flash-sale items during global sales | Editor diagnostics ✅; live backend validation on `127.0.0.1:8000` confirmed active `/flash-sales` and discounted `/products` payloads |
| Supplier discounts | Live | Supplier product create/update flows persist `compare_price`, `discount_starts_at`, and `discount_ends_at`; storefront surfaces consume those timed windows through backend product metadata. Offer end-time strip shown on web `ProductCard` and mobile `ProductCard`. Banner and offers surfaces now only display products marked `offer_type === "supplier_discount"` in the supplier slot | Source audit completed across backend + web + mobile supplier product screens |
| Product cards and pricing | **Fixed & Live** | Flash-sale products now surface a live ⚡ yellow pill badge (`-X% OFF`) plus strike-through original pricing. Shared helpers now normalize **string-decimal API payloads** (`price`, `compare_price`, `offer_discount_pct`) before computing discount badges, so card badges render reliably in both web and mobile. Promotion badge groundwork added with **red** badge styling for `offer_type === "promotion"`. **`QuickViewModal.tsx` hardcoded `fakeOriginal = price * 1.3` replaced with real `compare_price` + `offer_discount_pct` from backend** — no hardcoded pricing fallbacks remain | Backend: 14/14 flash sale tests ✅; live `127.0.0.1:8000/products?limit=5` returns discounted `price`, original `compare_price`, `offer_type="flash_sale"`, `offer_discount_pct`, and `offer_ends_at` ✅ |
| Mobile flash sales | Live | `app/flash-sales.tsx` loads public flash sales and fetches sale-specific products through `sale_id`; stale test contract updated from `discount_percentage/start_time/end_time` to live `discount_pct/starts_at/ends_at`. Mobile `ProductCard` now shows offer end-time ("⚡ ends MMM D" or "🏷 until MMM D") below the strikethrough price, and the dedicated flash-sales screen now normalizes string prices before `toFixed()` | Editor diagnostics ✅ |
| Mobile offers screen | Updated | `app/offers.tsx` renders real Flash Sales, Promotional Offers, and Supplier Discounts with duration windows instead of a generic `/products?deals=1` list; admin flash-sale payloads use normalized integer arrays in both web and mobile admin flows. `MobileSeasonalBanner.tsx` now mirrors web with **three offer panels**: Flash Sales, Promotional Offers, Supplier Discounts | Editor diagnostics ✅ |
| Shared product badges | Updated | Flash sale badge renders as a distinct ⚡ **yellow pill** (`bg-yellow-400 text-black font-extrabold`), supplier discount renders as a **lime green** badge, and promotion/deal support now maps to a **red** badge style. Shared discount parsing no longer depends on numeric-only payloads | `frontend/shared/src/productHelpers.ts` editor diagnostics ✅; `frontend/web_app/src/__tests__/components/ProductCard.test.tsx` covers string-price parsing + promotion badge behavior |



--------------------------------------------------------------------------------
--------------------------------------------------------------------------------



