# ZOZI Design System Governance Audit Report (GENERATED — do not hand-edit)

**Repo:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi`  
**Result:** 🔴 0 · 🟡 148 · 🟢 2  
**Design Debt Score:** `3111`  
**Token Coverage:** `87.7%` (278 distinct colors / 107 tokens / 860 files)  
**Ephemeral. Add to `.gitignore`.**

## Scorecard

| Code | Count | Sev | Meaning |
|---|---:|---|---|
| DS01 | 60 | 🟡 ADVISORY | hardcoded CSS: inline style={{...}} object in component |
| DS03 | 30 | 🟡 ADVISORY | raw/off-palette color literal (bypasses design tokens) |
| DS04 | 5 | 🟡 ADVISORY | color theme drift: near-duplicate colors used as if different |
| DS07 | 9 | 🟡 ADVISORY | hardcoded typography (font size / family literal) |
| DS08 | 30 | 🟡 ADVISORY | hardcoded spacing/dimension (raw px) |
| DS09 | 1 | 🟡 ADVISORY | inconsistent border-radius values |
| DS11 | 1 | 🟡 ADVISORY | inconsistent box-shadow values |
| DS13 | 11 | 🟡 ADVISORY | cross-workspace palette mismatch (web vs mobile differ) |
| DS16 | 1 | 🟡 ADVISORY | inconsistent motion durations (transition/animation) |
| DSI1 | 1 | 🟢 INFO | palette / token inventory |
| DSI2 | 1 | 🟢 INFO | token coverage |

## File-by-File Design Debt

| # | Score | Workspace | File | Colors | Off-palette | Inline styles | Issues |
|---:|---:|---|---|---:|---:|---:|---|
| 1 | 586 | mobile_app | `frontend\mobile_app\app\admin\dashboard.tsx` | 17 | 0 | 168 | inline×168, px×81 |
| 2 | 451 | mobile_app | `frontend\mobile_app\app\logistics-partner\profile.tsx` | 2 | 0 | 132 | inline×132, px×43 |
| 3 | 410 | mobile_app | `frontend\mobile_app\app\admin\email.tsx` | 62 | 0 | 110 | inline×110, px×61 |
| 4 | 364 | web_app | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | 133 | 52 | 33 | inline×33, off-color×52, tw-arb-size×45, z-magic, px×10 |
| 5 | 363 | mobile_app | `frontend\mobile_app\app\logistics-partner\shipments.tsx` | 21 | 2 | 103 | inline×103, off-color×2, px×38 |
| 6 | 341 | mobile_app | `frontend\mobile_app\app\checkout.tsx` | 13 | 0 | 105 | inline×105, px×20 |
| 7 | 297 | web_app | `frontend\web_app\_extra_files\gcss_proto\globals.css` | 572 | 42 | 0 | off-color×42, px×899 |
| 8 | 297 | web_app | `frontend\web_app\_extra_files\gcss_proto\globals_regen.css` | 567 | 42 | 0 | off-color×42, px×897 |
| 9 | 288 | mobile_app | `frontend\mobile_app\app\invoice.tsx` | 0 | 0 | 77 | inline×77, px×43 |
| 10 | 288 | mobile_app | `frontend\mobile_app\app\logistics-partner\dashboard.tsx` | 20 | 2 | 83 | inline×83, off-color×2, px×23 |
| 11 | 274 | mobile_app | `frontend\mobile_app\app\(tabs)\products\index.tsx` | 6 | 0 | 68 | inline×68, px×62 |
| 12 | 273 | web_app | `frontend\web_app\src\components\admin\commandCenter\hud.tsx` | 12 | 8 | 62 | inline×62, off-color×8, tw-arb-size×43, px×2 |
| 13 | 268 | mobile_app | `frontend\mobile_app\app\logistics-partner\payouts.tsx` | 0 | 0 | 86 | inline×86, px×8 |
| 14 | 244 | mobile_app | `frontend\mobile_app\app\supplier\logistics.tsx` | 10 | 0 | 68 | inline×68, px×30 |
| 15 | 240 | mobile_app | `frontend\mobile_app\app\(tabs)\profile.tsx` | 5 | 0 | 66 | inline×66, px×34 |
| 16 | 236 | mobile_app | `frontend\mobile_app\app\(tabs)\products\[id].tsx` | 4 | 0 | 72 | inline×72, px×16 |
| 17 | 222 | mobile_app | `frontend\mobile_app\app\tracking\[id].tsx` | 2 | 0 | 67 | inline×67, px×21 |
| 18 | 217 | mobile_app | `frontend\mobile_app\app\supplier\payouts.tsx` | 2 | 0 | 69 | inline×69, px×8 |
| 19 | 205 | web_app | `frontend\web_app\src\components\BackgroundEffect.tsx` | 49 | 16 | 33 | inline×33, off-color×16, px×26 |
| 20 | 197 | mobile_app | `frontend\mobile_app\app\logistics-partners\[id].tsx` | 0 | 0 | 50 | inline×50, px×31 |
| 21 | 194 | mobile_app | `frontend\mobile_app\app\barcode-scan.tsx` | 7 | 0 | 54 | inline×54, px×22 |
| 22 | 192 | mobile_app | `frontend\mobile_app\app\admin\analytics.tsx` | 10 | 0 | 54 | inline×54, px×26 |
| 23 | 191 | mobile_app | `frontend\mobile_app\app\supplier\dashboard.tsx` | 7 | 0 | 48 | inline×48, px×33 |
| 24 | 182 | mobile_app | `frontend\mobile_app\app\suppliers\[id].tsx` | 7 | 0 | 53 | inline×53, px×17 |
| 25 | 181 | mobile_app | `frontend\mobile_app\app\supplier\profile.tsx` | 1 | 0 | 58 | inline×58, px×5 |
| 26 | 181 | mobile_app | `frontend\mobile_app\app\(tabs)\cart.tsx` | 7 | 0 | 55 | inline×55, px×10 |
| 27 | 179 | mobile_app | `frontend\mobile_app\app\supplier\products\new.tsx` | 5 | 0 | 51 | inline×51, px×22 |
| 28 | 175 | mobile_app | `frontend\mobile_app\app\logistics-partner\scan.tsx` | 14 | 1 | 51 | inline×51, off-color×1, px×14 |
| 29 | 172 | mobile_app | `frontend\mobile_app\app\supplier\register.tsx` | 15 | 0 | 53 | inline×53, px×11 |
| 30 | 171 | mobile_app | `frontend\mobile_app\app\supplier\documents.tsx` | 4 | 0 | 40 | inline×40, px×35 |
| 31 | 170 | mobile_app | `frontend\mobile_app\app\offers.tsx` | 30 | 2 | 50 | inline×50, off-color×2, px×8 |
| 32 | 165 | mobile_app | `frontend\mobile_app\components\MobileSeasonalBanner.tsx` | 40 | 3 | 23 | inline×23, off-color×3, px×62 |
| 33 | 163 | mobile_app | `frontend\mobile_app\app\supplier\credibility.tsx` | 19 | 1 | 45 | inline×45, off-color×1, px×16 |
| 34 | 158 | mobile_app | `frontend\mobile_app\app\(tabs)\orders\[id].tsx` | 0 | 0 | 48 | inline×48, px×14 |
| 35 | 151 | mobile_app | `frontend\mobile_app\app\flash-sales.tsx` | 27 | 5 | 28 | inline×28, off-color×5, px×25 |
| 36 | 140 | mobile_app | `frontend\mobile_app\app\admin\product-verification.tsx` | 11 | 0 | 43 | inline×43, px×9 |
| 37 | 139 | mobile_app | `frontend\mobile_app\app\supplier\bulk.tsx` | 0 | 0 | 40 | inline×40, px×17 |
| 38 | 138 | mobile_app | `frontend\mobile_app\app\admin\coupons.tsx` | 8 | 0 | 36 | inline×36, px×22 |
| 39 | 137 | mobile_app | `frontend\mobile_app\app\referrals.tsx` | 0 | 0 | 45 | inline×45, px×2 |
| 40 | 129 | mobile_app | `frontend\mobile_app\app\settings.tsx` | 3 | 0 | 41 | inline×41, px×6 |
| 41 | 125 | mobile_app | `frontend\mobile_app\app\admin\flash-sales.tsx` | 11 | 0 | 32 | inline×32, px×21 |
| 42 | 122 | mobile_app | `frontend\mobile_app\app\admin\barcode.tsx` | 19 | 1 | 33 | inline×33, off-color×1, px×11 |
| 43 | 121 | mobile_app | `frontend\mobile_app\app\edit-profile.tsx` | 2 | 0 | 38 | inline×38, px×3 |
| 44 | 119 | mobile_app | `frontend\mobile_app\app\supplier\support.tsx` | 7 | 0 | 39 | inline×39, px×2 |
| 45 | 115 | mobile_app | `frontend\mobile_app\components\MobileBackgroundEffect.tsx` | 36 | 5 | 15 | inline×15, off-color×5, px×36 |
| 46 | 114 | mobile_app | `frontend\mobile_app\app\ticket-detail.tsx` | 1 | 0 | 37 | inline×37, px×3 |
| 47 | 114 | mobile_app | `frontend\mobile_app\app\admin\logistics-partners.tsx` | 10 | 0 | 34 | inline×34, px×8 |
| 48 | 114 | mobile_app | `frontend\mobile_app\app\(tabs)\_layout.tsx` | 18 | 0 | 34 | inline×34, px×8 |
| 49 | 111 | mobile_app | `frontend\mobile_app\app\admin\products.tsx` | 10 | 0 | 26 | inline×26, px×21 |
| 50 | 110 | web_app | `frontend\web_app\src\styles\globals.css` | 119 | 0 | 0 | px×178 |
| 51 | 109 | web_app | `frontend\web_app\src\styles\tokens.css` | 73 | 15 | 0 | off-color×15, px×43 |
| 52 | 107 | mobile_app | `frontend\mobile_app\app\supplier\orders.tsx` | 0 | 0 | 35 | inline×35, px×2 |
| 53 | 106 | mobile_app | `frontend\mobile_app\app\tickets.tsx` | 6 | 0 | 34 | inline×34, px×4 |
| 54 | 106 | mobile_app | `frontend\mobile_app\app\admin\banners.tsx` | 6 | 0 | 32 | inline×32, px×8 |
| 55 | 105 | mobile_app | `frontend\mobile_app\app\supplier\invoices.tsx` | 6 | 0 | 33 | inline×33, px×4 |
| 56 | 105 | mobile_app | `frontend\mobile_app\app\returns\[id].tsx` | 0 | 0 | 25 | inline×25, px×22 |
| 57 | 101 | mobile_app | `frontend\mobile_app\app\supplier\reports.tsx` | 7 | 0 | 33 | inline×33, px×2 |
| 58 | 100 | web_app | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | 16 | 16 | 9 | inline×9, off-color×16, tw-arb-size×9 |
| 59 | 99 | mobile_app | `frontend\mobile_app\app\help.tsx` | 1 | 0 | 31 | inline×31, px×4 |
| 60 | 99 | mobile_app | `frontend\mobile_app\app\admin\invoices.tsx` | 13 | 0 | 30 | inline×30, px×7 |

## Color Inventory (most used first)

| Color | Hex | Usage | Files | Palette status |
|---|---|---:|---:|---|
| ![#ffffff](https://via.placeholder.com/14/ffffff/ffffff) | `#ffffff` | 697 | 100 | ✅ token |
| ![#000000](https://via.placeholder.com/14/000000/000000) | `#000000` | 398 | 62 | ✅ token |
| ![#ef4444](https://via.placeholder.com/14/ef4444/ef4444) | `#ef4444` | 120 | 42 | ✅ token |
| ![#0f172a](https://via.placeholder.com/14/0f172a/0f172a) | `#0f172a` | 93 | 14 | ✅ token |
| ![#22c55e](https://via.placeholder.com/14/22c55e/22c55e) | `#22c55e` | 92 | 36 | ✅ token |
| ![#f59e0b](https://via.placeholder.com/14/f59e0b/f59e0b) | `#f59e0b` | 71 | 35 | ✅ token |
| ![#4a5d35](https://via.placeholder.com/14/4a5d35/4a5d35) | `#4a5d35` | 54 | 2 | ✅ token |
| ![#3b82f6](https://via.placeholder.com/14/3b82f6/3b82f6) | `#3b82f6` | 50 | 25 | ✅ token |
| ![#2fb43d](https://via.placeholder.com/14/2fb43d/2fb43d) | `#2fb43d` | 47 | 3 | 🔴 OFF-PALETTE |
| ![#f2c94c](https://via.placeholder.com/14/f2c94c/f2c94c) | `#f2c94c` | 39 | 3 | ✅ token |
| ![#32cd32](https://via.placeholder.com/14/32cd32/32cd32) | `#32cd32` | 38 | 14 | ✅ token |
| ![#d4af37](https://via.placeholder.com/14/d4af37/d4af37) | `#d4af37` | 37 | 8 | ✅ token |
| ![#6b7280](https://via.placeholder.com/14/6b7280/6b7280) | `#6b7280` | 37 | 18 | ✅ token |
| ![#ffd700](https://via.placeholder.com/14/ffd700/ffd700) | `#ffd700` | 33 | 11 | ✅ token |
| ![#94a3b8](https://via.placeholder.com/14/94a3b8/94a3b8) | `#94a3b8` | 31 | 12 | ✅ token |
| ![#9ca3af](https://via.placeholder.com/14/9ca3af/9ca3af) | `#9ca3af` | 31 | 17 | ✅ token |
| ![#111111](https://via.placeholder.com/14/111111/111111) | `#111111` | 25 | 11 | ✅ token |
| ![#facc15](https://via.placeholder.com/14/facc15/facc15) | `#facc15` | 25 | 9 | ✅ token |
| ![#f8fafc](https://via.placeholder.com/14/f8fafc/f8fafc) | `#f8fafc` | 21 | 11 | ✅ token |
| ![#2563eb](https://via.placeholder.com/14/2563eb/2563eb) | `#2563eb` | 18 | 9 | ✅ token |
| ![#ec4899](https://via.placeholder.com/14/ec4899/ec4899) | `#ec4899` | 17 | 9 | ✅ token |
| ![#8b5cf6](https://via.placeholder.com/14/8b5cf6/8b5cf6) | `#8b5cf6` | 17 | 9 | 🔴 OFF-PALETTE |
| ![#d97706](https://via.placeholder.com/14/d97706/d97706) | `#d97706` | 17 | 7 | ✅ token |
| ![#a855f7](https://via.placeholder.com/14/a855f7/a855f7) | `#a855f7` | 16 | 9 | ✅ token |
| ![#0ea5e9](https://via.placeholder.com/14/0ea5e9/0ea5e9) | `#0ea5e9` | 16 | 5 | ✅ token |
| ![#1e293b](https://via.placeholder.com/14/1e293b/1e293b) | `#1e293b` | 15 | 11 | ✅ token |
| ![#ea580c](https://via.placeholder.com/14/ea580c/ea580c) | `#ea580c` | 15 | 8 | ✅ token |
| ![#1a1a1a](https://via.placeholder.com/14/1a1a1a/1a1a1a) | `#1a1a1a` | 14 | 6 | ✅ token |
| ![#38bdf8](https://via.placeholder.com/14/38bdf8/38bdf8) | `#38bdf8` | 14 | 7 | ✅ token |
| ![#fde68a](https://via.placeholder.com/14/fde68a/fde68a) | `#fde68a` | 13 | 2 | 🔴 OFF-PALETTE |
| ![#f97316](https://via.placeholder.com/14/f97316/f97316) | `#f97316` | 13 | 8 | ✅ token |
| ![#2f9440](https://via.placeholder.com/14/2f9440/2f9440) | `#2f9440` | 13 | 3 | ✅ token |
| ![#7cfc00](https://via.placeholder.com/14/7cfc00/7cfc00) | `#7cfc00` | 12 | 6 | ✅ token |
| ![#fbfcf8](https://via.placeholder.com/14/fbfcf8/fbfcf8) | `#fbfcf8` | 12 | 3 | ✅ token |
| ![#cbd5e1](https://via.placeholder.com/14/cbd5e1/cbd5e1) | `#cbd5e1` | 11 | 8 | ✅ token |
| ![#e5e7eb](https://via.placeholder.com/14/e5e7eb/e5e7eb) | `#e5e7eb` | 11 | 9 | ✅ token |
| ![#14b8a6](https://via.placeholder.com/14/14b8a6/14b8a6) | `#14b8a6` | 11 | 8 | ✅ token |
| ![#59bc61](https://via.placeholder.com/14/59bc61/59bc61) | `#59bc61` | 11 | 3 | ✅ token |
| ![#1a5204](https://via.placeholder.com/14/1a5204/1a5204) | `#1a5204` | 10 | 10 | ✅ token |
| ![#eeff99](https://via.placeholder.com/14/eeff99/eeff99) | `#eeff99` | 10 | 10 | ✅ token |

## Color Theme Drift Clusters

These colors are visually near-identical but written differently — 
the classic symptom of theme drift.

- `#0f172a` ×93 ≈ `#111827` ×3
- `#f8faf5` ×2 ≈ `#f8fafc` ×21 ≈ `#f8fbf4` ×6 ≈ `#f8fcf3` ×2 ≈ `#f8fcf4` ×2 ≈ `#f9fbf5` ×4 ≈ `#fafcf6` ×2 ≈ `#fbfcf8` ×12
- `#1a1a1a` ×14 ≈ `#1c1917` ×6
- `#cbd5e1` ×11 ≈ `#d1d5db` ×9
- `#f1f5f9` ×10 ≈ `#f5f5f5` ×3
- `#ffd440` ×4 ≈ `#ffd740` ×9
- `#060e1c` ×3 ≈ `#080d18` ×7 ≈ `#080d1a` ×1 ≈ `#0c0c1d` ×1
- `#f0fdf0` ×4 ≈ `#f3f8ee` ×2 ≈ `#f4f8ee` ×2 ≈ `#f5f9ef` ×2 ≈ `#f5faf0` ×2
- `#f3f6ee` ×3 ≈ `#f5f7ef` ×3 ≈ `#f7faf3` ×6
- `#fef3c7` ×8 ≈ `#fff7bf` ×3
- `#475569` ×6 ≈ `#4b5563` ×3
- `#e3e9d8` ×3 ≈ `#e6ebdd` ×3
- `#edf1e5` ×3 ≈ `#eef3e6` ×3
- `#10233e` ×4 ≈ `#16213e` ×1
- `#1e3a5f` ×1 ≈ `#233a61` ×4
- `#fef2f2` ×2 ≈ `#fff7ed` ×1

## Design Damage Hotlist

| Sev | Rule | Domain | Location | Problem | Intended |
|---|---|---|---|---|---|
| 🟡 | DS03 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css` | off-palette color #2fb43d used 47× in 3 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, frontend\web_app\src\styles\glow.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\app\admin\barcode.tsx` | off-palette color #8b5cf6 used 17× in 9 file(s): frontend\mobile_app\app\admin\barcode.tsx, frontend\mobile_app\app\admin\users.tsx, frontend\mobile_app\app\logistics-partner\analytics.tsx, frontend\mobile_app\app\logistics-partner\dashboard.tsx +5 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #fde68a used 13× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\banner-effects.module.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\components\MobileBackgroundEffect.tsx` | off-palette color #a78bfa used 10× in 6 file(s): frontend\mobile_app\components\MobileBackgroundEffect.tsx, frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, frontend\web_app\src\components\BackgroundEffect.tsx +2 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\ui\SupplierBadge.native.tsx` | off-palette color #a3b3c8 used 8× in 2 file(s): frontend\shared\src\components\ui\SupplierBadge.native.tsx, frontend\shared\src\components\ui\SupplierBadge.web.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\components\ui\Footer.tsx` | off-palette color #6ae022 used 7× in 4 file(s): frontend\mobile_app\components\ui\Footer.tsx, frontend\mobile_app\components\ui\HeaderBar.tsx, frontend\mobile_app\components\ui\ScreenHeader.tsx, frontend\web_app\src\styles\comm.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\components\ProductCard.tsx` | off-palette color #d08c00 used 7× in 6 file(s): frontend\mobile_app\components\ProductCard.tsx, frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx +2 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css` | off-palette color #2dd4bf used 6× in 4 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, frontend\web_app\src\components\BackgroundEffect.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css` | off-palette color #325a24 used 6× in 2 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\ui\ErrorBoundary.tsx` | off-palette color #7f1d1d used 6× in 3 file(s): frontend\shared\src\components\ui\ErrorBoundary.tsx, frontend\web_app\src\app\supplier\bulk\draftUtils.ts, frontend\web_app\src\components\BannerCanvasEditor.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\lib\printStyles.ts` | off-palette color #cccccc used 6× in 4 file(s): frontend\mobile_app\lib\printStyles.ts, frontend\web_app\src\app\supplier\bulk\components\ColorPickerField.tsx, frontend\web_app\src\app\supplier\products\add\page.tsx, frontend\web_app\src\components\supplier\ProductImageCanvas.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\app\flash-sales.tsx` | off-palette color #dc2626 used 6× in 3 file(s): frontend\mobile_app\app\flash-sales.tsx, frontend\mobile_app\components\MobileSeasonalBanner.tsx, frontend\shared\src\components\ui\ErrorBoundary.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css` | off-palette color #1e3a8a used 5× in 3 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, frontend\web_app\src\app\supplier\bulk\draftUtils.ts | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #22d3ee used 5× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\logo\Logo.native.tsx` | off-palette color #a86000 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\logo\Logo.native.tsx` | off-palette color #f0c800 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\logo\Logo.native.tsx` | off-palette color #fff550 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | off-palette color #00c800 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\components\HeroBanner.tsx` | off-palette color #10233e used 4× in 4 file(s): frontend\mobile_app\components\HeroBanner.tsx, frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\logoArt.ts, frontend\shared\src\logo\Logo.native.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #1e1b4b used 4× in 1 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | off-palette color #2828ff used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\logo\LogoAnimation.tsx` | off-palette color #3d8018 used 4× in 2 file(s): frontend\shared\src\components\logo\LogoAnimation.tsx, frontend\shared\src\logo\LogoAnimation.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css` | off-palette color #40542e used 4× in 2 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css` | off-palette color #4f8ef7 used 4× in 2 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #60a5fa used 4× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css` | off-palette color #6fd648 used 4× in 2 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css` | off-palette color #a37e0e used 4× in 2 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | off-palette color #ff2828 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | off-palette color #ffdc28 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #064e3b used 3× in 1 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS04 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, fronte` | color drift (12× total): #f3f6ee (×3) ≈ #f5f7ef (×3) ≈ #f7faf3 (×6) | pick ONE token; these are visually the same color |
| 🟡 | DS04 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, fronte` | color drift (11× total): #fef3c7 (×8) ≈ #fff7bf (×3) | pick ONE token; these are visually the same color |
| 🟡 | DS04 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, fronte` | color drift (6× total): #e3e9d8 (×3) ≈ #e6ebdd (×3) | pick ONE token; these are visually the same color |
| 🟡 | DS04 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, fronte` | color drift (6× total): #edf1e5 (×3) ≈ #eef3e6 (×3) | pick ONE token; these are visually the same color |
| 🟡 | DS04 | design | `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css` | color drift (3× total): #fef2f2 (×2) ≈ #fff7ed (×1) | pick ONE token; these are visually the same color |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\mobile_app\components\SignaturePad.tsx, frontend\mobile_app\components\ui\SearchBar.tsx, frontend\mobile_app\th` | color drift (96× total): #0f172a (×93) ≈ #111827 (×3) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css` | color drift (51× total): #f8faf5 (×2) ≈ #f8fafc (×21) ≈ #f8fbf4 (×6) ≈ #f8fcf3 (×2) ≈ #f8fcf4 (×2) ≈ #f9fbf5 (×4) ≈ #fafcf6 (×2) ≈ #fbfcf8 (×12) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\mobile_app\theme\index.ts, frontend\shared\src\theme.native.ts, frontend\web_app\_extra_files\gcss_proto\global` | color drift (20× total): #1a1a1a (×14) ≈ #1c1917 (×6) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\mobile_app\components\SignaturePad.tsx, frontend\shared\src\components\ui\ThemeToggle.native.tsx, frontend\shar` | color drift (20× total): #cbd5e1 (×11) ≈ #d1d5db (×9) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\mobile_app\lib\printStyles.ts, frontend\shared\src\theme.native.ts, frontend\web_app\_extra_files\gcss_proto\gl` | color drift (13× total): #f1f5f9 (×10) ≈ #f5f5f5 (×3) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\shared\src\components\logo\LogoAnimation.tsx, frontend\shared\src\logo\LogoAnimation.tsx` | color drift (13× total): #ffd440 (×4) ≈ #ffd740 (×9) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/web_app | `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, fronte` | color drift (12× total): #060e1c (×3) ≈ #080d18 (×7) ≈ #080d1a (×1) ≈ #0c0c1d (×1) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\shared\src\theme.native.ts, frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files` | color drift (12× total): #f0fdf0 (×4) ≈ #f3f8ee (×2) ≈ #f4f8ee (×2) ≈ #f5f9ef (×2) ≈ #f5faf0 (×2) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\shared\src\theme.native.ts, frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files` | color drift (9× total): #475569 (×6) ≈ #4b5563 (×3) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\mobile_app\components\HeroBanner.tsx, frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\` | color drift (5× total): #10233e (×4) ≈ #16213e (×1) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\web_app\src\styles\tokens.css` | color drift (5× total): #1e3a5f (×1) ≈ #233a61 (×4) | web and mobile disagree on this color — unify in shared tokens |

## Domain: design

- 🟢 **DSI2** `frontend` — token coverage: 87.7% of color occurrences match the palette (2623/2990, 278 distinct colors)
- 🟡 **DS03** `frontend\web_app\_extra_files\gcss_proto\globals.css` — off-palette color #2fb43d used 47× in 3 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, frontend\web_app\src\styles\glow.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\app\admin\barcode.tsx` — off-palette color #8b5cf6 used 17× in 9 file(s): frontend\mobile_app\app\admin\barcode.tsx, frontend\mobile_app\app\admin\users.tsx, frontend\mobile_app\app\logistics-partner\analytics.tsx, frontend\mobile_app\app\logistics-partner\dashboard.tsx +5 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #fde68a used 13× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\banner-effects.module.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\components\MobileBackgroundEffect.tsx` — off-palette color #a78bfa used 10× in 6 file(s): frontend\mobile_app\components\MobileBackgroundEffect.tsx, frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, frontend\web_app\src\components\BackgroundEffect.tsx +2 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\ui\SupplierBadge.native.tsx` — off-palette color #a3b3c8 used 8× in 2 file(s): frontend\shared\src\components\ui\SupplierBadge.native.tsx, frontend\shared\src\components\ui\SupplierBadge.web.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\components\ui\Footer.tsx` — off-palette color #6ae022 used 7× in 4 file(s): frontend\mobile_app\components\ui\Footer.tsx, frontend\mobile_app\components\ui\HeaderBar.tsx, frontend\mobile_app\components\ui\ScreenHeader.tsx, frontend\web_app\src\styles\comm.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\components\ProductCard.tsx` — off-palette color #d08c00 used 7× in 6 file(s): frontend\mobile_app\components\ProductCard.tsx, frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx +2 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\_extra_files\gcss_proto\globals.css` — off-palette color #2dd4bf used 6× in 4 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, frontend\web_app\src\components\BackgroundEffect.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\_extra_files\gcss_proto\globals.css` — off-palette color #325a24 used 6× in 2 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\ui\ErrorBoundary.tsx` — off-palette color #7f1d1d used 6× in 3 file(s): frontend\shared\src\components\ui\ErrorBoundary.tsx, frontend\web_app\src\app\supplier\bulk\draftUtils.ts, frontend\web_app\src\components\BannerCanvasEditor.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\lib\printStyles.ts` — off-palette color #cccccc used 6× in 4 file(s): frontend\mobile_app\lib\printStyles.ts, frontend\web_app\src\app\supplier\bulk\components\ColorPickerField.tsx, frontend\web_app\src\app\supplier\products\add\page.tsx, frontend\web_app\src\components\supplier\ProductImageCanvas.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\app\flash-sales.tsx` — off-palette color #dc2626 used 6× in 3 file(s): frontend\mobile_app\app\flash-sales.tsx, frontend\mobile_app\components\MobileSeasonalBanner.tsx, frontend\shared\src\components\ui\ErrorBoundary.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\_extra_files\gcss_proto\globals.css` — off-palette color #1e3a8a used 5× in 3 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, frontend\web_app\src\app\supplier\bulk\draftUtils.ts → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #22d3ee used 5× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\logo\Logo.native.tsx` — off-palette color #a86000 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\logo\Logo.native.tsx` — off-palette color #f0c800 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\logo\Logo.native.tsx` — off-palette color #fff550 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` — off-palette color #00c800 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\components\HeroBanner.tsx` — off-palette color #10233e used 4× in 4 file(s): frontend\mobile_app\components\HeroBanner.tsx, frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\logoArt.ts, frontend\shared\src\logo\Logo.native.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #1e1b4b used 4× in 1 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` — off-palette color #2828ff used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\logo\LogoAnimation.tsx` — off-palette color #3d8018 used 4× in 2 file(s): frontend\shared\src\components\logo\LogoAnimation.tsx, frontend\shared\src\logo\LogoAnimation.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\_extra_files\gcss_proto\globals.css` — off-palette color #40542e used 4× in 2 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\_extra_files\gcss_proto\globals.css` — off-palette color #4f8ef7 used 4× in 2 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #60a5fa used 4× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\_extra_files\gcss_proto\globals.css` — off-palette color #6fd648 used 4× in 2 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\_extra_files\gcss_proto\globals.css` — off-palette color #a37e0e used 4× in 2 file(s): frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` — off-palette color #ff2828 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` — off-palette color #ffdc28 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #064e3b used 3× in 1 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS04** `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, fronte` — color drift (12× total): #f3f6ee (×3) ≈ #f5f7ef (×3) ≈ #f7faf3 (×6) → *pick ONE token; these are visually the same color*
- 🟡 **DS04** `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, fronte` — color drift (11× total): #fef3c7 (×8) ≈ #fff7bf (×3) → *pick ONE token; these are visually the same color*
- 🟡 **DS04** `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, fronte` — color drift (6× total): #e3e9d8 (×3) ≈ #e6ebdd (×3) → *pick ONE token; these are visually the same color*
- 🟡 **DS04** `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css, fronte` — color drift (6× total): #edf1e5 (×3) ≈ #eef3e6 (×3) → *pick ONE token; these are visually the same color*
- 🟡 **DS04** `frontend\web_app\_extra_files\gcss_proto\globals.css, frontend\web_app\_extra_files\gcss_proto\globals_regen.css` — color drift (3× total): #fef2f2 (×2) ≈ #fff7ed (×1) → *pick ONE token; these are visually the same color*
- 🟡 **DS07** `frontend` — 58 distinct hardcoded font sizes: 0.75rem, 0.7rem, 0.875rem, 0.8rem, 1.05rem, 1.125rem, 1.15rem, 1.25rem, 1.35rem, 1.5rem, 1.6rem, 1.7rem ... → *collapse onto a type scale (text-xs/sm/base/lg/xl...); max ~8 steps*
- 🟡 **DS07** `frontend\shared\src\components\logo\Logo.web.tsx` — font family literal 'var(--font-nunito, 'Nunito', var(--font-body, 'Sora', system-ui, sans-serif))' hardcoded in 5 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\_extra_files\gcss_proto\globals.css` — font family literal 'inherit' hardcoded in 5 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\_extra_files\gcss_proto\globals.css` — font family literal 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace' hardcoded in 3 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\_extra_files\gcss_proto\globals.css` — font family literal '"Arabic UI"' hardcoded in 3 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\_extra_files\gcss_proto\globals.css` — font family literal 'var(--font-arabic), "Arabic UI", "Noto Naskh Arabic", "Noto Sans Arabic", "Segoe UI", Tahoma,
               "Arial Unicode MS", sans-serif' hardcoded in 3 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\_extra_files\gcss_proto\globals.css` — font family literal 'var(--font-body), Sora, system-ui, sans-serif' hardcoded in 3 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\shared\src\components\logo\LogoAnimation.tsx` — font family literal 'var(--font-body, 'Sora', system-ui, sans-serif)' hardcoded in 2 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\_extra_files\gcss_proto\globals.css` — font family literal 'var(--font-body), Sora, sans-serif' hardcoded in 2 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS09** `frontend` — 62 distinct border-radius values: 0, 0 0 4px 4px, 0.25rem, 0.5rem, 0.75rem, 0px, 1, 1.25rem, 1.2rem, 1.4rem → *standardize on 3-4 radii tokens (sm/md/lg/full)*
- 🟡 **DS11** `frontend` — 103 distinct shadow definitions — no elevation system → *define 3 elevation tokens (shadow-sm/md/lg) and reuse them*
- 🟡 **DS16** `frontend` — 9 distinct animation durations: 0ms, 1000ms, 120ms, 150ms, 180ms, 200ms, 300ms, 500ms, 700ms → *standardize on 2-3 motion tokens (150ms/250ms/400ms)*
- 🟢 **DSI1** `frontend` — top colors in use: #ffffff×697, #000000×398, #ef4444×120, #0f172a×93, #22c55e×92, #f59e0b×71, #4a5d35×54, #3b82f6×50, #2fb43d×47, #f2c94c×39

## Domain: web_app

- 🟡 **DS01** `frontend\web_app\src\components\admin\commandCenter\hud.tsx` — 62 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\BackgroundEffect.tsx` — 33 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — 33 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS08** `frontend\web_app\_extra_files\gcss_proto\globals.css` — 899 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\_extra_files\gcss_proto\globals_regen.css` — 897 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\styles\globals.css` — 178 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\styles\comm.css` — 63 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\styles\tokens.css` — 43 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\components\BackgroundEffect.tsx` — 26 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*

## Domain: mobile_app

- 🟡 **DS01** `frontend\mobile_app\app\admin\dashboard.tsx` — 168 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\logistics-partner\profile.tsx` — 132 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\email.tsx` — 110 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\checkout.tsx` — 105 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\logistics-partner\shipments.tsx` — 103 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\logistics-partner\payouts.tsx` — 86 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\logistics-partner\dashboard.tsx` — 83 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\invoice.tsx` — 77 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\(tabs)\products\[id].tsx` — 72 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\payouts.tsx` — 69 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\logistics.tsx` — 68 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\(tabs)\products\index.tsx` — 68 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\tracking\[id].tsx` — 67 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\(tabs)\profile.tsx` — 66 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\profile.tsx` — 58 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\(tabs)\cart.tsx` — 55 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\barcode-scan.tsx` — 54 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\analytics.tsx` — 54 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\suppliers\[id].tsx` — 53 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\register.tsx` — 53 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\products\new.tsx` — 51 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\logistics-partner\scan.tsx` — 51 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\offers.tsx` — 50 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\logistics-partners\[id].tsx` — 50 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\dashboard.tsx` — 48 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\(tabs)\orders\[id].tsx` — 48 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\referrals.tsx` — 45 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\credibility.tsx` — 45 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\product-verification.tsx` — 43 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\settings.tsx` — 41 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\bulk.tsx` — 40 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\documents.tsx` — 40 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\support.tsx` — 39 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\edit-profile.tsx` — 38 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\ticket-detail.tsx` — 37 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\coupons.tsx` — 36 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\orders.tsx` — 35 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\tickets.tsx` — 34 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\logistics-partners.tsx` — 34 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\(tabs)\_layout.tsx` — 34 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\invoices.tsx` — 33 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\reports.tsx` — 33 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\barcode.tsx` — 33 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\banners.tsx` — 32 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\flash-sales.tsx` — 32 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\help.tsx` — 31 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\guide.tsx` — 30 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\invoices.tsx` — 30 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\components\AddressesScreen.tsx` — 28 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\flash-sales.tsx` — 28 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\label.tsx` — 27 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\products\index.tsx` — 27 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\components\ProductCard.tsx` — 26 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\chatbot.tsx` — 26 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\supplier\notification-preferences.tsx` — 26 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\bank-accounts.tsx` — 26 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\mobile_app\app\admin\products.tsx` — 26 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS08** `frontend\mobile_app\app\admin\dashboard.tsx` — 81 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\components\MobileSeasonalBanner.tsx` — 62 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\(tabs)\products\index.tsx` — 62 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\admin\email.tsx` — 61 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\invoice.tsx` — 43 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\logistics-partner\profile.tsx` — 43 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\logistics-partner\shipments.tsx` — 38 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\components\MobileBackgroundEffect.tsx` — 36 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\supplier\documents.tsx` — 35 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\(tabs)\profile.tsx` — 34 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\supplier\dashboard.tsx` — 33 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\logistics-partners\[id].tsx` — 31 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\supplier\logistics.tsx` — 30 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\admin\analytics.tsx` — 26 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\flash-sales.tsx` — 25 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\logistics-partner\dashboard.tsx` — 23 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\barcode-scan.tsx` — 22 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\supplier\products\new.tsx` — 22 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\returns\[id].tsx` — 22 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\admin\coupons.tsx` — 22 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\components\ui\ErrorBoundary.tsx` — 21 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\tracking\[id].tsx` — 21 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\admin\flash-sales.tsx` — 21 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*

## Domain: shared

- 🟡 **DS08** `frontend\shared\src\components\ui\ErrorBoundary.tsx` — 21 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
