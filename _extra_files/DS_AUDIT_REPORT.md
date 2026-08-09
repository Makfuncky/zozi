# Design-System Audit — DS01–DS18 (complete, read-only)


## 0. Synthesis & Remediation Roadmap


### 0.1 Method

- Faithful read-only replica of `scripts/system_trackers/system_architecture_audit.py` SECTION 50-54 (DS01-DS18).
- Palette discovered from `tailwind.config.js` + CSS custom properties across `frontend/` (88 tokens).
- Scanned **857** frontend files with `os.walk` + ignore-dir pruning (robust where the original rglob crashed on `node_modules`).
- Each file profiled for color literals (off-palette classification via CIE76 distance >10 to nearest token), inline `style={{}}}` objects, `<style>` tags, `!important`, arbitrary Tailwind, raw px, z-index, radii, shadows, font sizes/families, motion durations, breakpoints, contrast pairs, CSS-in-JS.

### 0.2 What is REAL debt vs FALSE POSITIVE

- **DS02 (`<style>` tags, 3): FALSE POSITIVE** - the `<style` substring exists only inside `/* */` comments in `banner-effects.css`, `hud.css`, `print.css`. No real `<style>` tags. Audit regex `<style[\s>/]` matches the word inside comments.
- **DS01 / DS08 inline & px counts are inflated by mobile_app** - React Native's `StyleSheet.create` legitimately uses `style={{}}}` (1661 blocks / 1336 px). This is FRAMEWORK-STANDARD, not a violation. Genuine web debt: **web_app = 247 inline blocks / 1064 px**.
- **DS10 / DS16 / DS13 / DS07 nuances:** max z-index is 999 (<1000 -> no magic-z violation); DS16 is 9 durations (over the 6-token limit, so still a violation - 0/120/180ms are the extras beyond globals.css's 6); DS13 is not a web/mobile *mismatch* but mobile_app having **no token source at all**; DS07's 12 font-families are mostly formatting variants of the same 2 token families (`--font-body`/`--font-display`).

### 0.3 Root causes

1. **`globals.css` is a 9601-line hand-authored monolith** (not build output - full Tailwind build is only ~1900 lines). It carries 899 px, 81 shadows, 19 radii, 57 off-palette literals. This single file dominates DS08/DS09/DS11/DS03 web debt.
2. **No elevation/shadow scale** - 96 distinct `box-shadow` definitions, mostly near-duplicate glass shadows differing only in alpha. Should collapse to <=4 tokens (`shadow-card-sm/md/lg/xl` already defined in tailwind.config but unused).
3. **No radius scale adoption** - 30 distinct radii (px + rem + % + 9999px). Should collapse to <=5 tokens (`rounded-sm/md/lg/xl/pill`).
4. **Off-palette literals & drift** - 140 off-palette colors / 16 near-duplicate clusters (e.g. `#0f172a`~`#111827`, `#f8fafc`~`#fafcf6`). Brand greens (`#2fb43d`, `#6ae022`) and neutrals are re-typed instead of referenced from tokens.
5. **mobile_app has no token module** - every screen hardcodes colors in StyleSheet. DS13 + DS01(mobile) stem from this.
6. **web_app inline styles (247)** - true DS01 in components like `BannerCanvasEditor.tsx` (54 off-palette, 33 inline), `hud.tsx`, `BackgroundEffect.tsx`.

### 0.4 Prioritized remediation roadmap (one module at a time, audit+build+jest after each)

| # | DS | Scope | Effort | Action |
|---|---|---|---|---|
| 1 | DS11 | globals.css | M | Collapse 96 shadows -> 4 `shadow-*` tokens (tailwind.config already has card-sm/md/lg/xl + glass). |
| 2 | DS09 | globals.css | M | Collapse 30 radii -> 5 `rounded-*` tokens. |
| 3 | DS08 | globals.css | L | Replace 899 raw px with spacing/size tokens (keep `globals.css` as `@tailwind` layers + base). |
| 4 | DS03/DS04 | globals.css + components | L | Map 140 off-palette literals + 16 drift clusters onto nearest token. |
| 5 | DS16 | codebase | S | Standardize 9 durations -> 6 `duration-*` tokens (already exist). |
| 6 | DS01 | web_app components | L | Convert 247 web `style={{}}}` blocks -> Tailwind classes / `StyleSheet.create`. |
| 7 | DS13 | mobile_app | L | Create `mobile_app/theme/tokens.ts` mirroring `shared/src/theme.ts`; reference from StyleSheet. |
| 8 | DS07 | codebase | M | Collapse 35 font sizes -> 8-step scale; 2 families (body/display) via tokens. |
| 9 | DS12 | shared | S | Promote `shared/src/theme.ts` (88 tokens) as the single source; document usage. |

**Already OK:** DS05 (0 arbitrary colors), DS06 (0 `!important`), DS14 (Tailwind-only), DS15 (no low-contrast inline pairs), DS17 (0 unused tokens), DS18 (0 off-scale breakpoints), DS10 (max z=999 < 1000).

**Decision needed before edits:** per the prior step you chose *audit-only first* for `globals.css`. Modules 1-4 (the bulk of web debt) require editing `globals.css`; module 6 edits web components; module 7 is a new token file for mobile. No `scripts/`, no `SYSTEM_AUDIT_REPORT.md`, no `backend/main.py` will be touched.


## 0. Synthesis & Remediation Roadmap


### 0.1 Method

- Faithful read-only replica of `scripts/system_trackers/system_architecture_audit.py` SECTION 50–54 (DS01–DS18).
- Palette discovered from `tailwind.config.js` + CSS custom properties across `frontend/` (88 tokens).
- Scanned **857** frontend files with `os.walk` + ignore-dir pruning (robust where the original rglob crashed on `node_modules`).
- Each file profiled for color literals (off-palette classification via CIE76 distance >10 to nearest token), inline `style={{}}}` objects, `<style>` tags, `!important`, arbitrary Tailwind, raw px, z-index, radii, shadows, font sizes/families, motion durations, breakpoints, contrast pairs, CSS-in-JS.

### 0.2 What is REAL debt vs FALSE POSITIVE

- **DS02 (`<style>` tags, 3): FALSE POSITIVE** — the `<style` substring exists only inside `/* */` comments in `banner-effects.css`, `hud.css`, `print.css`. No real `<style>` tags. Audit regex `<style[\s>/]` matches the word inside comments.
- **DS01 / DS08 inline & px counts are inflated by mobile_app** — React Native's `StyleSheet.create` legitimately uses `style={{}}}` (1661 blocks / 1336 px). This is FRAMEWORK-STANDARD, not a violation. Genuine web debt: **web_app = 247 inline blocks / 1064 px**.
- **DS10 / DS16 / DS13 / DS07 nuances:** max z-index is 999 (<1000 → no magic-z violation); DS16 is 9 durations (over the 6-token limit, so still a violation — 0/120/180ms are the extras beyond globals.css's 6); DS13 is not a web/mobile *mismatch* but mobile_app having **no token source at all**; DS07's 12 font-families are mostly formatting variants of the same 2 token families (`--font-body`/`--font-display`).

### 0.3 Root causes

1. **`globals.css` is a 9601-line hand-authored monolith** (not build output — full Tailwind build is only ~1900 lines). It carries 899 px, 81 shadows, 19 radii, 57 off-palette literals. This single file dominates DS08/DS09/DS11/DS03 web debt.
2. **No elevation/shadow scale** — 96 distinct `box-shadow` definitions, mostly near-duplicate glass shadows differing only in alpha. Should collapse to ≤4 tokens (`shadow-card-sm/md/lg/xl` already defined in tailwind.config but unused).
3. **No radius scale adoption** — 30 distinct radii (px + rem + % + 9999px). Should collapse to ≤5 tokens (`rounded-sm/md/lg/xl/pill`).
4. **Off-palette literals & drift** — 140 off-palette colors / 16 near-duplicate clusters (e.g. `#0f172a`≈`#111827`, `#f8fafc`≈`#fafcf6`). Brand greens (`#2fb43d`, `#6ae022`) and neutrals are re-typed instead of referenced from tokens.
5. **mobile_app has no token module** — every screen hardcodes colors in StyleSheet. DS13 + DS01(mobile) stem from this.
6. **web_app inline styles (247)** — true DS01 in components like `BannerCanvasEditor.tsx` (54 off-palette, 33 inline), `hud.tsx`, `BackgroundEffect.tsx`.

### 0.4 Prioritized remediation roadmap (one module at a time, audit+build+jest after each)

| # | DS | Scope | Effort | Action |
|---|---|---|---|---|
| 1 | DS11 | globals.css | M | Collapse 96 shadows → 4 `shadow-*` tokens (tailwind.config already has card-sm/md/lg/xl + glass). |
| 2 | DS09 | globals.css | M | Collapse 30 radii → 5 `rounded-*` tokens. |
| 3 | DS08 | globals.css | L | Replace 899 raw px with spacing/size tokens (keep `globals.css` as `@tailwind` layers + base). |
| 4 | DS03/DS04 | globals.css + components | L | Map 140 off-palette literals + 16 drift clusters onto nearest token. |
| 5 | DS16 | codebase | S | Standardize 9 durations → 6 `duration-*` tokens (already exist). |
| 6 | DS01 | web_app components | L | Convert 247 web `style={{}}}` blocks → Tailwind classes / `StyleSheet.create`. |
| 7 | DS13 | mobile_app | L | Create `mobile_app/theme/tokens.ts` mirroring `shared/src/theme.ts`; reference from StyleSheet. |
| 8 | DS07 | codebase | M | Collapse 35 font sizes → 8-step scale; 2 families (body/display) via tokens. |
| 9 | DS12 | shared | S | Promote `shared/src/theme.ts` (88 tokens) as the single source; document usage. |

**Already OK:** DS05 (0 arbitrary colors), DS06 (0 `!important`), DS14 (Tailwind-only), DS15 (no low-contrast inline pairs), DS17 (0 unused tokens), DS18 (0 off-scale breakpoints), DS10 (max z=999 < 1000).

**Decision needed before edits:** per the prior step you chose *audit-only first* for `globals.css`. Modules 1–4 (the bulk of web debt) require editing `globals.css`; module 6 edits web components; module 7 is a new token file for mobile. No `scripts/`, no `SYSTEM_AUDIT_REPORT.md`, no `backend/main.py` will be touched.

Repo: `D:\Projects\10- E-COMMERCE WEBSITE\zozi`  •  Files scanned: **857**  •  Palette tokens discovered: **88**

## 1. Executive summary

| Metric | Value | Audit threshold | Verdict |
|---|---|---|---|
| Palette token coverage | 83.6% | high | LOW |
| Off-palette color occurrences | 358 (140 distinct) | 0 | VIOLATION |
| Color drift clusters | 16 | 0 | VIOLATION |
| Inline style objects | 1949 | 0 | VIOLATION |
| `<style>` tags in components | 3 | 0 | VIOLATION |
| `!important` | 0 | 0 | OK |
| Raw px values | 2443 | ≤100 | VIOLATION |
| Distinct border-radius | 30 | ≤5 | VIOLATION |
| Distinct box-shadows | 96 | ≤4 | VIOLATION |
| Distinct font sizes | 35 | ≤8 | VIOLATION |
| Distinct font families | 12 | ≤2 | VIOLATION |
| Distinct motion durations | 9 | ≤6 | VIOLATION |
| Magic z-index (≥1000) | 8 (max 999) | 0 | OK |
| CSS-in-JS libraries | 0 | 0 | OK |
| Off-scale breakpoints | 0 | 0 | OK |
Total inline blocks found: **1949** across 123 files.

**IMPORTANT — workspace split:** mobile_app uses React Native `StyleSheet.create`/`style={{}}}` (**1661** blocks) — this is FRAMEWORK-STANDARD, NOT a DS01 violation. The real DS01 debt is in **web_app: 247** inline blocks (across 16 files) plus shared: 41.

Web workspace files with ≥3 inline style objects (the actual violation set):

- `frontend/web_app/src/app/admin/command-center/page.tsx`
- `frontend/web_app/src/app/admin/ess/page.tsx`
- `frontend/web_app/src/app/admin/treasury/_components/treasury-content.tsx`
- `frontend/web_app/src/app/brand/page.tsx`
- `frontend/web_app/src/app/products/page.tsx`
- `frontend/web_app/src/app/supplier/upload/bg-compare/page.tsx`
- `frontend/web_app/src/app/suppliers/[id]/page.tsx`
- `frontend/web_app/src/components/BackgroundEffect.tsx`
- `frontend/web_app/src/components/BannerCanvasEditor.tsx`
- `frontend/web_app/src/components/BannerCarousel.tsx`
- `frontend/web_app/src/components/admin/commandCenter/hud.tsx`
- `frontend/web_app/src/components/comms/Stage/renderers/ChatStream.tsx`
- `frontend/web_app/src/components/ems/ChatEnrichment.tsx`
- `frontend/web_app/src/components/map/MapView.tsx`
- `frontend/web_app/src/components/supplier/PhotoEditorModal.tsx`
- `frontend/web_app/src/logo/ZoziLogo.tsx`

(Note: DS02 `<style>` tags = 3 — confirmed FALSE POSITIVE: the `<style` substring appears only inside `/* */` comments in banner-effects.css, hud.css, print.css.)

## 3. DS02 — `<style>` tags inside components

- `frontend/web_app/src/app/supplier/labels/[id]/print.css` (FALSE-POSITIVE: literal `<style` appears only inside `/* */` comments — confirmed) 
- `frontend/web_app/src/components/admin/commandCenter/hud.css` (FALSE-POSITIVE: literal `<style` appears only inside `/* */` comments — confirmed) 
- `frontend/web_app/src/components/banner-effects.css` (FALSE-POSITIVE: literal `<style` appears only inside `/* */` comments — confirmed) 

## 4. DS03 / DS04 — Off-palette literals & color drift

Off-palette hex occurrences: **358** (140 distinct). Top:
- `#b91c1c` — 2×
- `#dc2626` — 6×
- `#c2410c` — 1×
- `#1d4ed8` — 1×
- `#f43f5e` — 1×
- `#6d28d9` — 2×
- `#facc15` — 20×
- `#db4437` — 2×
- `#1877f2` — 2×
- `#080d1a` — 1×
- `#8b5cf6` — 17×
- `#999999` — 1×
- `#0a2e0a` — 1×
- `#1a4a1a` — 1×
- `#1a1a2e` — 1×
- `#10233e` — 4×
- `#2d1b00` — 1×
- `#4a2800` — 1×
- `#1a0a2e` — 1×
- `#2d1650` — 1×
- `#0a1e2e` — 1×
- `#163040` — 1×
- `#bef264` — 1×
- `#fcd34d` — 2×
- `#a78bfa` — 8×
- `#b45309` — 3×
- `#1e293b` — 12×
- `#d08c00` — 7×
- `#fca5a5` — 2×
- `#bbf7d0` — 2×
- `#15803d` — 1×
- `#7dd3fc` — 1×
- `#0369a1` — 2×
- `#6ae022` — 7×
- `#808080` — 3×
- `#db2777` — 1×
- `#65a30d` — 2×
- `#0f766e` — 1×
- `#cccccc` — 6×
- `#666666` — 2×

Color drift clusters (near-duplicate colors used as if different):
- ≈ `#060e1c`(×1) ≈ `#080d18`(×4) ≈ `#080d1a`(×1)
- ≈ `#0f172a`(×54) ≈ `#111827`(×2)
- ≈ `#163040`(×1) ≈ `#1a2e45`(×1)
- ≈ `#1a1a1a`(×9) ≈ `#1c1917`(×2)
- ≈ `#475569`(×3) ≈ `#4b5563`(×1)
- ≈ `#cbd5e1`(×8) ≈ `#d1d5db`(×5)
- ≈ `#e3e9d8`(×1) ≈ `#e6ebdd`(×1)
- ≈ `#edf1e5`(×1) ≈ `#eef3e6`(×1)
- ≈ `#f0fdf0`(×2) ≈ `#f3f8ee`(×1) ≈ `#f4f8ee`(×1) ≈ `#f5f9ef`(×1) ≈ `#f5faf0`(×1)
- ≈ `#f1f5f9`(×7) ≈ `#f5f5f5`(×1)
- ≈ `#f3f6ee`(×1) ≈ `#f5f7ef`(×1) ≈ `#f7faf3`(×3)
- ≈ `#f8faf5`(×1) ≈ `#f8fafc`(×14) ≈ `#f8fbf4`(×3) ≈ `#f8fcf3`(×1) ≈ `#f8fcf4`(×1) ≈ `#f9fbf5`(×2) ≈ `#fafcf6`(×1) ≈ `#fbfcf8`(×5)
- ≈ `#fef2f2`(×1) ≈ `#fff7ed`(×1)
- ≈ `#fef3c7`(×3) ≈ `#fff7bf`(×1)
- ≈ `#ffd440`(×4) ≈ `#ffd740`(×7)
- ≈ `#fff176`(×1) ≈ `#fff27a`(×1)

## 5. DS05 — Arbitrary Tailwind color values (`bg-[#...]`)

Files using arbitrary Tailwind colors: 0

## 6. DS06 — `!important`

None.

## 7. DS07 — Hardcoded typography

Distinct font sizes: **35** (limit 8). Values: 0.75rem, 0.7rem, 0.875rem, 0.8rem, 1.05rem, 1.125rem, 1.15rem, 1.25rem, 1.35rem, 1.5rem, 1.6rem, 1.7rem, 1.875rem, 100%, 10px, 11px, 12px, 13px, 14px, 15px, 1em, 1rem, 2.25rem, 2rem, 3.75rem, 3rem, 4.5rem, 6rem, 75%, 7px, 80%, 8px, 9px, clamp(3.5rem, 9vw, 8.5rem), inherit

Distinct font families: **12** (limit 2). Values: "Arabic UI", Sora', 'Montserrat', system-ui, sans-serif, inherit, system-ui, sans-serif, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace, var(--font-arabic), "Arabic UI", "Noto Naskh Arabic", "Noto Sans Arabic", "Segoe UI", Tahoma,
               "Arial Unicode MS", sans-serif, var(--font-body), Sora, sans-serif, var(--font-body), Sora, system-ui, sans-serif, var(--font-body, 'Sora', system-ui, sans-serif), var(--font-display), Fraunces, serif, var(--font-display, ui-sans-serif), var(--font-nunito, 'Nunito', var(--font-body, 'Sora', system-ui, sans-serif))

## 8. DS08 — Raw px (spacing/dimension)

Total raw px: **2443** (limit ≤100). By workspace: mobile_app=1336, shared=43, web_app=1064.
mobile_app px are React Native `StyleSheet` dimensions (framework-standard). The DS08 debt is **web_app: 1064 px**, concentrated in `src/styles/globals.css` (hand-authored component CSS).

Worst web_app files by raw px:
- `frontend/web_app/src/components/BannerCanvasEditor.tsx`: 10 px
- `frontend/web_app/src/styles/globals.css`: 899 px
- `frontend/web_app/src/components/admin/commandCenter/hud.tsx`: 2 px
- `frontend/web_app/src/components/BackgroundEffect.tsx`: 26 px

## 9. DS09 — Inconsistent border-radius

Distinct radius values: **30** (limit ≤5). Values: `0px`, `1px`, `2px`, `3px`, `4px`, `50%`, `8px`, `10px`, `12px`, `1rem`, `20px`, `22px`, `28px`, `2rem`, `999px`, `0.5rem`, `1.2rem`, `1.4rem`, `1.5rem`, `1.6rem`, `1.7rem`, `9999px`, `0.25rem`, `0.75rem`, `1.25rem`, `1.75rem`, `inherit`, `40% 40% 46% 46%`, `50% 50% 48% 48%`, `var(--radius-card)`

## 10. DS10 — Magic z-index

Magic z-index values: 60, 100, 150, 151, 200, 201, 998, 999
- `frontend/web_app/src/app/admin/orders/page.tsx`
- `frontend/web_app/src/components/AdvancedFilter.tsx`
- `frontend/web_app/src/components/AdvancedFilterPanel.tsx`
- `frontend/web_app/src/components/AuthRequiredModal.tsx`
- `frontend/web_app/src/components/BannerCanvasEditor.tsx`
- `frontend/web_app/src/components/ColumnVisibilityPanel.tsx`
- `frontend/web_app/src/components/FilterSearchBar.tsx`
- `frontend/web_app/src/components/Header.tsx`
- `frontend/web_app/src/components/HeaderSearchBar.tsx`
- `frontend/web_app/src/components/MobileSearchOverlay.tsx`
- `frontend/web_app/src/components/UnifiedSearchBar.tsx`
- `frontend/web_app/src/components/supplier/BgStrategyOnboardingTooltip.tsx`
- `frontend/web_app/src/components/ui/Dropdown.tsx`

## 11. DS11 — Inconsistent box-shadow

Distinct shadow definitions: **96** (limit ≤4). Sample:
- `-4px 0 24px rgba(0, 0, 0, 0.12)`
- `0 -4px 24px rgba(0, 0, 0, 0.12)`
- `0 0 0 3px color-mix(in srgb, var(--color-brand) 12%, transparent)`
- `0 0 0 3px color-mix(in srgb, var(--color-brand) 18%, transparent)`
- `0 0 0 3px color-mix(in srgb, var(--color-brand) 28%, transparent)`
- `0 0 0 3px rgba(47, 180, 61, 0.12), 0 10px 24px -18px rgba(47, 180, 61, 0.24)`
- `0 0 0 3px rgba(47, 180, 61, 0.12), inset 0 1.5px 3px rgba(74, 93, 53, 0.04)`
- `0 0 16px #22d3ee30`
- `0 0 18px rgba(245,158,11,.8)`
- `0 0 24px color-mix(in srgb, var(--color-accent) 40%, transparent)`
- `0 0 30px rgba(253,230,138,.9)`
- `0 0 4px rgba(212,175,55,0.5)`
- `0 0 50px rgba(212,175,55,0.4), 0 0 100px rgba(212,175,55,0.2)`
- `0 10px 26px rgba(0, 0, 0, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.08)`
- `0 12px 20px -16px rgba(47, 148, 64, 0.42), 0 8px 16px -18px rgba(242, 201, 76, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.22)`
- `0 12px 24px -22px rgba(15, 23, 42, 0.14)`
- `0 12px 24px -24px color-mix(in srgb, var(--color-text) 25%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.16)`
- `0 12px 28px -12px rgba(0, 0, 0, 0.18), 0 0 0 1.5px color-mix(in srgb, var(--color-brand) 6%, transparent)`
- `0 12px 28px -12px rgba(15, 23, 42, 0.08), 0 4px 8px -4px rgba(50, 90, 36, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.92)`
- `0 12px 32px -18px rgba(15, 23, 42, 0.14), 0 4px 12px -8px rgba(47, 180, 61, 0.1), inset 0 1.5px 0 rgba(255, 255, 255, 1)`
- `0 14px 24px -16px rgba(47, 148, 64, 0.48), 0 10px 18px -18px rgba(242, 201, 76, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.26)`
- `0 14px 36px -28px color-mix(in srgb, var(--color-brand) 56%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.08)`
- `0 16px 28px -24px rgba(15, 23, 42, 0.14)`
- `0 16px 30px -24px rgba(15, 23, 42, 0.18)`
- `0 16px 36px -28px rgba(15, 23, 42, 0.16), 0 6px 14px -10px rgba(47, 180, 61, 0.12)`
- `0 16px 40px -8px rgba(0, 0, 0, 0.14), 0 4px 12px -2px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.9)`
- `0 18px 28px -24px color-mix(in srgb, var(--color-text) 28%, transparent), 0 8px 18px -20px color-mix(in srgb, var(--color-brand) 15%, transp`
- `0 18px 30px -22px color-mix(in srgb, var(--color-accent) 50%, transparent), 0 10px 22px -22px color-mix(in srgb, var(--color-brand) 25%, tra`
- `0 18px 30px -22px rgba(242, 201, 76, 0.72), 0 10px 22px -20px rgba(47, 180, 61, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.24)`
- `0 18px 32px -18px rgba(47, 180, 61, 0.48), 0 10px 20px -20px rgba(242, 201, 76, 0.3), inset 0 1px 0 rgba(255,255,255,0.3)`
- `0 18px 32px -22px color-mix(in srgb, var(--color-brand) 45%, transparent), 0 10px 24px -20px color-mix(in srgb, var(--color-accent) 30%, tra`
- `0 18px 32px -22px color-mix(in srgb, var(--color-danger) 50%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.15)`
- `0 18px 32px -22px rgba(47, 180, 61, 0.68), 0 10px 24px -20px rgba(242, 201, 76, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.2)`
- `0 18px 34px -22px rgba(15, 23, 42, 0.12), 0 10px 18px -16px rgba(47, 180, 61, 0.1), inset 0 1.5px 0 rgba(255, 255, 255, 1), inset 0 -1px 0 r`
- `0 18px 34px -28px rgba(15, 23, 42, 0.18)`
- `0 18px 35px -26px rgba(15, 23, 42, 0.45)`
- `0 18px 40px -12px rgba(0, 0, 0, 0.25), 0 4px 12px -4px rgba(0, 0, 0, 0.08), inset 0 1px 0 color-mix(in srgb, var(--color-text) 6%, transpare`
- `0 18px 40px -28px rgba(15, 23, 42, 0.34)`
- `0 18px 40px -28px rgba(15, 23, 42, 0.4)`
- `0 18px 40px -30px rgba(15, 23, 42, 0.14), inset 0 1px 0 rgba(255, 255, 255, 0.7)`
- `0 18px 44px -20px rgba(15, 23, 42, 0.18), 0 8px 20px -10px rgba(47, 180, 61, 0.16), inset 0 1.5px 0 rgba(255, 255, 255, 1)`
- `0 18px 50px -40px color-mix(in srgb, black 48%, transparent)`
- `0 18px 60px -34px color-mix(in srgb, var(--color-brand-dark) 32%, transparent), inset 0 1px 0 color-mix(in srgb, white 8%, transparent)`
- `0 1px 0 rgba(64, 84, 46, 0.08), 0 18px 40px -32px rgba(15, 23, 42, 0.16)`
- `0 1px 3px rgba(0, 0, 0, 0.04)`
- `0 1px 4px rgba(0,0,0,0.06)`
- `0 20px 34px -20px color-mix(in srgb, var(--color-brand) 35%, transparent), 0 12px 24px -20px color-mix(in srgb, var(--color-accent) 25%, tra`
- `0 20px 34px -22px color-mix(in srgb, var(--color-accent) 50%, transparent), 0 10px 20px -20px color-mix(in srgb, var(--color-brand) 20%, tra`
- `0 20px 36px -14px rgba(242, 201, 76, 0.68), 0 10px 22px -18px rgba(47, 180, 61, 0.22), inset 0 1.5px 0 rgba(255, 255, 255, 0.56), inset 0 -1`
- `0 20px 38px -28px rgba(15, 23, 42, 0.16)`
- `0 20px 40px rgba(15, 23, 42, 0.08)`
- `0 20px 46px -38px rgba(15, 23, 42, 0.14), 0 10px 22px -26px rgba(47, 148, 64, 0.14)`
- `0 20px 48px -28px rgba(15, 23, 42, 0.15), inset 0 1.5px 0 rgba(255, 255, 255, 1), 0 1px 0 rgba(255, 255, 255, 0.9)`
- `0 20px 48px -8px rgba(0, 0, 0, 0.42), 0 8px 20px -4px rgba(0, 0, 0, 0.22), inset 0 1.5px 0 rgba(255, 255, 255, 0.1), inset 0 -1px 0 rgba(0, `
- `0 22px 38px -18px rgba(242, 201, 76, 0.74), 0 12px 22px -20px rgba(47, 180, 61, 0.26), inset 0 1.5px 0 rgba(255, 255, 255, 0.52)`
- `0 22px 38px -24px color-mix(in srgb, var(--color-brand) 50%, transparent), 0 12px 26px -24px color-mix(in srgb, var(--color-accent) 40%, tra`
- `0 22px 44px -26px rgba(15, 23, 42, 0.16), 0 10px 18px -12px rgba(47, 180, 61, 0.14)`
- `0 22px 48px -28px rgba(15, 23, 42, 0.14), 0 8px 22px -18px rgba(47, 180, 61, 0.12)`
- `0 24px 34px -18px color-mix(in srgb, var(--color-accent) 55%, transparent), 0 12px 24px -22px color-mix(in srgb, var(--color-brand) 30%, tra`
- `0 24px 34px -20px rgba(242, 201, 76, 0.86), 0 14px 26px -22px rgba(47, 180, 61, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.28)`

## 12. DS13 — Cross-workspace palette (web vs mobile)

web_app token source: **65** tokens (tailwind.config + CSS vars). mobile_app token source: **0** — NONE detected (no tailwind.config / CSS-var token file).

**Root cause:** mobile_app (React Native) defines colors inline in `StyleSheet.create` blocks (**1661** inline style objects). This is a genuine DS13 gap: there is no shared token module, so brand colors are duplicated as literals across ~100 screens. Recommended fix: create `mobile_app/theme/tokens.ts` mirroring `shared/src/theme.ts` and reference it.

Web token names (sample): --color-accent, --color-accent-dark, --color-accent-light, --color-beige, --color-black, --color-blue, --color-border, --color-border-light, --color-brand, --color-brand-dark, --color-brand-light, --color-brown

## 13. DS14 — Mixed styling (CSS-in-JS)

None detected (Tailwind-only).

## 14. DS15 — Low-contrast pairs

None detected in inline styles.

## 15. DS16 — Motion durations

Distinct durations: **9** (limit ≤6). Values: 0ms, 1000ms, 120ms, 150ms, 180ms, 200ms, 300ms, 500ms, 700ms

## 16. DS17 — Unused palette tokens

Palette tokens: 88 • never referenced: 0

Inline styles by workspace: mobile_app=1661, shared=41, web_app=247
Raw px by workspace: mobile_app=1336, shared=43, web_app=1064

## 17. DS18 — Off-scale breakpoints

None.

## 18. Top files by DS score

| file | ws | score | inline | style_tag | !imp | px | off-pal | shadows | radii | css-in-js |
| `frontend/web_app/src/components/BannerCanvasEditor.tsx` | web_app | 410 | 33 | 0 | 0 | 10 | 54 | 0 | 0 | 0 |
| `frontend/web_app/src/styles/globals.css` | web_app | 357 | 0 | 0 | 0 | 899 | 57 | 81 | 19 | 0 |
| `frontend/mobile_app/app/admin/dashboard.tsx` | mobile_app | 282 | 74 | 0 | 0 | 81 | 0 | 0 | 0 | 0 |
| `frontend/web_app/src/components/admin/commandCenter/hud.tsx` | web_app | 265 | 62 | 0 | 0 | 2 | 7 | 2 | 1 | 0 |
| `frontend/mobile_app/app/(tabs)/products/index.tsx` | mobile_app | 216 | 52 | 0 | 0 | 62 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/admin/email.tsx` | mobile_app | 213 | 51 | 0 | 0 | 61 | 0 | 0 | 0 | 0 |
| `frontend/web_app/src/components/BackgroundEffect.tsx` | web_app | 193 | 33 | 0 | 0 | 26 | 16 | 2 | 0 | 0 |
| `frontend/mobile_app/app/logistics-partner/profile.tsx` | mobile_app | 181 | 46 | 0 | 0 | 43 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/logistics-partner/shipments.tsx` | mobile_app | 160 | 38 | 0 | 0 | 38 | 2 | 0 | 0 | 0 |
| `frontend/mobile_app/app/checkout.tsx` | mobile_app | 158 | 46 | 0 | 0 | 20 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/components/MobileSeasonalBanner.tsx` | mobile_app | 149 | 23 | 0 | 0 | 62 | 5 | 0 | 0 | 0 |
| `frontend/mobile_app/app/admin/analytics.tsx` | mobile_app | 146 | 40 | 0 | 0 | 26 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/invoice.tsx` | mobile_app | 142 | 33 | 0 | 0 | 43 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/logistics-partners/[id].tsx` | mobile_app | 133 | 34 | 0 | 0 | 31 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/logistics-partner/dashboard.tsx` | mobile_app | 130 | 33 | 0 | 0 | 23 | 2 | 0 | 0 | 0 |
| `frontend/mobile_app/app/suppliers/[id].tsx` | mobile_app | 125 | 36 | 0 | 0 | 17 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/supplier/documents.tsx` | mobile_app | 119 | 28 | 0 | 0 | 35 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/components/MobileBackgroundEffect.tsx` | mobile_app | 117 | 15 | 0 | 0 | 36 | 9 | 0 | 0 | 0 |
| `frontend/web_app/src/components/HeaderSearchBar.tsx` | web_app | 115 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `frontend/mobile_app/app/supplier/dashboard.tsx` | mobile_app | 114 | 27 | 0 | 0 | 33 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/supplier/bulk.tsx` | mobile_app | 110 | 31 | 0 | 0 | 17 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/admin/coupons.tsx` | mobile_app | 109 | 29 | 0 | 0 | 22 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/flash-sales.tsx` | mobile_app | 105 | 20 | 0 | 0 | 25 | 5 | 0 | 0 | 0 |
| `frontend/web_app/src/components/Header.tsx` | web_app | 104 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `frontend/web_app/src/app/supplier/upload/bg-compare/page.tsx` | web_app | 100 | 9 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| `frontend/mobile_app/app/admin/flash-sales.tsx` | mobile_app | 99 | 26 | 0 | 0 | 21 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/supplier/logistics.tsx` | mobile_app | 99 | 23 | 0 | 0 | 30 | 0 | 0 | 0 | 0 |
| `frontend/web_app/src/app/admin/treasury/_components/treasury-content.tsx` | web_app | 98 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/(tabs)/profile.tsx` | mobile_app | 97 | 21 | 0 | 0 | 34 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/supplier/credibility.tsx` | mobile_app | 95 | 25 | 0 | 0 | 16 | 1 | 0 | 0 | 0 |
| `frontend/mobile_app/app/supplier/register.tsx` | mobile_app | 95 | 28 | 0 | 0 | 11 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/(tabs)/products/[id].tsx` | mobile_app | 94 | 26 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| `frontend/web_app/src/styles/comm.css` | web_app | 92 | 0 | 0 | 0 | 63 | 3 | 3 | 4 | 0 |
| `frontend/mobile_app/app/barcode-scan.tsx` | mobile_app | 91 | 23 | 0 | 0 | 22 | 0 | 0 | 0 | 0 |
| `frontend/mobile_app/app/logistics-partner/scan.tsx` | mobile_app | 90 | 24 | 0 | 0 | 14 | 1 | 0 | 0 | 0 |
| `frontend/mobile_app/app/tracking/[id].tsx` | mobile_app | 87 | 22 | 0 | 0 | 21 | 0 | 0 | 0 | 0 |
| `frontend/web_app/src/components/FilterSearchBar.tsx` | web_app | 87 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `frontend/shared/src/components/ui/ErrorBoundary.tsx` | shared | 86 | 11 | 0 | 0 | 21 | 8 | 0 | 0 | 0 |
| `frontend/mobile_app/app/supplier/products/new.tsx` | mobile_app | 85 | 21 | 0 | 0 | 22 | 0 | 0 | 0 | 0 |
| `frontend/web_app/src/components/banner-effects.css` | web_app | 78 | 0 | 1 | 0 | 23 | 4 | 3 | 4 | 0 |