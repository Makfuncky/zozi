# Promotion System — Addendum: Banner, Flash Sales, Country & Effects

> Companion to `document/PROMOTION.md`. Appended here because the main doc was file-locked at edit time.

## Banner System & Background Effects

Banners are DB-backed (`backend/models/payments.py` -> `Banner`) and admin-managed via `BannerTab.tsx` (and the legacy `BannersPanel.tsx`). Public display uses `BannerCarousel.tsx`, mounted on the home page (`HomeClient.tsx`, `position="hero"`) and the product listing page (`products/page.tsx`, after the header and before `FilterSearchBar`, `position="product"`).

### Country management (country to country)
- `Banner.country_code` is a nullable FK. `NULL` = global banner shown in every country; a specific code = country-only.
- `GET /banners` now filters by the request country (`request.state.country_code`), returning `(country_code == X) OR (country_code IS NULL)`.
- `BannerTab` exposes a **Country** dropdown (fetched from `GET /countries`) so admins can target a banner to one country or leave it global.

### Background effects (celebration / season / occasion)
- Each banner carries an `effect` field: `balloons`, `poppers`, `ramadan`, `eid`, `christmas`, `diwali`, `newyear`, `aurora`, or `""` (none).
- `BannerCarousel` calls `useEffectStore.setEffect(banner.effect)` when the active banner changes, driving the global `BackgroundEffect.tsx` overlay (mounted in `layout.tsx`). The effect resets to `"none"` on carousel unmount. The animated background is therefore tied directly to the banner's celebration/season/occasion.

### Video & appearance
- `Banner` supports `video_url` (autoplay/muted/loop background video behind the content) plus `image_url`, gradient/`bg_color`, text/subtitle/button colors, `badge_text`/`badge_color`, and `cta_label`/`cta_url` — all editable in the canvas + `BannerTab`.
- **Implemented (see `PROMOTION.md` -> "Banner Canvas System & Background Effects"):** the full free-form **canvas** is done. `BannerCanvasEditor.tsx` lets staff add/drag/resize/rotate any shape (rect, ellipse, text, image, button, video) inside or outside the banner bounds; the scene is stored as `layout_json` on the `Banner` row and rendered by `BannerCarousel` via `BannerCanvasView`.

### Flash Sales - country & supplier
- `FlashSale.country_code` (nullable) scopes campaigns country to country. `FlashSale.product_ids` (JSON) defines the participating products; because products are supplier-owned, a flash sale is effectively **supplier-wise** through its product set.
- Admin routes: `backend/routers/flash_sales.py` (global admin) and `backend/routers/admin_promotions.py` (`/admin/{code}/promotions/flash-sales`).

### Router mounts (reference)
- `banners` -> `/banners` (public list + admin CRUD); `admin_banners` -> `/admin/banners`
- `coupons` -> `/coupons`
- `flash-sales` -> `/flash-sales`
- `admin_promotions` -> `/admin/promotions` + `/admin/{code}/promotions/...` (country router)