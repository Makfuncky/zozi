# ZOZI Design System Governance Audit Report (GENERATED — do not hand-edit)

**Repo:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi`  
**Result:** 🔴 0 · 🟡 46 · 🟢 2  
**Design Debt Score:** `945`  
**Token Coverage:** `99.6%` (192 distinct colors / 222 tokens / 623 files)  
**Ephemeral. Add to `.gitignore`.**

## Scorecard

| Code | Count | Sev | Meaning |
|---|---:|---|---|
| DS01 | 25 | 🟡 ADVISORY | hardcoded CSS: inline style={{...}} object in component |
| DS03 | 1 | 🟡 ADVISORY | raw/off-palette color literal (bypasses design tokens) |
| DS07 | 8 | 🟡 ADVISORY | hardcoded typography (font size / family literal) |
| DS08 | 7 | 🟡 ADVISORY | hardcoded spacing/dimension (raw px) |
| DS09 | 1 | 🟡 ADVISORY | inconsistent border-radius values |
| DS11 | 1 | 🟡 ADVISORY | inconsistent box-shadow values |
| DS13 | 2 | 🟡 ADVISORY | cross-workspace palette mismatch (web vs mobile differ) |
| DS16 | 1 | 🟡 ADVISORY | inconsistent motion durations (transition/animation) |
| DSI1 | 1 | 🟢 INFO | palette / token inventory |
| DSI2 | 1 | 🟢 INFO | token coverage |

## File-by-File Design Debt

| # | Score | Workspace | File | Colors | Off-palette | Inline styles | Issues |
|---:|---:|---|---|---:|---:|---:|---|
| 1 | 241 | web_app | `frontend\web_app\src\components\admin\commandCenter\hud.tsx` | 3 | 0 | 62 | inline×62, tw-arb-size×43, px×2 |
| 2 | 156 | web_app | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | 43 | 0 | 33 | inline×33, tw-arb-size×45, z-magic, px×10 |
| 3 | 141 | web_app | `frontend\web_app\src\components\BackgroundEffect.tsx` | 36 | 0 | 33 | inline×33, px×26 |
| 4 | 110 | web_app | `frontend\web_app\src\styles\globals.css` | 16 | 0 | 0 | px×164 |
| 5 | 98 | web_app | `frontend\web_app\src\app\admin\treasury\_components\treasury-content.tsx` | 0 | 0 | 3 | inline×3, tw-arb-size×89 |
| 6 | 78 | web_app | `frontend\web_app\src\styles\comm.css` | 8 | 0 | 0 | px×63 |
| 7 | 69 | web_app | `frontend\web_app\src\app\admin\command-center\page.tsx` | 0 | 0 | 13 | inline×13, tw-arb-size×30 |
| 8 | 66 | shared | `frontend\shared\src\components\ui\ErrorBoundary.tsx` | 17 | 0 | 11 | inline×11, px×21 |
| 9 | 63 | web_app | `frontend\web_app\src\app\supplier\batch-upload\page.tsx` | 0 | 0 | 2 | inline×2, tw-arb-size×57 |
| 10 | 56 | web_app | `frontend\web_app\src\app\admin\suppliers\page.tsx` | 1 | 0 | 1 | inline×1, tw-arb-size×53 |
| 11 | 46 | web_app | `frontend\web_app\src\app\suppliers\[id]\page.tsx` | 0 | 0 | 3 | inline×3, tw-arb-size×37 |
| 12 | 45 | web_app | `frontend\web_app\src\app\admin\employees\_components\employees-content.tsx` | 0 | 0 | 0 | tw-arb-size×45 |
| 13 | 44 | web_app | `frontend\web_app\src\app\supplier\profile\page.tsx` | 0 | 0 | 2 | inline×2, tw-arb-size×38 |
| 14 | 41 | web_app | `frontend\web_app\src\app\products\[id]\page.tsx` | 0 | 0 | 2 | inline×2, tw-arb-size×33 |
| 15 | 37 | web_app | `frontend\web_app\src\app\supplier\products\add\page.tsx` | 6 | 0 | 2 | inline×2, tw-arb-size×31 |
| 16 | 36 | web_app | `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` | 16 | 0 | 9 | inline×9, tw-arb-size×9 |
| 17 | 35 | web_app | `frontend\web_app\src\components\supplier\ParcelAuditWidget.tsx` | 6 | 0 | 2 | inline×2, tw-arb-size×29 |
| 18 | 35 | web_app | `frontend\web_app\src\app\admin\staff\_components\staff-content.tsx` | 0 | 0 | 0 | tw-arb-size×33 |
| 19 | 35 | web_app | `frontend\web_app\src\styles\tokens.css` | 229 | 0 | 0 | px×29 |
| 20 | 34 | web_app | `frontend\web_app\src\app\products\page.tsx` | 0 | 0 | 4 | inline×4, tw-arb-size×18 |
| 21 | 32 | web_app | `frontend\web_app\src\components\comms\Context\Context.tsx` | 0 | 0 | 0 | tw-arb-size×32 |
| 22 | 32 | web_app | `frontend\web_app\src\components\banner-effects.module.css` | 9 | 0 | 0 | px×18 |
| 23 | 31 | web_app | `frontend\web_app\src\app\supplier\labels\[id]\page.tsx` | 2 | 0 | 0 | tw-arb-size×27 |
| 24 | 30 | web_app | `frontend\web_app\src\app\supplier\payouts\page.tsx` | 0 | 0 | 0 | tw-arb-size×30 |
| 25 | 30 | web_app | `frontend\web_app\src\app\supplier\orders\SupplierOrdersList.tsx` | 0 | 0 | 0 | tw-arb-size×30 |
| 26 | 30 | web_app | `frontend\web_app\src\app\profile\page.tsx` | 0 | 0 | 0 | tw-arb-size×30 |
| 27 | 29 | web_app | `frontend\web_app\src\components\supplier\UploadProgressDashboard.tsx` | 0 | 0 | 2 | inline×2, tw-arb-size×23 |
| 28 | 29 | web_app | `frontend\web_app\src\app\admin\hr\page.tsx` | 0 | 0 | 2 | inline×2, tw-arb-size×23 |
| 29 | 29 | web_app | `frontend\web_app\src\app\admin\dashboard\_components\ExportsPanel.tsx` | 0 | 0 | 0 | tw-arb-size×29 |
| 30 | 28 | web_app | `frontend\web_app\src\app\admin\orders\page.tsx` | 0 | 0 | 0 | tw-arb-size×28, z-magic |
| 31 | 27 | web_app | `frontend\web_app\src\components\FilterSearchBar.tsx` | 0 | 0 | 1 | inline×1, tw-arb-size×22, z-magic |
| 32 | 26 | web_app | `frontend\web_app\src\components\PanelShell.tsx` | 0 | 0 | 1 | inline×1, tw-arb-size×23 |
| 33 | 26 | web_app | `frontend\web_app\src\components\ProductCard.tsx` | 0 | 0 | 1 | inline×1, tw-arb-size×23 |
| 34 | 26 | web_app | `frontend\web_app\src\components\comms\Stage\renderers\ChatStream.tsx` | 0 | 0 | 3 | inline×3, tw-arb-size×17 |
| 35 | 26 | web_app | `frontend\web_app\src\app\supplier\bulk\components\ProductDraftCard.tsx` | 0 | 0 | 0 | tw-arb-size×26 |
| 36 | 24 | web_app | `frontend\web_app\src\components\admin\AdminVideoPanel.tsx` | 0 | 0 | 0 | tw-arb-size×24 |
| 37 | 24 | web_app | `frontend\web_app\src\app\admin\countries\CountryLedgerTable.tsx` | 0 | 0 | 0 | tw-arb-size×24 |
| 38 | 23 | web_app | `frontend\web_app\src\app\logistics-partner\profile\page.tsx` | 0 | 0 | 0 | tw-arb-size×23 |
| 39 | 23 | web_app | `frontend\web_app\src\app\admin\promotions\_components\PromotionBuilderPanel.tsx` | 0 | 0 | 0 | tw-arb-size×23 |
| 40 | 23 | web_app | `frontend\web_app\src\app\admin\commission\page.tsx` | 0 | 0 | 0 | tw-arb-size×23 |
| 41 | 22 | web_app | `frontend\web_app\src\components\AdvancedFilter.tsx` | 0 | 0 | 1 | inline×1, tw-arb-size×19, z-magic |
| 42 | 22 | web_app | `frontend\web_app\src\components\supplier\CommissionPolicySummary.tsx` | 0 | 0 | 0 | tw-arb-size×22 |
| 43 | 22 | web_app | `frontend\web_app\src\components\admin\AdminChatPanel.tsx` | 1 | 0 | 0 | tw-arb-size×22 |
| 44 | 21 | web_app | `frontend\web_app\src\app\checkout\page.tsx` | 0 | 0 | 0 | tw-arb-size×21 |
| 45 | 21 | web_app | `frontend\web_app\src\app\brand\page.tsx` | 12 | 0 | 6 | inline×6, px×1 |
| 46 | 21 | shared | `frontend\shared\src\components\EnterpriseDataTable.tsx` | 0 | 0 | 3 | inline×3, tw-arb-size×10, px×2 |
| 47 | 20 | web_app | `frontend\web_app\src\app\admin\payments\page.tsx` | 0 | 0 | 0 | tw-arb-size×20 |
| 48 | 19 | web_app | `frontend\web_app\src\components\Header.tsx` | 0 | 0 | 0 | tw-arb-size×19, z-magic |
| 49 | 19 | web_app | `frontend\web_app\src\components\supplier\PhotoEditorModal.tsx` | 1 | 0 | 5 | inline×5, tw-arb-size×1, px×1 |
| 50 | 19 | web_app | `frontend\web_app\src\app\supplier\bulk\components\VariantSection.tsx` | 0 | 0 | 0 | tw-arb-size×19 |
| 51 | 19 | web_app | `frontend\web_app\src\app\admin\payouts\page.tsx` | 0 | 0 | 0 | tw-arb-size×19 |
| 52 | 18 | web_app | `frontend\web_app\src\logo\ZoziLogo.tsx` | 21 | 0 | 6 | inline×6 |
| 53 | 18 | shared | `frontend\shared\src\logo\LogoAnimation.tsx` | 10 | 0 | 3 | inline×3, px×5 |
| 54 | 18 | shared | `frontend\shared\src\logo\ZoziLogo.tsx` | 21 | 0 | 6 | inline×6 |
| 55 | 18 | shared | `frontend\shared\src\components\ui\Input.native.tsx` | 0 | 0 | 5 | inline×5, px×1 |
| 56 | 18 | shared | `frontend\shared\src\components\logo\LogoAnimation.tsx` | 10 | 0 | 3 | inline×3, px×5 |
| 57 | 18 | shared | `frontend\shared\src\components\logo\ZoziLogo.tsx` | 21 | 0 | 6 | inline×6 |
| 58 | 17 | web_app | `frontend\web_app\src\app\supplier\support\page.tsx` | 0 | 0 | 0 | tw-arb-size×17 |
| 59 | 17 | shared | `frontend\shared\src\components\ui\QuickFilters.native.tsx` | 6 | 0 | 4 | inline×4, px×3 |
| 60 | 16 | web_app | `frontend\web_app\src\components\BannerCarousel.tsx` | 5 | 0 | 4 | inline×4, tw-arb-size×4 |

## Color Inventory (most used first)

| Color | Hex | Usage | Files | Palette status |
|---|---|---:|---:|---|
| ![#ffffff](https://via.placeholder.com/14/ffffff/ffffff) | `#ffffff` | 75 | 26 | ✅ token |
| ![#000000](https://via.placeholder.com/14/000000/000000) | `#000000` | 49 | 17 | ✅ token |
| ![#d4af37](https://via.placeholder.com/14/d4af37/d4af37) | `#d4af37` | 21 | 4 | ✅ token |
| ![#ef4444](https://via.placeholder.com/14/ef4444/ef4444) | `#ef4444` | 18 | 10 | ✅ token |
| ![#22c55e](https://via.placeholder.com/14/22c55e/22c55e) | `#22c55e` | 14 | 9 | ✅ token |
| ![#3b82f6](https://via.placeholder.com/14/3b82f6/3b82f6) | `#3b82f6` | 14 | 10 | ✅ token |
| ![#f59e0b](https://via.placeholder.com/14/f59e0b/f59e0b) | `#f59e0b` | 13 | 8 | ✅ token |
| ![#0f172a](https://via.placeholder.com/14/0f172a/0f172a) | `#0f172a` | 11 | 8 | ✅ token |
| ![#f8fafc](https://via.placeholder.com/14/f8fafc/f8fafc) | `#f8fafc` | 11 | 8 | ✅ token |
| ![#111111](https://via.placeholder.com/14/111111/111111) | `#111111` | 10 | 5 | ✅ token |
| ![#6b7280](https://via.placeholder.com/14/6b7280/6b7280) | `#6b7280` | 10 | 6 | ✅ token |
| ![#ffd700](https://via.placeholder.com/14/ffd700/ffd700) | `#ffd700` | 9 | 4 | ✅ token |
| ![#9ca3af](https://via.placeholder.com/14/9ca3af/9ca3af) | `#9ca3af` | 9 | 6 | ✅ token |
| ![#a3b3c8](https://via.placeholder.com/14/a3b3c8/a3b3c8) | `#a3b3c8` | 9 | 3 | ✅ token |
| ![#2563eb](https://via.placeholder.com/14/2563eb/2563eb) | `#2563eb` | 8 | 4 | ✅ token |
| ![#1a1a1a](https://via.placeholder.com/14/1a1a1a/1a1a1a) | `#1a1a1a` | 8 | 3 | ✅ token |
| ![#f8c400](https://via.placeholder.com/14/f8c400/f8c400) | `#f8c400` | 7 | 7 | ✅ token |
| ![#2a7006](https://via.placeholder.com/14/2a7006/2a7006) | `#2a7006` | 7 | 7 | ✅ token |
| ![#f1f5f9](https://via.placeholder.com/14/f1f5f9/f1f5f9) | `#f1f5f9` | 7 | 5 | ✅ token |
| ![#38bdf8](https://via.placeholder.com/14/38bdf8/38bdf8) | `#38bdf8` | 7 | 4 | ✅ token |
| ![#1e293b](https://via.placeholder.com/14/1e293b/1e293b) | `#1e293b` | 7 | 6 | ✅ token |
| ![#e2ff70](https://via.placeholder.com/14/e2ff70/e2ff70) | `#e2ff70` | 6 | 6 | ✅ token |
| ![#c8ec22](https://via.placeholder.com/14/c8ec22/c8ec22) | `#c8ec22` | 6 | 6 | ✅ token |
| ![#86be12](https://via.placeholder.com/14/86be12/86be12) | `#86be12` | 6 | 6 | ✅ token |
| ![#409808](https://via.placeholder.com/14/409808/409808) | `#409808` | 6 | 6 | ✅ token |
| ![#1a5204](https://via.placeholder.com/14/1a5204/1a5204) | `#1a5204` | 6 | 6 | ✅ token |
| ![#e8a000](https://via.placeholder.com/14/e8a000/e8a000) | `#e8a000` | 6 | 6 | ✅ token |
| ![#eeff99](https://via.placeholder.com/14/eeff99/eeff99) | `#eeff99` | 6 | 6 | ✅ token |
| ![#ccee38](https://via.placeholder.com/14/ccee38/ccee38) | `#ccee38` | 6 | 6 | ✅ token |
| ![#97d01a](https://via.placeholder.com/14/97d01a/97d01a) | `#97d01a` | 6 | 6 | ✅ token |
| ![#55b010](https://via.placeholder.com/14/55b010/55b010) | `#55b010` | 6 | 6 | ✅ token |
| ![#ffd740](https://via.placeholder.com/14/ffd740/ffd740) | `#ffd740` | 6 | 6 | ✅ token |
| ![#ffcc22](https://via.placeholder.com/14/ffcc22/ffcc22) | `#ffcc22` | 6 | 6 | ✅ token |
| ![#fff550](https://via.placeholder.com/14/fff550/fff550) | `#fff550` | 6 | 6 | ✅ token |
| ![#f0c800](https://via.placeholder.com/14/f0c800/f0c800) | `#f0c800` | 6 | 6 | ✅ token |
| ![#d08c00](https://via.placeholder.com/14/d08c00/d08c00) | `#d08c00` | 6 | 6 | ✅ token |
| ![#a86000](https://via.placeholder.com/14/a86000/a86000) | `#a86000` | 6 | 6 | ✅ token |
| ![#ec4899](https://via.placeholder.com/14/ec4899/ec4899) | `#ec4899` | 6 | 3 | ✅ token |
| ![#0ea5e9](https://via.placeholder.com/14/0ea5e9/0ea5e9) | `#0ea5e9` | 6 | 3 | ✅ token |
| ![#cbd5e1](https://via.placeholder.com/14/cbd5e1/cbd5e1) | `#cbd5e1` | 6 | 5 | ✅ token |

## Color Theme Drift Clusters

These colors are visually near-identical but written differently — 
the classic symptom of theme drift.

- `#ffd440` ×4 ≈ `#ffd740` ×6
- `#cbd5e1` ×6 ≈ `#d1d5db` ×3

## Design Damage Hotlist

| Sev | Rule | Domain | Location | Problem | Intended |
|---|---|---|---|---|---|
| 🟡 | DS03 | design | `frontend\shared\src\theme.native.ts` | off-palette color #d1d5db used 3× in 1 file(s): frontend\shared\src\theme.native.ts | replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color |
| 🟡 | DS13 | shared/web_app | `frontend\shared\src\components\logo\LogoAnimation.tsx, frontend\shared\src\logo\LogoAnimation.tsx` | color drift (10× total): #ffd440 (×4) ≈ #ffd740 (×6) | web and mobile disagree on this color — unify in shared tokens |
| 🟡 | DS13 | shared/web_app | `frontend\shared\src\components\ui\ThemeToggle.native.tsx, frontend\shared\src\theme.native.ts, frontend\web_app\src\app\` | color drift (9× total): #cbd5e1 (×6) ≈ #d1d5db (×3) | web and mobile disagree on this color — unify in shared tokens |

## Domain: design

- 🟢 **DSI2** `frontend` — token coverage: 99.6% of color occurrences match the palette (782/785, 192 distinct colors)
- 🟡 **DS03** `frontend\shared\src\theme.native.ts` — off-palette color #d1d5db used 3× in 1 file(s): frontend\shared\src\theme.native.ts → *replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color*
- 🟡 **DS07** `frontend` — 26 distinct hardcoded font sizes: 0.75rem, 0.7rem, 0.875rem, 0.8rem, 1.15rem, 1.35rem, 1.5rem, 1.875rem, 11, 12, 12px, 13 ... → *collapse onto a type scale (text-xs/sm/base/lg/xl...); max ~8 steps*
- 🟡 **DS07** `frontend\shared\src\components\logo\Logo.web.tsx` — font family literal 'var(--font-nunito, 'Nunito', var(--font-body, 'Sora', system-ui, sans-serif))' hardcoded in 5 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\shared\src\components\logo\LogoAnimation.tsx` — font family literal 'var(--font-body, 'Sora', system-ui, sans-serif)' hardcoded in 2 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\src\app\brand\page.tsx` — font family literal 'Sora', 'Montserrat', system-ui, sans-serif' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\shared\src\components\ui\ErrorBoundary.tsx` — font family literal 'system-ui, sans-serif' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\src\styles\comm.css` — font family literal 'var(--font-display, ui-sans-serif)' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\src\styles\globals.css` — font family literal 'var(--font-arabic), "Arabic UI", "Noto Naskh Arabic", "Noto Sans Arabic", "Segoe UI", Tahoma,
               "Arial Unicode MS", sans-serif' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS07** `frontend\web_app\src\styles\globals.css` — font family literal '"Arabic UI"' hardcoded in 1 file(s) → *reference the font token from the theme; one brand family + one mono*
- 🟡 **DS09** `frontend` — 30 distinct border-radius values: 0 0 4px 4px, 0.5rem, 1.25rem, 1.2rem, 1.4rem, 1.6rem, 1.75rem, 1.7rem, 10px, 12 → *standardize on 3-4 radii tokens (sm/md/lg/full)*
- 🟡 **DS11** `frontend` — 22 distinct shadow definitions — no elevation system → *define 3 elevation tokens (shadow-sm/md/lg) and reuse them*
- 🟡 **DS16** `frontend` — 7 distinct animation durations: 120ms, 150ms, 180ms, 200ms, 300ms, 500ms, 700ms → *standardize on 2-3 motion tokens (150ms/250ms/400ms)*
- 🟢 **DSI1** `frontend` — top colors in use: #ffffff×75, #000000×49, #d4af37×21, #ef4444×18, #22c55e×14, #3b82f6×14, #f59e0b×13, #0f172a×11, #f8fafc×11, #111111×10

## Domain: web_app

- 🟡 **DS01** `frontend\web_app\src\components\admin\commandCenter\hud.tsx` — 62 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\BackgroundEffect.tsx` — 33 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — 33 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\app\admin\command-center\page.tsx` — 13 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\app\supplier\upload\bg-compare\page.tsx` — 9 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\logo\ZoziLogo.tsx` — 6 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\app\brand\page.tsx` — 6 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\supplier\PhotoEditorModal.tsx` — 5 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\BannerCarousel.tsx` — 4 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\ems\ChatEnrichment.tsx` — 4 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\app\products\page.tsx` — 4 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\map\MapView.tsx` — 3 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\components\comms\Stage\renderers\ChatStream.tsx` — 3 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\app\suppliers\[id]\page.tsx` — 3 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\app\admin\treasury\_components\treasury-content.tsx` — 3 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\web_app\src\app\admin\ess\page.tsx` — 3 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS08** `frontend\web_app\src\styles\globals.css` — 164 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\styles\comm.css` — 63 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\styles\tokens.css` — 29 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\components\BackgroundEffect.tsx` — 26 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\components\banner-effects.module.css` — 18 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
- 🟡 **DS08** `frontend\web_app\src\components\BannerCanvasEditor.tsx` — 10 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*

## Domain: shared

- 🟡 **DS01** `frontend\shared\src\components\ui\ErrorBoundary.tsx` — 11 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\shared\src\logo\ZoziLogo.tsx` — 6 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\shared\src\components\logo\ZoziLogo.tsx` — 6 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\shared\src\components\ui\Input.native.tsx` — 5 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\shared\src\components\ui\QuickFilters.native.tsx` — 4 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\shared\src\components\ui\SearchBar.native.tsx` — 4 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\shared\src\logo\LogoAnimation.tsx` — 3 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\shared\src\components\EnterpriseDataTable.tsx` — 3 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS01** `frontend\shared\src\components\logo\LogoAnimation.tsx` — 3 inline style object(s) — hardcoded CSS inside the component → *move to Tailwind classes / StyleSheet.create / a shared component variant*
- 🟡 **DS08** `frontend\shared\src\components\ui\ErrorBoundary.tsx` — 21 raw px value(s) — hardcoded spacing/sizing → *use the spacing scale (p-2/gap-4...) or RN spacing tokens*
