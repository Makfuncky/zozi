# Banner · Promotion · Flash-Sales · Discount — Code & Setup Reference

Single consolidated reference for the four subsystems. The two companion docs
(`document/DISCOUNT_SYSTEM.md`, `document/PROMOTION.md`) hold the long-form
prose; this file is the **code & setup** extraction.

---

## 0. Requirements (as implemented)

- **Banner** is managed by the admin team / employees.
- Banners are **country-wise**: each banner can target one country or be global.
- Banners use a **complete canvas system**: admin/employee can add any shape
  (rectangle, ellipse, text, image, video, button), drag it anywhere (inside or
  outside the banner), resize from 8 handles, rotate, recolor, set opacity,
  border-radius, font, and wire buttons to a CTA URL. The whole scene is stored
  as `layout_json`.
- Banner is rendered on the **product (main) page after the header and before
  the search bar** (`products/page.tsx`), and on the home hero.
- **Background effect animation** is tied to the banner / celebration / season /
  occasion and is chosen inside the banner canvas; `BannerCarousel` pushes it to
  the global `effectStore` which drives `BackgroundEffect.tsx`.
- **Promotion / Flash-Sales / Discount** are country-to-country and
  supplier-wise (flash sales via `product_ids`; coupons can add `supplier_id`).

---

## 1. Banner — Backend

### 1.1 Model (`backend/models/payments.py` → `Banner`)

```python
class Banner(Base):
    __tablename__ = "banners"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    link = Column(String, nullable=True)
    banner_type = Column(String, default="hero")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    bg_color = Column(String, nullable=True)
    text_color = Column(String, nullable=True)
    subtitle_color = Column(String, nullable=True)
    btn_bg_color = Column(String, nullable=True)
    btn_text_color = Column(String, nullable=True)
    badge_text = Column(String, nullable=True)
    badge_color = Column(String, nullable=True)
    effect = Column(String, nullable=True)          # balloons|poppers|ramadan|eid|christmas|diwali|newyear|aurora|""
    video_url = Column(String, nullable=True)
    cta_label = Column(String, nullable=True)
    cta_url = Column(String, nullable=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True, index=True)
    layout_json = Column(Text, nullable=True)        # <-- free-form canvas (JSON string)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country = relationship("CountryConfig", foreign_keys=[country_code])
```

DB migration (SQLite): `ALTER TABLE banners ADD COLUMN layout_json TEXT;`

### 1.2 Controller (`backend/controllers/banner_controller.py`)

`BannerCreate` / `BannerUpdate` gained `layout_json: Optional[str] = None`.
`_banner_to_dict` now returns `"layout_json": banner.layout_json`.
`create_banner` passes `layout_json=payload.layout_json`.

Country-aware read:

```python
def get_banners(db, banner_type=None, active_only=False, country_code=None):
    q = db.query(Banner)
    if country_code:
        q = q.filter(or_(Banner.country_code == country_code, Banner.country_code == None))
    ...
```

### 1.3 Router (`backend/routers/banners.py`)

```python
@router.get("", response_model=list[dict])
def list_banners(request: Request, position: Optional[str] = Query(None), db: Session = Depends(get_db)):
    country = getattr(request.state, "country_code", None)
    return get_banners(db, banner_type=position, active_only=True, country_code=country)
```

Admin CRUD: `POST /banners`, `PUT /banners/{id}`, `DELETE /banners/{id}`,
`POST /banners/{id}/image`. Country-admin routes live in
`backend/routers/admin_promotions.py` (`/admin/{code}/promotions/banners`).

---

## 2. Banner — Frontend Canvas

### 2.1 `components/BannerCanvasEditor.tsx` (NEW)

A complete free-form editor. Exports:

- `BannerCanvasEditor` — interactive editor (`value: BannerLayout | null`, `onChange`).
- `BannerCanvasView` — read-only renderer used by the carousel.
- `renderCanvasElement` — shared element renderer.
- Types: `BannerLayout`, `CanvasElement`, `CanvasEffect`.

`BannerLayout` shape:

```ts
interface BannerLayout {
  bg: { color: string; gradientFrom: string; gradientVia: string; gradientTo: string; imageUrl: string; videoUrl: string };
  effect: "" | "balloons" | "poppers" | "ramadan" | "eid" | "christmas" | "diwali" | "newyear" | "aurora";
  elements: CanvasElement[];
}
interface CanvasElement {
  id: string; type: "rect" | "ellipse" | "text" | "image" | "button" | "video";
  x: number; y: number; w: number; h: number; rotation: number; z: number;
  fill: string; stroke: string; strokeWidth: number; borderRadius: number; opacity: number;
  content?: string; textColor?: string; fontSize?: number; fontWeight?: number;
  src?: string; ctaUrl?: string;
}
```

Editor features: toolbar to add rect / ellipse / text / image / button / video;
drag-to-move (pointer capture); 8 resize handles; rotate; opacity; border-radius;
color pickers for fill / text / border; per-element image & video URL; button CTA
URL; layer front/back; delete. A Background & Effect section sets the bg color,
3-stop gradient, background image/video URL, and the celebration/season effect.
All coordinates are **percentages**, so the canvas is fully responsive.

