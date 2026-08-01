# ZOZI Design System Governance Audit Report (GENERATED — do not hand-edit)

**Repo:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi`  
**Result:** 🔴 14 · 🟡 158 · 🟢 2  
**Design Debt Score:** `5148`  
**Token Coverage:** `83.3%` (279 distinct colors / 88 tokens / 831 files)  
**Ephemeral. Add to `.gitignore`.**

## Scorecard

| Code | Count | Sev | Meaning |
|---|---:|---|---|
| DS01 | 60 | 🟡 ADVISORY | hardcoded CSS: inline style={{...}} object in component |
| DS02 | 8 | 🔴 VIOLATION | hardcoded CSS: <style> tag inside a component file |
| DS03 | 30 | 🟡 ADVISORY | raw/off-palette color literal (bypasses design tokens) |
| DS04 | 3 | 🟡 ADVISORY | color theme drift: near-duplicate colors used as if different |
| DS05 | 5 | 🟡 ADVISORY | Tailwind arbitrary value bypassing tokens (bg-[#...], w-[123px]...) |
| DS06 | 3 | 🔴 VIOLATION | !important usage (specificity war) |
| DS07 | 9 | 🟡 ADVISORY | hardcoded typography (font size / family literal) |
| DS08 | 30 | 🟡 ADVISORY | hardcoded spacing/dimension (raw px) |
| DS09 | 1 | 🟡 ADVISORY | inconsistent border-radius values |
| DS10 | 3 | 🔴 VIOLATION | magic z-index (>=1000) |
| DS11 | 1 | 🟡 ADVISORY | inconsistent box-shadow values |
| DS13 | 18 | 🟡 ADVISORY | cross-workspace palette mismatch (web vs mobile differ) |
| DS16 | 1 | 🟡 ADVISORY | inconsistent motion durations (transition/animation) |
| DSI1 | 1 | 🟢 INFO | palette / token inventory |
| DSI2 | 1 | 🟢 INFO | token coverage |

## File-by-File Design Debt

| # | Score | Workspace | File | Colors | Off-palette | Inline styles | Issues |
|---:|---:|---|---|---:|---:|---:|---|
| 1 | 697 | web_app | `frontend\web_app\src\styles\globals.css` | 572 | 61 | 0 | off-color×61, !important×38, z-magic, px×899 |
| 2 | 586 | mobile_app | `frontend\mobile_app\app\admin\dashboard.tsx` | 17 | 0 | 168 | inline×168, px×81 |
| 3 | 503 | web_app | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | 144 | 58 | 33 | inline×33, style-tag, off-color×58, tw-arb-size×45, z-magic, px×10 |
| 4 | 451 | mobile_app | `frontend\mobile_app\app\logistics-partner\profile.tsx` | 2 | 0 | 132 | inline×132, px×43 |
| 5 | 410 | mobile_app | `frontend\mobile_app\app\admin\email.tsx` | 62 | 0 | 110 | inline×110, px×61 |
| 6 | 363 | mobile_app | `frontend\mobile_app\app\logistics-partner\shipments.tsx` | 21 | 2 | 103 | inline×103, off-color×2, px×38 |
| 7 | 341 | mobile_app | `frontend\mobile_app\app\checkout.tsx` | 13 | 0 | 105 | inline×105, px×20 |
| 8 | 323 | web_app | `frontend\web_app\src\components\admin\commandCenter\hud.tsx` | 12 | 8 | 62 | inline×62, style-tag, off-color×8, tw-arb-size×43, px×2 |
| 9 | 288 | mobile_app | `frontend\mobile_app\app\invoice.tsx` | 0 | 0 | 77 | inline×77, px×43 |
| 10 | 288 | mobile_app | `frontend\mobile_app\app\logistics-partner\dashboard.tsx` | 20 | 2 | 83 | inline×83, off-color×2, px×23 |
| 11 | 274 | mobile_app | `frontend\mobile_app\app\(tabs)\products\index.tsx` | 6 | 0 | 68 | inline×68, px×62 |
| 12 | 268 | mobile_app | `frontend\mobile_app\app\logistics-partner\payouts.tsx` | 0 | 0 | 86 | inline×86, px×8 |
| 13 | 244 | mobile_app | `frontend\mobile_app\app\supplier\logistics.tsx` | 10 | 0 | 68 | inline×68, px×30 |
| 14 | 240 | mobile_app | `frontend\mobile_app\app\(tabs)\profile.tsx` | 5 | 0 | 66 | inline×66, px×34 |
| 15 | 236 | mobile_app | `frontend\mobile_app\app\(tabs)\products\[id].tsx` | 4 | 0 | 72 | inline×72, px×16 |
| 16 | 222 | mobile_app | `frontend\mobile_app\app\tracking\[id].tsx` | 2 | 0 | 67 | inline×67, px×21 |
| 17 | 217 | mobile_app | `frontend\mobile_app\app\supplier\payouts.tsx` | 2 | 0 | 69 | inline×69, px×8 |
| 18 | 205 | web_app | `frontend\web_app\src\components\BackgroundEffect.tsx` | 49 | 16 | 33 | inline×33, off-color×16, px×26 |
| 19 | 197 | mobile_app | `frontend\mobile_app\app\logistics-partners\[id].tsx` | 0 | 0 | 50 | inline×50, px×31 |
| 20 | 194 | mobile_app | `frontend\mobile_app\app\barcode-scan.tsx` | 7 | 0 | 54 | inline×54, px×22 |
| 21 | 192 | mobile_app | `frontend\mobile_app\app\admin\analytics.tsx` | 10 | 0 | 54 | inline×54, px×26 |
| 22 | 191 | mobile_app | `frontend\mobile_app\app\supplier\dashboard.tsx` | 7 | 0 | 48 | inline×48, px×33 |
| 23 | 182 | mobile_app | `frontend\mobile_app\app\suppliers\[id].tsx` | 7 | 0 | 53 | inline×53, px×17 |
| 24 | 181 | mobile_app | `frontend\mobile_app\app\supplier\profile.tsx` | 1 | 0 | 58 | inline×58, px×5 |
| 25 | 181 | mobile_app | `frontend\mobile_app\app\(tabs)\cart.tsx` | 7 | 0 | 55 | inline×55, px×10 |
| 26 | 179 | mobile_app | `frontend\mobile_app\app\supplier\products\new.tsx` | 5 | 0 | 51 | inline×51, px×22 |
| 27 | 175 | mobile_app | `frontend\mobile_app\app\logistics-partner\scan.tsx` | 14 | 1 | 51 | inline×51, off-color×1, px×14 |
| 28 | 173 | mobile_app | `frontend\mobile_app\components\MobileSeasonalBanner.tsx` | 40 | 5 | 23 | inline×23, off-color×5, px×62 |
| 29 | 172 | mobile_app | `frontend\mobile_app\app\supplier\register.tsx` | 15 | 0 | 53 | inline×53, px×11 |
| 30 | 171 | mobile_app | `frontend\mobile_app\app\supplier\documents.tsx` | 4 | 0 | 40 | inline×40, px×35 |
| 31 | 170 | mobile_app | `frontend\mobile_app\app\offers.tsx` | 30 | 2 | 50 | inline×50, off-color×2, px×8 |
| 32 | 163 | mobile_app | `frontend\mobile_app\app\supplier\credibility.tsx` | 19 | 1 | 45 | inline×45, off-color×1, px×16 |
| 33 | 158 | mobile_app | `frontend\mobile_app\app\(tabs)\orders\[id].tsx` | 0 | 0 | 48 | inline×48, px×14 |
| 34 | 151 | mobile_app | `frontend\mobile_app\app\flash-sales.tsx` | 27 | 5 | 28 | inline×28, off-color×5, px×25 |
| 35 | 140 | mobile_app | `frontend\mobile_app\app\admin\product-verification.tsx` | 11 | 0 | 43 | inline×43, px×9 |
| 36 | 139 | mobile_app | `frontend\mobile_app\app\supplier\bulk.tsx` | 0 | 0 | 40 | inline×40, px×17 |
| 37 | 138 | mobile_app | `frontend\mobile_app\app\admin\coupons.tsx` | 8 | 0 | 36 | inline×36, px×22 |
| 38 | 137 | mobile_app | `frontend\mobile_app\app\referrals.tsx` | 0 | 0 | 45 | inline×45, px×2 |
| 39 | 135 | mobile_app | `frontend\mobile_app\app\supplier\label.tsx` | 12 | 3 | 27 | inline×27, style-tag, off-color×3, px×9 |
| 40 | 131 | mobile_app | `frontend\mobile_app\components\MobileBackgroundEffect.tsx` | 36 | 9 | 15 | inline×15, off-color×9, px×36 |
| 41 | 129 | mobile_app | `frontend\mobile_app\app\settings.tsx` | 3 | 0 | 41 | inline×41, px×6 |
| 42 | 125 | mobile_app | `frontend\mobile_app\app\admin\flash-sales.tsx` | 11 | 0 | 32 | inline×32, px×21 |
| 43 | 122 | mobile_app | `frontend\mobile_app\app\admin\barcode.tsx` | 19 | 1 | 33 | inline×33, off-color×1, px×11 |
| 44 | 121 | mobile_app | `frontend\mobile_app\app\edit-profile.tsx` | 2 | 0 | 38 | inline×38, px×3 |
| 45 | 119 | mobile_app | `frontend\mobile_app\app\supplier\support.tsx` | 7 | 0 | 39 | inline×39, px×2 |
| 46 | 118 | mobile_app | `frontend\mobile_app\app\(tabs)\_layout.tsx` | 18 | 1 | 34 | inline×34, off-color×1, px×8 |
| 47 | 114 | mobile_app | `frontend\mobile_app\app\ticket-detail.tsx` | 1 | 0 | 37 | inline×37, px×3 |
| 48 | 114 | mobile_app | `frontend\mobile_app\app\admin\logistics-partners.tsx` | 10 | 0 | 34 | inline×34, px×8 |
| 49 | 111 | mobile_app | `frontend\mobile_app\app\admin\products.tsx` | 10 | 0 | 26 | inline×26, px×21 |
| 50 | 108 | mobile_app | `frontend\mobile_app\components\ProductCard.tsx` | 26 | 7 | 26 | inline×26, off-color×7, px×2 |
| 51 | 107 | mobile_app | `frontend\mobile_app\app\supplier\orders.tsx` | 0 | 0 | 35 | inline×35, px×2 |
| 52 | 106 | shared | `frontend\shared\src\components\ui\ErrorBoundary.tsx` | 17 | 10 | 11 | inline×11, off-color×10, px×21 |
| 53 | 106 | mobile_app | `frontend\mobile_app\app\tickets.tsx` | 6 | 0 | 34 | inline×34, px×4 |
| 54 | 106 | mobile_app | `frontend\mobile_app\app\admin\banners.tsx` | 6 | 0 | 32 | inline×32, px×8 |
| 55 | 106 | web_app | `frontend\web_app\src\styles\comm.css` | 8 | 3 | 0 | off-color×3, !important×2, px×63 |
| 56 | 105 | mobile_app | `frontend\mobile_app\app\supplier\invoices.tsx` | 6 | 0 | 33 | inline×33, px×4 |
| 57 | 105 | mobile_app | `frontend\mobile_app\app\returns\[id].tsx` | 0 | 0 | 25 | inline×25, px×22 |
| 58 | 101 | mobile_app | `frontend\mobile_app\app\supplier\reports.tsx` | 7 | 0 | 33 | inline×33, px×2 |
| 59 | 100 | web_app | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | 16 | 16 | 9 | inline×9, off-color×16, tw-arb-size×9 |
| 60 | 99 | mobile_app | `frontend\mobile_app\app\help.tsx` | 1 | 0 | 31 | inline×31, px×4 |

## Color Inventory (most used first)

| Color | Hex | Usage | Files | Palette status |
|---|---|---:|---:|---|
| ![#ffffff](https://via.placeholder.com/14/ffffff/ffffff) | `#ffffff` | 560 | 96 | ✅ token |
| ![#000000](https://via.placeholder.com/14/000000/000000) | `#000000` | 254 | 58 | ✅ token |
| ![#ef4444](https://via.placeholder.com/14/ef4444/ef4444) | `#ef4444` | 108 | 39 | ✅ token |
| ![#22c55e](https://via.placeholder.com/14/22c55e/22c55e) | `#22c55e` | 81 | 33 | ✅ token |
| ![#f59e0b](https://via.placeholder.com/14/f59e0b/f59e0b) | `#f59e0b` | 65 | 32 | ✅ token |
| ![#0f172a](https://via.placeholder.com/14/0f172a/0f172a) | `#0f172a` | 52 | 10 | ✅ token |
| ![#3b82f6](https://via.placeholder.com/14/3b82f6/3b82f6) | `#3b82f6` | 47 | 23 | ✅ token |
| ![#32cd32](https://via.placeholder.com/14/32cd32/32cd32) | `#32cd32` | 35 | 13 | ✅ token |
| ![#d4af37](https://via.placeholder.com/14/d4af37/d4af37) | `#d4af37` | 31 | 6 | ✅ token |
| ![#6b7280](https://via.placeholder.com/14/6b7280/6b7280) | `#6b7280` | 30 | 15 | ✅ token |
| ![#4a5d35](https://via.placeholder.com/14/4a5d35/4a5d35) | `#4a5d35` | 28 | 2 | ✅ token |
| ![#2fb43d](https://via.placeholder.com/14/2fb43d/2fb43d) | `#2fb43d` | 24 | 2 | 🔴 OFF-PALETTE |
| ![#9ca3af](https://via.placeholder.com/14/9ca3af/9ca3af) | `#9ca3af` | 23 | 14 | ✅ token |
| ![#94a3b8](https://via.placeholder.com/14/94a3b8/94a3b8) | `#94a3b8` | 20 | 9 | ✅ token |
| ![#facc15](https://via.placeholder.com/14/facc15/facc15) | `#facc15` | 20 | 7 | 🔴 OFF-PALETTE |
| ![#ffd700](https://via.placeholder.com/14/ffd700/ffd700) | `#ffd700` | 19 | 7 | ✅ token |
| ![#f2c94c](https://via.placeholder.com/14/f2c94c/f2c94c) | `#f2c94c` | 19 | 1 | ✅ token |
| ![#8b5cf6](https://via.placeholder.com/14/8b5cf6/8b5cf6) | `#8b5cf6` | 17 | 9 | 🔴 OFF-PALETTE |
| ![#111111](https://via.placeholder.com/14/111111/111111) | `#111111` | 16 | 9 | ✅ token |
| ![#d97706](https://via.placeholder.com/14/d97706/d97706) | `#d97706` | 16 | 6 | ✅ token |
| ![#2563eb](https://via.placeholder.com/14/2563eb/2563eb) | `#2563eb` | 15 | 8 | ✅ token |
| ![#ea580c](https://via.placeholder.com/14/ea580c/ea580c) | `#ea580c` | 14 | 7 | ✅ token |
| ![#38bdf8](https://via.placeholder.com/14/38bdf8/38bdf8) | `#38bdf8` | 14 | 7 | ✅ token |
| ![#fde68a](https://via.placeholder.com/14/fde68a/fde68a) | `#fde68a` | 13 | 1 | 🔴 OFF-PALETTE |
| ![#0ea5e9](https://via.placeholder.com/14/0ea5e9/0ea5e9) | `#0ea5e9` | 12 | 5 | ✅ token |
| ![#7cfc00](https://via.placeholder.com/14/7cfc00/7cfc00) | `#7cfc00` | 12 | 6 | ✅ token |
| ![#f8fafc](https://via.placeholder.com/14/f8fafc/f8fafc) | `#f8fafc` | 12 | 7 | ✅ token |
| ![#ec4899](https://via.placeholder.com/14/ec4899/ec4899) | `#ec4899` | 11 | 6 | ✅ token |
| ![#d1d5db](https://via.placeholder.com/14/d1d5db/d1d5db) | `#d1d5db` | 11 | 6 | ✅ token |
| ![#a855f7](https://via.placeholder.com/14/a855f7/a855f7) | `#a855f7` | 10 | 6 | ✅ token |
| ![#1f2937](https://via.placeholder.com/14/1f2937/1f2937) | `#1f2937` | 9 | 7 | 🔴 OFF-PALETTE |
| ![#1a5204](https://via.placeholder.com/14/1a5204/1a5204) | `#1a5204` | 8 | 8 | ✅ token |
| ![#eeff99](https://via.placeholder.com/14/eeff99/eeff99) | `#eeff99` | 8 | 8 | ✅ token |
| ![#f472b6](https://via.placeholder.com/14/f472b6/f472b6) | `#f472b6` | 8 | 5 | ✅ token |
| ![#a78bfa](https://via.placeholder.com/14/a78bfa/a78bfa) | `#a78bfa` | 8 | 5 | 🔴 OFF-PALETTE |
| ![#fbbf24](https://via.placeholder.com/14/fbbf24/fbbf24) | `#fbbf24` | 8 | 5 | ✅ token |
| ![#a3b3c8](https://via.placeholder.com/14/a3b3c8/a3b3c8) | `#a3b3c8` | 8 | 2 | 🔴 OFF-PALETTE |
| ![#ccee38](https://via.placeholder.com/14/ccee38/ccee38) | `#ccee38` | 7 | 7 | ✅ token |
| ![#97d01a](https://via.placeholder.com/14/97d01a/97d01a) | `#97d01a` | 7 | 7 | ✅ token |
| ![#55b010](https://via.placeholder.com/14/55b010/55b010) | `#55b010` | 7 | 7 | ✅ token |

## Color Theme Drift Clusters

These colors are visually near-identical but written differently — 
the classic symptom of theme drift.

- `#0f172a` ×52 ≈ `#111827` ×4
- `#f8faf5` ×1 ≈ `#f8fafc` ×12 ≈ `#f8fbf4` ×3 ≈ `#f8fcf3` ×1 ≈ `#f8fcf4` ×1 ≈ `#f9fbf5` ×2 ≈ `#fafcf6` ×1 ≈ `#fbfcf8` ×5 ≈ `#fff7f7` ×2
- `#ffd400` ×3 ≈ `#ffd600` ×1 ≈ `#ffd700` ×19
- `#cbd5e1` ×2 ≈ `#d1d5db` ×11
- `#1e293b` ×3 ≈ `#1f2937` ×9
- `#1a1a1a` ×6 ≈ `#1c1917` ×5
- `#ffd440` ×4 ≈ `#ffd740` ×7
- `#f1f5f9` ×3 ≈ `#f3f4f6` ×2 ≈ `#f5f5f5` ×4
- `#2a7006` ×7 ≈ `#2d6a04` ×1
- `#e5e5e5` ×1 ≈ `#e5e7eb` ×7
- `#060e1c` ×3 ≈ `#080d18` ×3 ≈ `#080d1a` ×1
- `#ca8a04` ×2 ≈ `#d08c00` ×5
- `#eeeeee` ×5 ≈ `#efefef` ×1 ≈ `#f0f0f0` ×1
- `#f8c400` ×6 ≈ `#ffc400` ×1
- `#f0fdf0` ×1 ≈ `#f0fdf4` ×1 ≈ `#f3f8ee` ×1 ≈ `#f4f8ee` ×1 ≈ `#f5f9ef` ×1 ≈ `#f5faf0` ×1
- `#f3f6ee` ×1 ≈ `#f5f7ef` ×1 ≈ `#f7faf3` ×3
- `#10233e` ×2 ≈ `#102643` ×1 ≈ `#16213e` ×1
- `#334155` ×3 ≈ `#374151` ×1
- `#475569` ×2 ≈ `#4b5563` ×2
- `#fef3c7` ×2 ≈ `#fef9c3` ×1 ≈ `#fff7bf` ×1

## Design Damage Hotlist

| Sev | Rule | Domain | Location | Problem | Intended |
|---|---|---|---|---|---|
| 🔴 | DS02 | web_app | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | 3 <style> tag(s) inside a component file | delete; styles belong in the design system (Tailwind/global CSS), not in JSX |
| 🔴 | DS02 | web_app | `frontend\web_app\src\components\TickerBar.tsx` | 1 <style> tag(s) inside a component file | delete; styles belong in the design system (Tailwind/global CSS), not in JSX |
| 🔴 | DS02 | web_app | `frontend\web_app\src\components\supplier\PhotoEditorModal.tsx` | 1 <style> tag(s) inside a component file | delete; styles belong in the design system (Tailwind/global CSS), not in JSX |
| 🔴 | DS02 | web_app | `frontend\web_app\src\components\supplier\ProductImageCanvas.tsx` | 1 <style> tag(s) inside a component file | delete; styles belong in the design system (Tailwind/global CSS), not in JSX |
| 🔴 | DS02 | web_app | `frontend\web_app\src\components\admin\commandCenter\hud.tsx` | 2 <style> tag(s) inside a component file | delete; styles belong in the design system (Tailwind/global CSS), not in JSX |
| 🔴 | DS02 | web_app | `frontend\web_app\src\app\supplier\labels\[id]\page.tsx` | 1 <style> tag(s) inside a component file | delete; styles belong in the design system (Tailwind/global CSS), not in JSX |
| 🔴 | DS02 | mobile_app | `frontend\mobile_app\lib\invoiceService.ts` | 1 <style> tag(s) inside a component file | delete; styles belong in the design system (Tailwind/global CSS), not in JSX |
| 🔴 | DS02 | mobile_app | `frontend\mobile_app\app\supplier\label.tsx` | 1 <style> tag(s) inside a component file | delete; styles belong in the design system (Tailwind/global CSS), not in JSX |
| 🔴 | DS06 | web_app | `frontend\web_app\src\styles\globals.css` | !important used 38× — specificity war | fix selector specificity or component structure; never !important in a design system |
| 🔴 | DS06 | web_app | `frontend\web_app\src\styles\comm.css` | !important used 2× — specificity war | fix selector specificity or component structure; never !important in a design system |
| 🔴 | DS06 | web_app | `frontend\web_app\src\styles\panel-modern.css` | !important used 2× — specificity war | fix selector specificity or component structure; never !important in a design system |
| 🔴 | DS10 | web_app | `frontend\web_app\src\app\layout.tsx` | magic z-index value(s): 10000 | use a z-index scale token (dropdown=100, modal=200, toast=300); never 9999+ |
| 🔴 | DS10 | web_app | `frontend\web_app\src\styles\globals.css` | magic z-index value(s): 10000 | use a z-index scale token (dropdown=100, modal=200, toast=300); never 9999+ |
| 🔴 | DS10 | web_app | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | magic z-index value(s): 1000, 1001 | use a z-index scale token (dropdown=100, modal=200, toast=300); never 9999+ |
| 🟡 | DS03 | design | `frontend\web_app\src\components\Footer.tsx` | off-palette color #2fb43d used 24× in 2 file(s): frontend\web_app\src\components\Footer.tsx, frontend\web_app\src\styles\globals.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\app\write-review.tsx` | off-palette color #facc15 used 20× in 7 file(s): frontend\mobile_app\app\write-review.tsx, frontend\mobile_app\components\MobileBackgroundEffect.tsx, frontend\mobile_app\components\ProductCard.tsx, frontend\mobile_app\components\QuickViewModal.tsx +3 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\app\admin\barcode.tsx` | off-palette color #8b5cf6 used 17× in 9 file(s): frontend\mobile_app\app\admin\barcode.tsx, frontend\mobile_app\app\admin\users.tsx, frontend\mobile_app\app\logistics-partner\analytics.tsx, frontend\mobile_app\app\logistics-partner\dashboard.tsx +5 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #fde68a used 13× in 1 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\components\MobileSeasonalBanner.tsx` | off-palette color #1f2937 used 9× in 7 file(s): frontend\mobile_app\components\MobileSeasonalBanner.tsx, frontend\mobile_app\components\ui\SearchBar.tsx, frontend\shared\src\components\ui\QuickFilters.native.tsx, frontend\shared\src\components\ui\SearchBar.native.tsx +3 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\ui\SupplierBadge.native.tsx` | off-palette color #a3b3c8 used 8× in 2 file(s): frontend\shared\src\components\ui\SupplierBadge.native.tsx, frontend\shared\src\components\ui\SupplierBadge.web.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\components\MobileBackgroundEffect.tsx` | off-palette color #a78bfa used 8× in 5 file(s): frontend\mobile_app\components\MobileBackgroundEffect.tsx, frontend\web_app\src\components\BackgroundEffect.tsx, frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx +1 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\components\ui\Footer.tsx` | off-palette color #6ae022 used 7× in 4 file(s): frontend\mobile_app\components\ui\Footer.tsx, frontend\mobile_app\components\ui\HeaderBar.tsx, frontend\mobile_app\components\ui\ScreenHeader.tsx, frontend\web_app\src\styles\comm.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\ui\ErrorBoundary.tsx` | off-palette color #7f1d1d used 6× in 3 file(s): frontend\shared\src\components\ui\ErrorBoundary.tsx, frontend\web_app\src\app\supplier\bulk\draftUtils.ts, frontend\web_app\src\components\BannerCanvasEditor.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\lib\invoiceService.ts` | off-palette color #cccccc used 6× in 4 file(s): frontend\mobile_app\lib\invoiceService.ts, frontend\web_app\src\app\supplier\bulk\components\ColorPickerField.tsx, frontend\web_app\src\app\supplier\products\add\page.tsx, frontend\web_app\src\components\supplier\ProductImageCanvas.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\mobile_app\app\flash-sales.tsx` | off-palette color #dc2626 used 6× in 3 file(s): frontend\mobile_app\app\flash-sales.tsx, frontend\mobile_app\components\MobileSeasonalBanner.tsx, frontend\shared\src\components\ui\ErrorBoundary.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #22d3ee used 5× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\logo\Logo.native.tsx` | off-palette color #a86000 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\logo\Logo.native.tsx` | off-palette color #d08c00 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\logo\Logo.native.tsx` | off-palette color #f0c800 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\logo\Logo.native.tsx` | off-palette color #fff550 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | off-palette color #00c800 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #1e1b4b used 4× in 1 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\logo\LogoAnimation.tsx` | off-palette color #233a61 used 4× in 2 file(s): frontend\shared\src\components\logo\LogoAnimation.tsx, frontend\shared\src\logo\LogoAnimation.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | off-palette color #2828ff used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BackgroundEffect.tsx` | off-palette color #2dd4bf used 4× in 3 file(s): frontend\web_app\src\components\BackgroundEffect.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx, frontend\web_app\src\styles\globals.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\styles\globals.css` | off-palette color #325a24 used 4× in 2 file(s): frontend\web_app\src\styles\globals.css, frontend\web_app\src\styles\panel-modern.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\shared\src\components\logo\LogoAnimation.tsx` | off-palette color #3d8018 used 4× in 2 file(s): frontend\shared\src\components\logo\LogoAnimation.tsx, frontend\shared\src\logo\LogoAnimation.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #60a5fa used 4× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | off-palette color #ff2828 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | off-palette color #ffdc28 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\app\logo-animation\LogoAnimationClient.tsx` | off-palette color #060e1c used 3× in 2 file(s): frontend\web_app\src\app\logo-animation\LogoAnimationClient.tsx, frontend\web_app\src\styles\globals.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #064e3b used 3× in 1 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\styles\globals.css` | off-palette color #080d18 used 3× in 1 file(s): frontend\web_app\src\styles\globals.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS03 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | off-palette color #1e293b used 3× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\styles\globals.css | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS04 | design | `frontend\web_app\src\styles\globals.css` | color drift (5× total): #f3f6ee (×1) ≈ #f5f7ef (×1) ≈ #f7faf3 (×3) | pick ONE token; these are visually the same color |
| 🟡 | DS04 | design | `frontend\web_app\src\styles\globals.css` | color drift (4× total): #fef3c7 (×2) ≈ #fef9c3 (×1) ≈ #fff7bf (×1) | pick ONE token; these are visually the same color |
| 🟡 | DS04 | design | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | color drift (3× total): #fffbeb (×2) ≈ #fffff0 (×1) | pick ONE token; these are visually the same color |
| 🟡 | DS05 | web_app | `frontend\web_app\src\app\logistics-partners\page.tsx` | 2 arbitrary Tailwind color value(s) bypass tokens: radial-gradient(circle_at_top,_rgba(14,165,233,0.10),_transparent_40%),linear-gradient(180deg,_var(--color-surface-0),_var(--color-surface-1)), radial-gradient(circle_at_top_right,_rgba(14,165,233,0.20),_transparent_45%) | use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...] |
| 🟡 | DS05 | web_app | `frontend\web_app\src\components\Footer.tsx` | 1 arbitrary Tailwind color value(s) bypass tokens: radial-gradient(circle_at_top_left,rgba(47,180,61,0.1),transparent_32%),radial-gradient(circle_at_top_right,rgba(250,204,21,0.08),transparent_30%) | use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...] |
| 🟡 | DS05 | web_app | `frontend\web_app\src\app\tracking\[id]\page.tsx` | 1 arbitrary Tailwind color value(s) bypass tokens: radial-gradient(circle_at_top,rgba(14,165,233,0.18),transparent_55%) | use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...] |
| 🟡 | DS05 | web_app | `frontend\web_app\src\app\supplier\labels\[id]\page.tsx` | 1 arbitrary Tailwind color value(s) bypass tokens: linear-gradient(135deg,color-mix(in_srgb,var(--color-surface-2)_84%,transparent)_0%,color-mix(in_srgb,var(--color-surface-0)_92%,transparent)_45%,color-mix(in_srgb,var(--color-brand)_14%,transparent)_100%) | use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...] |
| 🟡 | DS05 | web_app | `frontend\web_app\src\app\logo-animation\LogoAnimationClient.tsx` | 1 arbitrary Tailwind color value(s) bypass tokens: #060e1c | use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...] |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\mobile_app\components\ui\SearchBar.tsx, frontend\mobile_app\theme\index.ts, frontend\shared\src\components\ui\Q` | color drift (56× total): #0f172a (×52) ≈ #111827 (×4) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\web_app\src\styles\globals.css` | color drift (28× total): #f8faf5 (×1) ≈ #f8fafc (×12) ≈ #f8fbf4 (×3) ≈ #f8fcf3 (×1) ≈ #f8fcf4 (×1) ≈ #f9fbf5 (×2) ≈ #fafcf6 (×1) ≈ #fbfcf8 (×5) ≈ #fff7f7 (×2) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | color drift (23× total): #ffd400 (×3) ≈ #ffd600 (×1) ≈ #ffd700 (×19) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\web_app\src\styles\globals.css` | color drift (13× total): #cbd5e1 (×2) ≈ #d1d5db (×11) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\styles\globals.css` | color drift (12× total): #1e293b (×3) ≈ #1f2937 (×9) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\shared\src\theme.native.ts, frontend\web_app\src\app\supplier\bulk\draftUtils.ts, frontend\web_app\src\styles\g` | color drift (11× total): #1a1a1a (×6) ≈ #1c1917 (×5) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\shared\src\components\logo\LogoAnimation.tsx, frontend\shared\src\logo\LogoAnimation.tsx` | color drift (11× total): #ffd440 (×4) ≈ #ffd740 (×7) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\styles\globals.css` | color drift (9× total): #f1f5f9 (×3) ≈ #f3f4f6 (×2) ≈ #f5f5f5 (×4) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\s` | color drift (8× total): #2a7006 (×7) ≈ #2d6a04 (×1) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\shared\src\theme.native.ts` | color drift (8× total): #e5e5e5 (×1) ≈ #e5e7eb (×7) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/web_app | `frontend\web_app\src\app\logo-animation\LogoAnimationClient.tsx, frontend\web_app\src\styles\globals.css` | color drift (7× total): #060e1c (×3) ≈ #080d18 (×3) ≈ #080d1a (×1) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared/web_app | `frontend\mobile_app\components\ProductCard.tsx` | color drift (7× total): #ca8a04 (×2) ≈ #d08c00 (×5) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared | `frontend\mobile_app\app\supplier\label.tsx, frontend\mobile_app\lib\invoiceService.ts` | color drift (7× total): #eeeeee (×5) ≈ #efefef (×1) ≈ #f0f0f0 (×1) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\s` | color drift (7× total): #f8c400 (×6) ≈ #ffc400 (×1) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\web_app\src\styles\globals.css` | color drift (6× total): #f0fdf0 (×1) ≈ #f0fdf4 (×1) ≈ #f3f8ee (×1) ≈ #f4f8ee (×1) ≈ #f5f9ef (×1) ≈ #f5faf0 (×1) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | mobile_app/shared | `frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\logo\Logo.native.tsx` | color drift (4× total): #10233e (×2) ≈ #102643 (×1) ≈ #16213e (×1) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\shared\src\components\ui\ThemeToggle.native.tsx, frontend\web_app\src\styles\globals.css` | color drift (4× total): #334155 (×3) ≈ #374151 (×1) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\web_app\src\styles\globals.css` | color drift (4× total): #475569 (×2) ≈ #4b5563 (×2) | web and mobile disagree on this color — unify in shared tokens |

## Domain: design

- 🟢 **DSI2** `frontend` — token coverage: 83.3% of color occurrences match the palette (1844/2214, 279 distinct colors)
- 🟡 **DS03** `frontend\web_app\src\components\Footer.tsx` — off-palette color #2fb43d used 24× in 2 file(s): frontend\web_app\src\components\Footer.tsx, frontend\web_app\src\styles\globals.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\app\write-review.tsx` — off-palette color #facc15 used 20× in 7 file(s): frontend\mobile_app\app\write-review.tsx, frontend\mobile_app\components\MobileBackgroundEffect.tsx, frontend\mobile_app\components\ProductCard.tsx, frontend\mobile_app\components\QuickViewModal.tsx +3 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\app\admin\barcode.tsx` — off-palette color #8b5cf6 used 17× in 9 file(s): frontend\mobile_app\app\admin\barcode.tsx, frontend\mobile_app\app\admin\users.tsx, frontend\mobile_app\app\logistics-partner\analytics.tsx, frontend\mobile_app\app\logistics-partner\dashboard.tsx +5 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #fde68a used 13× in 1 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\components\MobileSeasonalBanner.tsx` — off-palette color #1f2937 used 9× in 7 file(s): frontend\mobile_app\components\MobileSeasonalBanner.tsx, frontend\mobile_app\components\ui\SearchBar.tsx, frontend\shared\src\components\ui\QuickFilters.native.tsx, frontend\shared\src\components\ui\SearchBar.native.tsx +3 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\ui\SupplierBadge.native.tsx` — off-palette color #a3b3c8 used 8× in 2 file(s): frontend\shared\src\components\ui\SupplierBadge.native.tsx, frontend\shared\src\components\ui\SupplierBadge.web.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\components\MobileBackgroundEffect.tsx` — off-palette color #a78bfa used 8× in 5 file(s): frontend\mobile_app\components\MobileBackgroundEffect.tsx, frontend\web_app\src\components\BackgroundEffect.tsx, frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx +1 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\components\ui\Footer.tsx` — off-palette color #6ae022 used 7× in 4 file(s): frontend\mobile_app\components\ui\Footer.tsx, frontend\mobile_app\components\ui\HeaderBar.tsx, frontend\mobile_app\components\ui\ScreenHeader.tsx, frontend\web_app\src\styles\comm.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\ui\ErrorBoundary.tsx` — off-palette color #7f1d1d used 6× in 3 file(s): frontend\shared\src\components\ui\ErrorBoundary.tsx, frontend\web_app\src\app\supplier\bulk\draftUtils.ts, frontend\web_app\src\components\BannerCanvasEditor.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\lib\invoiceService.ts` — off-palette color #cccccc used 6× in 4 file(s): frontend\mobile_app\lib\invoiceService.ts, frontend\web_app\src\app\supplier\bulk\components\ColorPickerField.tsx, frontend\web_app\src\app\supplier\products\add\page.tsx, frontend\web_app\src\components\supplier\ProductImageCanvas.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\mobile_app\app\flash-sales.tsx` — off-palette color #dc2626 used 6× in 3 file(s): frontend\mobile_app\app\flash-sales.tsx, frontend\mobile_app\components\MobileSeasonalBanner.tsx, frontend\shared\src\components\ui\ErrorBoundary.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #22d3ee used 5× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\logo\Logo.native.tsx` — off-palette color #a86000 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\logo\Logo.native.tsx` — off-palette color #d08c00 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\logo\Logo.native.tsx` — off-palette color #f0c800 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\logo\Logo.native.tsx` — off-palette color #fff550 used 5× in 5 file(s): frontend\shared\src\components\logo\Logo.native.tsx, frontend\shared\src\components\logo\ZoziLogo.tsx, frontend\shared\src\logo\Logo.native.tsx, frontend\shared\src\logo\ZoziLogo.tsx +1 more → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` — off-palette color #00c800 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #1e1b4b used 4× in 1 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\logo\LogoAnimation.tsx` — off-palette color #233a61 used 4× in 2 file(s): frontend\shared\src\components\logo\LogoAnimation.tsx, frontend\shared\src\logo\LogoAnimation.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` — off-palette color #2828ff used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BackgroundEffect.tsx` — off-palette color #2dd4bf used 4× in 3 file(s): frontend\web_app\src\components\BackgroundEffect.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx, frontend\web_app\src\styles\globals.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\styles\globals.css` — off-palette color #325a24 used 4× in 2 file(s): frontend\web_app\src\styles\globals.css, frontend\web_app\src\styles\panel-modern.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\shared\src\components\logo\LogoAnimation.tsx` — off-palette color #3d8018 used 4× in 2 file(s): frontend\shared\src\components\logo\LogoAnimation.tsx, frontend\shared\src\logo\LogoAnimation.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #60a5fa used 4× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\components\admin\commandCenter\hud.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` — off-palette color #ff2828 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` — off-palette color #ffdc28 used 4× in 1 file(s): frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\app\logo-animation\LogoAnimationClient.tsx` — off-palette color #060e1c used 3× in 2 file(s): frontend\web_app\src\app\logo-animation\LogoAnimationClient.tsx, frontend\web_app\src\styles\globals.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #064e3b used 3× in 1 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\styles\globals.css` — off-palette color #080d18 used 3× in 1 file(s): frontend\web_app\src\styles\globals.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS03** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — off-palette color #1e293b used 3× in 2 file(s): frontend\web_app\src\components\BannerCanvasEditor.tsx, frontend\web_app\src\styles\globals.css → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS04** `frontend\web_app\src\styles\globals.css` — color drift (5× total): #f3f6ee (×1) ≈ #f5f7ef (×1) ≈ #f7faf3 (×3) → *pick ONE token; these are visually the same color*
- 🟡 **DS04** `frontend\web_app\src\styles\globals.css` — color drift (4× total): #fef3c7 (×2) ≈ #fef9c3 (×1) ≈ #fff7bf (×1) → *pick ONE token; these are visually the same color*
- 🟡 **DS04** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — color drift (3× total): #fffbeb (×2) ≈ #fffff0 (×1) → *pick ONE token; these are visually the same color*
- 🟡 **DS07** `frontend` — 57 distinct hardcoded font sizes: 0.75rem, 0.7rem, 0.875rem, 1.05rem, 1.125rem, 1.15rem, 1.25rem, 1.35rem, 1.5rem, 1.6rem, 1.7rem, 1.875rem ... → *collapse onto a type scale (text-xs/sm/base/lg/xl...); max ~8 steps*
- 🟡 **DS07** `frontend\shared\src\components\logo\Logo.web.tsx` — font family literal 'var(--font-nunito, 'Nunito', var(--font-body, 'Sora', system-ui, sans-serif))' hardcoded in 5 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\shared\src\components\logo\LogoAnimation.tsx` — font family literal 'var(--font-body, 'Sora', system-ui, sans-serif)' hardcoded in 2 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\src\app\brand\page.tsx` — font family literal 'Sora', 'Montserrat', system-ui, sans-serif' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\shared\src\components\ui\ErrorBoundary.tsx` — font family literal 'system-ui, sans-serif' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\src\styles\comm.css` — font family literal 'var(--font-display, ui-sans-serif)' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\src\styles\globals.css` — font family literal 'var(--font-arabic), "Arabic UI", "Noto Naskh Arabic", "Noto Sans Arabic", "Segoe UI", Tahoma,
               "Arial Unicode MS", sans-serif' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\src\styles\globals.css` — font family literal 'var(--font-body), Sora, sans-serif' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\src\styles\globals.css` — font family literal '"Arabic UI"' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS09** `frontend` — 56 distinct border-radius values: 0, 0 0 4px 4px, 0.25rem, 0.5rem, 0.75rem, 0px, 1, 1.25rem, 1.2rem, 1.4rem → *standardize on 3-4 radii tokens (sm/md/lg/full)*
- 🟡 **DS11** `frontend` — 95 distinct shadow definitions — no elevation system → *define 3 elevation tokens (shadow-sm/md/lg) and reuse them*
- 🟡 **DS16** `frontend` — 9 distinct animation durations: 0ms, 1000ms, 120ms, 150ms, 180ms, 200ms, 300ms, 500ms, 700ms → *standardize on 2-3 motion tokens (150ms/250ms/400ms)*
- 🟢 **DSI1** `frontend` — top colors in use: #ffffff×560, #000000×254, #ef4444×108, #22c55e×81, #f59e0b×65, #0f172a×52, #3b82f6×47, #32cd32×35, #d4af37×31, #6b7280×30

## Domain: web_app

- 🟡 **DS01** `frontend\web_app\src\components\admin\commandCenter\hud.tsx` — 62 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\BackgroundEffect.tsx` — 33 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — 33 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🔴 **DS02** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — 3 <style> tag(s) inside a component file → *delete; styles belong in the design system (Tailwind/global CSS), not in JSX*
- 🔴 **DS02** `frontend\web_app\src\components\TickerBar.tsx` — 1 <style> tag(s) inside a component file → *delete; styles belong in the design system (Tailwind/global CSS), not in JSX*
- 🔴 **DS02** `frontend\web_app\src\components\supplier\PhotoEditorModal.tsx` — 1 <style> tag(s) inside a component file → *delete; styles belong in the design system (Tailwind/global CSS), not in JSX*
- 🔴 **DS02** `frontend\web_app\src\components\supplier\ProductImageCanvas.tsx` — 1 <style> tag(s) inside a component file → *delete; styles belong in the design system (Tailwind/global CSS), not in JSX*
- 🔴 **DS02** `frontend\web_app\src\components\admin\commandCenter\hud.tsx` — 2 <style> tag(s) inside a component file → *delete; styles belong in the design system (Tailwind/global CSS), not in JSX*
- 🔴 **DS02** `frontend\web_app\src\app\supplier\labels\[id]\page.tsx` — 1 <style> tag(s) inside a component file → *delete; styles belong in the design system (Tailwind/global CSS), not in JSX*
- 🟡 **DS05** `frontend\web_app\src\app\logistics-partners\page.tsx` — 2 arbitrary Tailwind color value(s) bypass tokens: radial-gradient(circle_at_top,_rgba(14,165,233,0.10),_transparent_40%),linear-gradient(180deg,_var(--color-surface-0),_var(--color-surface-1)), radial-gradient(circle_at_top_right,_rgba(14,165,233,0.20),_transparent_45%) → *use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...]*
- 🟡 **DS05** `frontend\web_app\src\components\Footer.tsx` — 1 arbitrary Tailwind color value(s) bypass tokens: radial-gradient(circle_at_top_left,rgba(47,180,61,0.1),transparent_32%),radial-gradient(circle_at_top_right,rgba(250,204,21,0.08),transparent_30%) → *use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...]*
- 🟡 **DS05** `frontend\web_app\src\app\tracking\[id]\page.tsx` — 1 arbitrary Tailwind color value(s) bypass tokens: radial-gradient(circle_at_top,rgba(14,165,233,0.18),transparent_55%) → *use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...]*
- 🟡 **DS05** `frontend\web_app\src\app\supplier\labels\[id]\page.tsx` — 1 arbitrary Tailwind color value(s) bypass tokens: linear-gradient(135deg,color-mix(in_srgb,var(--color-surface-2)_84%,transparent)_0%,color-mix(in_srgb,var(--color-surface-0)_92%,transparent)_45%,color-mix(in_srgb,var(--color-brand)_14%,transparent)_100%) → *use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...]*
- 🟡 **DS05** `frontend\web_app\src\app\logo-animation\LogoAnimationClient.tsx` — 1 arbitrary Tailwind color value(s) bypass tokens: #060e1c → *use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...]*
- 🔴 **DS06** `frontend\web_app\src\styles\globals.css` — !important used 38× — specificity war → *fix selector specificity or component structure; never !important in a design system*
- 🔴 **DS06** `frontend\web_app\src\styles\comm.css` — !important used 2× — specificity war → *fix selector specificity or component structure; never !important in a design system*
- 🔴 **DS06** `frontend\web_app\src\styles\panel-modern.css` — !important used 2× — specificity war → *fix selector specificity or component structure; never !important in a design system*
- 🟡 **DS08** `frontend\web_app\src\styles\globals.css` — 899 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\styles\comm.css` — 63 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\styles\panel-modern.css` — 34 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\components\BackgroundEffect.tsx` — 26 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🔴 **DS10** `frontend\web_app\src\app\layout.tsx` — magic z-index value(s): 10000 → *use a z-index scale token (dropdown=100, modal=200, toast=300); never 9999+*
- 🔴 **DS10** `frontend\web_app\src\styles\globals.css` — magic z-index value(s): 10000 → *use a z-index scale token (dropdown=100, modal=200, toast=300); never 9999+*
- 🔴 **DS10** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — magic z-index value(s): 1000, 1001 → *use a z-index scale token (dropdown=100, modal=200, toast=300); never 9999+*

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
- 🔴 **DS02** `frontend\mobile_app\lib\invoiceService.ts` — 1 <style> tag(s) inside a component file → *delete; styles belong in the design system (Tailwind/global CSS), not in JSX*
- 🔴 **DS02** `frontend\mobile_app\app\supplier\label.tsx` — 1 <style> tag(s) inside a component file → *delete; styles belong in the design system (Tailwind/global CSS), not in JSX*
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
- 🟡 **DS08** `frontend\mobile_app\app\admin\products.tsx` — 21 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\mobile_app\app\checkout.tsx` — 20 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*

## Domain: shared

- 🟡 **DS08** `frontend\shared\src\components\ui\ErrorBoundary.tsx` — 21 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