### 2.2 `components/BannerCarousel.tsx`

Parses `banner.layout_json`; if present renders `<BannerCanvasView layout={layout} />`
(full canvas) instead of the legacy image/video block, and pushes
`banner.effect` (== `layout.effect`) to the global `effectStore`. Falls back to
the simple title/subtitle/badge/CTA overlay for banners without a saved canvas.

### 2.3 `app/admin/dashboard/tabs/BannerTab.tsx`

Embeds `<BannerCanvasEditor>` and persists `layout_json` on save (and sets
`banner.effect` from `layout.effect`). Keeps title/subtitle/badge/CTA/country
fields for the legacy overlay. Loads countries from `GET /countries` for the
per-country dropdown. New banners start from `DEFAULT_LAYOUT`; legacy banners
build a starter layout from their `bg_color`/`effect`.

### 2.4 Placement

`app/products/page.tsx` (after header, before `FilterSearchBar`):

```tsx
<BannerCarousel position="product" className="mb-6" />
```

`app/HomeClient.tsx` (hero):

```tsx
<BannerCarousel position="hero" />
```

`app/layout.tsx` mounts `<BackgroundEffect />` globally (driven by `effectStore`).

---

## 3. Promotion System (`backend/controllers/promotion_controller.py`,
`flash_sale_controller.py`; `app/admin/promotions/*`)

- `PromotionEngineConfig` singleton: engine switches, `stacking_mode`, combined-
  discount caps, points config.
- `PromotionOrderTier`: order-value bands → automatic discount (seeded: A–D).
- `FlashSale` / `FlashSaleItem`: time-boxed campaigns with `discount_pct`,
  `product_ids` (JSON), `country_code` (nullable → global).
- `FlashSalesPanel.tsx` uses `useAdminCountry()`; country routes under
  `/admin/{code}/promotions/flash-sales`.

### 3.1 Country & Supplier

| Scope | Field | Effect |
|-------|-------|--------|
| Global | `country_code = NULL` | visible in every country |
| Country | `country_code = "AE"` | only that country |
| Supplier (flash sale) | `product_ids` (supplier-owned products) | supplier-wise via product set |

To add per-supplier coupons: add nullable `supplier_id` to `Coupon` (model +
migration); routers/controllers forward it via `model_dump(exclude_none=True)`.

---

## 4. Discount System (`backend/controllers/coupons_controller.py`;
`routers/coupons.py`, `routers/admin_promotions.py`; `CouponsPanel.tsx`)

- `Coupon` (`coupons` table): `code` (UPPERCASE unique), `discount_type`
  (`percentage`|`fixed`), `discount_value`, `minimum_order`, `maximum_discount`,
  `usage_limit`/`usage_count`, `starts_at`/`expires_at`, `is_active`,
  `is_deleted`, `country_code`. `CouponUsage` tracks each redemption.
- Validation: normalize → active → expiry → usage cap → min order → compute → cap.
- Country scoping identical to Flash Sales (see §3.1). Admin routes:
  `/admin/{code}/promotions/coupons`.
- Soft-archive/restore; hard-delete blocked when `CouponUsage` exists.

---

## 5. Background Effects (celebration / season / occasion)

`effectStore` (`lib/effectStore.ts`) holds the active `effect`. `BannerCarousel`
calls `setEffect(banner.effect)` on the active banner and resets to `"none"` on
unmount. `BackgroundEffect.tsx` (fixed, `zIndex:0`, `pointer-events:none`) renders
balloons, poppers/confetti, ramadan, eid, christmas (snow), diwali (diyas),
newyear (sparklers), aurora. Effects are selected **inside the banner canvas**
(`BannerCanvasEditor` → Background & Effect dropdown), so the animated backdrop
always matches the banner's celebration/season/occasion.

---

## 6. Router Mounts (`backend/main.py`)

| Router | Prefix |
|--------|--------|
| `coupons` | `/coupons` |
| `banners` | `/banners` (public list + admin CRUD) |
| `flash_sales` | `/flash-sales` |
| `admin_promotions` | `/admin/promotions` + `/admin/{code}/promotions/...` (country router) |
| `admin_banners` | `/admin` |

---

## 7. Quick Endpoint Reference

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/banners?position=product` | Country-aware public banner list |
| GET | `/admin/banners` | Admin list (all) |
| POST | `/admin/banners` | Create banner (incl. `layout_json`) |
| PUT | `/admin/banners/{id}` | Update banner (incl. `layout_json`) |
| POST | `/banners/{id}/image` | Upload banner image |
| DELETE | `/admin/banners/{id}` | Delete banner |
| GET | `/countries` | Country list for targeting |
| POST | `/validate` | Validate coupon |
| GET/POST | `/admin/{code}/promotions/coupons` | Country coupons |
| GET/POST | `/admin/{code}/promotions/flash-sales` | Country flash sales |
| GET/POST | `/admin/{code}/promotions/banners` | Country banners |
