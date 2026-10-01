# ZOZI Frontend Design — Line-by-Line Implementation Plan

> **Document purpose:** A copy-paste-ready, line-to-line plan for modernizing the ZOZI frontend design. Every action states exact file path, exact line numbers, exact old text, exact new text, and exact validation command. No guessing required.
>
> **Scope:** 12,500+ lines across `frontend/web_app` and `frontend/shared`. Covers CSS restoration, token reconciliation, component consolidation, motion modernization, and visual polish.
>
> **Execution order:** Phase 0 → 1 → 2 → 3 → 4 → 5. Phases 0, 1, 3 are low-risk and can ship quickly. Phase 2 is the long pole (migrate per-PR).

---

## Phase 0 — Restore + Wire (close concrete gap)

These 4 CSS files exist verbatim at `HEAD` but are deleted from the working tree. The red test `designSystemTokens.test.ts` requires them.

### 0.1 Restore the 4 CSS files verbatim from HEAD

Run these 4 commands in `frontend/web_app`:

```bash
cd frontend/web_app
git show HEAD:src/styles/comm.css         > src/styles/comm.css
git show HEAD:src/styles/panel-modern.css > src/styles/panel-modern.css
git show HEAD:src/styles/glow.css         > src/styles/glow.css
git show HEAD:src/styles/tokens.css       > src/styles/tokens.css
```

**Verify:**
- `src/styles/comm.css`         → 292 lines
- `src/styles/panel-modern.css`  → 74 lines
- `src/styles/glow.css`          → 43 lines
- `src/styles/tokens.css`        → 246 lines

### 0.2 Wire `tokens.css` into `globals.css`

**File:** `frontend/web_app/src/styles/globals.css`

**Current line 1–2:**
```css
1: @import "tailwindcss";
2: 
```

**Replace lines 1–2 with:**
```css
1: @import "tailwindcss";
2: @import "./tokens.css";
3: 
```

### 0.3 Wire `tokens.css` + `glow.css` into `layout.tsx`

**File:** `frontend/web_app/src/app/layout.tsx`

**Current lines 4–5:**
```tsx
4: import "@/styles/globals.css";
5: import { AuthProvider } from "@/lib/useAuth";
```

**Replace lines 4–5 with:**
```tsx
4: import "@/styles/globals.css";
5: import "@/styles/tokens.css";
6: import "@/styles/glow.css";
7: import { AuthProvider } from "@/lib/useAuth";
```

### 0.4 Delete orphan `variables.css`

**File:** `frontend/web_app/src/styles/variables.css` (90 lines, orange/purple palette, conflicts with brand lime/gold, imported nowhere)

```bash
rm frontend/web_app/src/styles/variables.css
```

### 0.5 Validate Phase 0

```bash
cd frontend/web_app
npx jest src/__tests__/designSystemTokens.test.ts
```

**Expected:** All 9 assertions pass. The test at line 12 previously threw `ENOENT tokens.css`; after 0.1 that error is gone. Assertions at lines 17, 21, 55–59, 61–65 will also pass after 0.2.

---

## Phase 1 — Token Foundation Reconciliation

Goal: Make `theme.ts`, `globals.css`, and `tailwind.config.js` share one source of truth.

### 1.1 Make status/semantic/glass/gradient vars theme-aware

**File:** `frontend/shared/src/theme.ts`

**Current lines 177–205 (`applyCssTheme` function):**
```ts
177: export function applyCssTheme(theme: ColorTheme) {
178:   const root = (globalThis as any).document?.documentElement;
179:   if (!root) return;
180:   const colors = palette(theme);
181: 
182:   root.style.setProperty("--color-brand", brand.primary);
183:   root.style.setProperty("--color-brand-light", brand.primaryLight);
184:   root.style.setProperty("--color-brand-dark", brand.primaryDark);
185:   root.style.setProperty("--color-accent", brand.accent);
186:   root.style.setProperty("--color-accent-light", brand.accentLight);
187: 
188:   root.style.setProperty("--color-surface-0", colors.surface0);
189:   root.style.setProperty("--color-surface-1", colors.surface1);
190:   root.style.setProperty("--color-surface-2", colors.surface2);
191:   root.style.setProperty("--color-surface-3", colors.surface3);
192:   root.style.setProperty("--color-border", colors.border);
193:   root.style.setProperty("--color-border-light", colors.borderLight);
194:   root.style.setProperty("--color-text", colors.text);
195:   root.style.setProperty("--color-text-muted", colors.textMuted);
196:   root.style.setProperty("--color-text-faint", colors.textFaint);
197:   root.style.setProperty("--color-on-brand", colors.onBrand ?? "#ffffff");
198:   root.style.setProperty("--color-on-accent", colors.onAccent ?? "#000000");
199:   root.style.setProperty("--color-on-warning", colors.onWarning ?? "#1a1a1a");
200: 
201:   root.classList.remove("light", "dark");
202:   root.classList.add(theme);
203:   root.style.colorScheme = theme;
204: }
```

**Replace lines 197–199 (the on-color block) and insert status/glass vars after line 199, before the classList block:**

```ts
197:   root.style.setProperty("--color-on-brand", colors.onBrand ?? "#ffffff");
198:   root.style.setProperty("--color-on-accent", colors.onAccent ?? "#000000");
199:   root.style.setProperty("--color-on-warning", colors.onWarning ?? "#1a1a1a");
200: 
201:   root.style.setProperty("--color-success", status.success);
202:   root.style.setProperty("--color-danger", status.danger);
203:   root.style.setProperty("--color-warning", status.warning);
204:   root.style.setProperty("--color-info", status.info);
205:   root.style.setProperty("--color-accent-dark", brand.accentDark ?? "#C09000");
206: 
207:   root.style.setProperty("--color-glass-base", "color-mix(in srgb, " + colors.surface0 + " 60%, transparent)");
208:   root.style.setProperty("--color-glass-panel", "color-mix(in srgb, " + colors.surface1 + " 84%, transparent)");
209:   root.style.setProperty("--color-glass-border", colors.borderLight);
210: 
211:   root.classList.remove("light", "dark");
212:   root.classList.add(theme);
213:   root.style.colorScheme = theme;
```

### 1.2 Add font-size tokens for `text-[10px]…[7px]` arbitrarys

**File:** `frontend/web_app/tailwind.config.js`

**Current lines 72–85 (`fontSize` block):**
```js
72:       fontSize: {
73:         "2xs": ["0.625rem", { lineHeight: "1rem" }],
74:         xs: ["0.75rem", { lineHeight: "1.125rem" }],
75:         sm: ["0.875rem", { lineHeight: "1.375rem" }],
76:         base: ["1rem", { lineHeight: "1.625rem" }],
77:         lg: ["1.125rem", { lineHeight: "1.75rem" }],
78:         xl: ["1.25rem", { lineHeight: "1.875rem" }],
79:         "2xl": ["1.5rem", { lineHeight: "2rem" }],
80:         "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
81:         "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
82:         "5xl": ["3rem", { lineHeight: "1.15" }],
83:         "6xl": ["3.75rem", { lineHeight: "1.1" }],
84:         display: ["clamp(2.5rem,6vw,4.5rem)", { lineHeight: "1.1" }],
85:       },
```

**Replace lines 72–85 with:**
```js
72:       fontSize: {
73:         "2xs": ["0.625rem", { lineHeight: "1rem" }],
74:         "3xs": ["0.5625rem", { lineHeight: "0.875rem" }],
75:         "4xs": ["0.5rem", { lineHeight: "0.75rem" }],
76:         "5xs": ["0.4375rem", { lineHeight: "0.625rem" }],
77:         xs: ["0.75rem", { lineHeight: "1.125rem" }],
78:         sm: ["0.875rem", { lineHeight: "1.375rem" }],
79:         base: ["1rem", { lineHeight: "1.625rem" }],
80:         lg: ["1.125rem", { lineHeight: "1.75rem" }],
81:         xl: ["1.25rem", { lineHeight: "1.875rem" }],
82:         "2xl": ["1.5rem", { lineHeight: "2rem" }],
83:         "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
84:         "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
85:         "5xl": ["3rem", { lineHeight: "1.15" }],
86:         "6xl": ["3.75rem", { lineHeight: "1.1" }],
87:         display: ["clamp(2.5rem,6vw,4.5rem)", { lineHeight: "1.1" }],
88:       },
```

### 1.3 Add a named z-index scale

**File:** `frontend/web_app/tailwind.config.js`

**Current lines 194–202 (`zIndex` block):**
```js
194:       zIndex: {
195:         60: "60",
196:         70: "70",
197:         80: "80",
198:         90: "90",
199:         100: "100",
200:         1200: "1200",
201:         1201: "1201",
202:       },
```

**Replace lines 194–202 with:**
```js
194:       zIndex: {
195:         header: "50",
196:         dropdown: "1000",
197:         sticky: "1020",
198:         overlay: "1040",
199:         modal: "1050",
200:         popover: "1060",
201:         tooltip: "1070",
202:         toast: "1080",
203:       },
```

### 1.4 Add `max-w-450` (used by PanelShell)

**File:** `frontend/web_app/tailwind.config.js`

**Current lines 205–210 (`maxWidth` block):**
```js
205:       maxWidth: {
206:         "8xl": "88rem",
207:         "9xl": "96rem",
208:         "10xl": "120rem",
209:         "11xl": "140rem",
210:       },
```

**Replace lines 205–210 with:**
```js
205:       maxWidth: {
206:         "8xl": "88rem",
207:         "9xl": "96rem",
208:         "10xl": "120rem",
209:         "11xl": "140rem",
210:         450: "22.5rem",
211:       },
```

### 1.5 Add `gradient-brand-to-*` background images

**File:** `frontend/web_app/tailwind.config.js`

**Current lines 127–136 (`backgroundImage` block):**
```js
127:       backgroundImage: {
128:         "gradient-primary": "var(--gradient-banner)",
129:         "gradient-accent": "var(--gradient-banner-alt)",
130:         "gradient-hero": "var(--gradient-hero)",
131:         "gradient-logo": "var(--gradient-logo)",
132:         "gradient-card": "var(--gradient-card)",
133:         "gradient-radial": "radial-gradient(ellipse at center, var(--tw-gradient-stops))",
134:         "gradient-text": "var(--gradient-brand-text)",
135:         "gradient-logo-text": "var(--gradient-logo-text)",
136:       },
```

**Replace lines 127–136 with:**
```js
127:       backgroundImage: {
128:         "gradient-primary": "var(--gradient-banner)",
129:         "gradient-accent": "var(--gradient-banner-alt)",
130:         "gradient-hero": "var(--gradient-hero)",
131:         "gradient-logo": "var(--gradient-logo)",
132:         "gradient-card": "var(--gradient-card)",
133:         "gradient-radial": "radial-gradient(ellipse at center, var(--tw-gradient-stops))",
134:         "gradient-text": "var(--gradient-brand-text)",
135:         "gradient-logo-text": "var(--gradient-logo-text)",
136:         "gradient-brand-to-success": "var(--gradient-brand-to-success)",
137:         "gradient-brand-to-brand-dark": "var(--gradient-brand-to-brand-dark)",
138:         "gradient-brand-to-brand-light": "var(--gradient-brand-to-brand-light)",
139:       },
```

### 1.6 Add `borderRadius` token mapping

**File:** `frontend/web_app/tailwind.config.js`

**Current lines 100–109 (`borderRadius` block):**
```js
100:       borderRadius: {
101:         sm: "0.375rem",
102:         md: "0.5rem",
103:         lg: "0.75rem",
104:         xl: "1rem",
105:         "2xl": "1.25rem",
106:         "3xl": "1.5rem",
107:         "4xl": "2rem",
108:         pill: "9999px",
109:       },
```

**Replace lines 100–109 with:**
```js
100:       borderRadius: {
101:         sm: "var(--zozi-radius-sm)",
102:         md: "var(--zozi-radius-md)",
103:         lg: "var(--zozi-radius-lg)",
104:         xl: "var(--zozi-radius-xl)",
105:         "2xl": "var(--zozi-radius-2xl)",
106:         "3xl": "1.5rem",
107:         "4xl": "2rem",
108:         pill: "var(--zozi-radius-pill)",
109:       },
```

### 1.7 Add `transitionDuration` token mapping

**File:** `frontend/web_app/tailwind.config.js`

**Current lines 144–148 (`transitionDuration` block):**
```js
144:       transitionDuration: {
145:         250: "250ms",
146:         350: "350ms",
147:         400: "400ms",
148:       },
```

**Replace lines 144–148 with:**
```js
144:       transitionDuration: {
145:         fast: "var(--zozi-duration-fast)",
146:         base: "var(--zozi-duration-base)",
147:         normal: "var(--zozi-duration-normal)",
148:         slow: "var(--zozi-duration-slow)",
149:         slower: "var(--zozi-duration-slower)",
150:         slowest: "var(--zozi-duration-slowest)",
151:         250: "250ms",
152:         350: "350ms",
153:         400: "400ms",
154:       },
```

### 1.8 Kill dead keyframes in `globals.css`

**File:** `frontend/web_app/src/styles/globals.css`

**Delete lines 2004–2012 (dead `fadeIn` and `slideUp` keyframes — framer-motion owns all entrance animations):**

```bash
# Remove fadeIn (lines 2004-2007) and slideUp (lines 2009-2012)
# After removal, the file should go from line 2003 directly to @keyframes float at line 2014
```

**Current lines 2003–2014:**
```css
2003: }
2004: 
2005: @keyframes fadeIn {
2006:   from { opacity: 0; }
2007:   to { opacity: 1; }
2008: }
2009: 
2010: @keyframes slideUp {
2011:   from { transform: translateY(12px); opacity: 0; }
2012:   to { transform: translateY(0); opacity: 1; }
2013: }
2014: 
2015: @keyframes float {
```

**Replace lines 2003–2014 with:**
```css
2003: }
2004: 
2005: @keyframes float {
```

### 1.9 Add `@keyframes scaleIn` to `globals.css` (currently missing, but Tailwind config references it)

**File:** `frontend/web_app/src/styles/globals.css`

**Insert after line 2002 (after the `shimmer` keyframe, before `fadeIn` which we just deleted):**

```css
@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to   { transform: scale(1);    opacity: 1; }
}
```

**Exact insertion point:** between line 2002 (`}` closing shimmer) and line 2003 (`}` closing the block before fadeIn).

### 1.10 Add missing button classes to `globals.css`

**File:** `frontend/web_app/src/styles/globals.css`

These classes are referenced by `ui/Button.tsx:36-37` (`theme-btn-danger`, `theme-btn-danger-outline`) and `ui/Button.tsx:34` (`theme-btn-secondary`) but are missing or incomplete.

**A) Add `.theme-btn-danger` after line 319 (after `.theme-btn-accent`):**

**Current lines 308–319:**
```css
308: .theme-btn-accent {
309:   display: inline-flex;
310:   align-items: center;
311:   justify-content: center;
312:   background: linear-gradient(135deg, color-mix(in srgb, var(--color-brand-light) 12%, var(--color-accent-light)) 0%, var(--color-accent) 54%, color-mix(in srgb, var(--color-brand) 14%, var(--color-accent-dark)) 100%);
313:   color: var(--color-on-accent);
314:   padding: 0.48rem 0.98rem;
315:   border-radius: 0.75rem;
316:   box-shadow: 0 18px 30px -22px rgba(242, 201, 76, 0.72), 0 10px 22px -20px rgba(47, 180, 61, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.24);
317:   border: 1px solid color-mix(in srgb, var(--color-accent-light) 42%, rgba(255, 255, 255, 0.14));
318:   transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
319: }
```

**Insert after line 319:**
```css
.theme-btn-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: #ffffff;
  padding: 0.5rem 1rem;
  border-radius: 0.75rem;
  box-shadow: 0 18px 32px -22px rgba(239, 68, 68, 0.5), 0 10px 24px -20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.35);
  transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
}
.theme-btn-danger:hover,
.theme-btn-danger:focus {
  transform: translateY(-2px);
  box-shadow: 0 24px 36px -22px rgba(239, 68, 68, 0.6), 0 14px 28px -24px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  filter: saturate(1.05);
}
.light .theme-btn-danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 12px 20px -16px rgba(239, 68, 68, 0.4), 0 8px 16px -18px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
```

**B) Add `.theme-btn-danger-outline` after the `.theme-btn-danger` block:**

```css
.theme-btn-danger-outline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #ef4444;
  padding: 0.5rem 1rem;
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid rgba(239, 68, 68, 0.4);
  transition: transform 120ms ease, box-shadow 120ms ease, background-color 120ms ease;
}
.theme-btn-danger-outline:hover,
.theme-btn-danger-outline:focus {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.7);
  transform: translateY(-1px);
}
.light .theme-btn-danger-outline {
  color: #dc2626;
  border-color: rgba(220, 38, 38, 0.45);
}
.light .theme-btn-danger-outline:hover {
  background: rgba(220, 38, 38, 0.06);
}
```

**C) Add `.theme-btn-secondary` at the top level (outside `@layer utilities`) — currently only defined inside `@layer utilities` at line 978:**

**Current line 278 (base `.theme-btn-primary` definition):**
```css
278: .theme-btn-primary {
```

**Insert BEFORE line 278 (before the base `.theme-btn-primary`):**
```css
.theme-btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, color-mix(in srgb, var(--color-surface-1) 96%, transparent), color-mix(in srgb, var(--color-surface-2) 90%, transparent));
  color: var(--color-text);
  padding: 0.5rem 1rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border);
  box-shadow: 0 12px 24px -24px rgba(15, 23, 42, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.16);
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease, transform 0.12s ease;
}
.theme-btn-secondary:hover {
  border-color: color-mix(in srgb, var(--color-brand) 50%, var(--color-border));
  background-color: var(--color-surface-2);
  box-shadow: 0 18px 28px -24px rgba(15, 23, 42, 0.45), 0 8px 18px -20px rgba(47, 180, 61, 0.18);
  transform: translateY(-1px);
}
.light .theme-btn-secondary {
  background: linear-gradient(180deg, rgba(245, 247, 239, 0.96), rgba(237, 241, 229, 0.92));
  border-color: var(--color-border);
}
```

### 1.11 Replace focus-kill block with focus-visible ring

**File:** `frontend/web_app/src/styles/globals.css`

**Current lines 2255–2271:**
```css
2255: /* -- Focus / Focus Visible (only for interactive controls) --------------------- */
2256: button:focus,
2257: button:focus-visible,
2258: a:focus,
2259: a:focus-visible,
2260: input:focus,
2261: input:focus-visible,
2262: select:focus,
2263: select:focus-visible,
2264: textarea:focus,
2265: textarea:focus-visible,
2266: [tabindex]:focus,
2267: [tabindex]:focus-visible {
2268:   outline: none;
2269:   box-shadow: none;
2270:   border-color: transparent;
2271: }
```

**Replace lines 2255–2271 with:**
```css
/* -- Focus / Focus Visible (keyboard-only ring) -------------------------------- */
button:focus,
a:focus,
input:focus,
select:focus,
textarea:focus,
[tabindex]:focus {
  outline: none;
}
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
[tabindex]:focus-visible {
  outline: 2px solid var(--color-brand);
  outline-offset: 2px;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-brand) 28%, transparent);
}
```

### 1.12 Add `--color-background` definition (referenced in 49 files)

**File:** `frontend/web_app/src/styles/globals.css`

**Current lines 28–49 (`:root` brand/surface vars):**
```css
28: :root {
29:   --zozi-logo-z-top: #EEFF99;
...
43:   --color-brand: #32CD32;
44:   --color-brand-light: #7CFC00;
45:   --color-brand-dark: #228B22;
46:   --color-accent: #FFD700;
47:   --color-accent-light: #FFEA00;
48:   --color-accent-dark: #C09000;
49:   --color-surface-0: #000000;
```

**Insert after line 49:**
```css
  --color-background: var(--color-surface-0);
```

### 1.13 Add `@keyframes scaleIn` to `globals.css` (if not already added in 1.9)

Already covered in 1.9.

### 1.14 Manual z-index fixes for remaining `z-[200]` / `z-200` usages in live components

Four live files still use raw `z-[200]` or `z-200`. Fix them individually:

**File:** `frontend/web_app/src/components/ToastContainer.tsx`

**Current line 37:**
```tsx
37:     <div className="fixed top-4 right-4 flex flex-col gap-1.5 z-200">
```

**Replace line 37 with:**
```tsx
37:     <div className="fixed top-4 right-4 flex flex-col gap-1.5 z-toast">
```

**File:** `frontend/web_app/src/components/AuthRequiredModal.tsx`

**Current line 165:**
```tsx
165:           className="fixed inset-0 z-[200] flex items-center justify-center p-4"
```

**Replace line 165 with:**
```tsx
165:           className="fixed inset-0 z-modal flex items-center justify-center p-4"
```

**File:** `frontend/web_app/src/components/MobileSearchOverlay.tsx`

**Current line 322:**
```tsx
322:             className="fixed inset-0 z-[200] bg-black/40 backdrop-blur-sm"
```

**Replace line 322 with:**
```tsx
322:             className="fixed inset-0 z-overlay bg-black/40 backdrop-blur-sm"
```

**File:** `frontend/web_app/src/components/SizeGuide.tsx`

**Current line 57:**
```tsx
57:         <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
```

**Replace line 57 with:**
```tsx
57:         <div className="fixed inset-0 z-modal flex items-center justify-center p-4">
```

### 1.15 Validate Phase 1

```bash
cd frontend/web_app
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest src/__tests__/designSystemTokens.test.ts
```

**Expected:** Zero type errors, lint passes, all 9 token test assertions pass.

---

## Phase 2 — Component System Consolidation

Goal: Make `components/ui/` the **only** way to render buttons, modals, toasts, cards, inputs.

### 2.1 Create `components/ui/index.ts` barrel export

**New file:** `frontend/web_app/src/components/ui/index.ts`

```ts
export { Button, type ButtonProps, type ButtonVariant, type ButtonSize } from "./Button";
export { Card, CardHeader, CardContent, CardFooter } from "./Card";
export { GlassCard, GlassCardHeader, GlassCardContent, GlassCardFooter } from "./GlassCard";
export { Dropdown } from "./Dropdown";
export { FormLayout, FormInput, FormSelect, FormTextarea, FormCheckbox } from "./FormLayout";
export { StatCard } from "./StatCard";
export { Modal, ModalFooter } from "./shared/Modal";
export { Table, TableHeader, TableBody, TableRow, TableCell, TableHead } from "./shared/Table";
export { Badge, StatusBadge } from "./shared/Badge";
export { LoadingSkeleton, LoadingCard, LoadingTable } from "./shared/LoadingSkeleton";
export { EmptyState } from "./shared/EmptyState";
```

### 2.2 Extend `Modal.tsx` with Drawer variant + a11y props

**File:** `frontend/web_app/src/components/ui/shared/Modal.tsx`

**Current lines 7–17 (ModalProps interface):**
```tsx
7: export interface ModalProps {
8:   isOpen: boolean;
9:   onClose: () => void;
10:   title?: string;
11:   children: React.ReactNode;
12:   size?: "sm" | "md" | "lg" | "xl";
13:   showCloseButton?: boolean;
14:   className?: string;
15:   bodyClassName?: string;
16:   overlayClassName?: string;
17: }
```

**Replace lines 7–17 with:**
```tsx
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  showCloseButton?: boolean;
  className?: string;
  bodyClassName?: string;
  overlayClassName?: string;
  variant?: "modal" | "drawer";
  closeOnEscape?: boolean;
  lockScroll?: boolean;
  initialFocusRef?: React.RefObject<HTMLElement>;
}
```

**Current lines 19–30 (Modal function signature + useEffect):**
```tsx
19: export const Modal = forwardRef<HTMLDivElement, ModalProps>(
20:   ({ 
21:     isOpen, 
22:     onClose, 
23:     title,
24:     children, 
25:     size = "md", 
26:     showCloseButton = true,
27:     className,
28:     bodyClassName,
29:     overlayClassName,
30:   }, ref) => {
31:     // Close on Escape and lock background scroll while open.
32:     useEffect(() => {
33:       if (!isOpen) return;
34:       const onKey = (event: KeyboardEvent) => {
35:         if (event.key === "Escape") onClose();
36:       };
37:       window.addEventListener("keydown", onKey);
38:       const prevOverflow = document.body.style.overflow;
39:       document.body.style.overflow = "hidden";
40:       return () => {
41:         window.removeEventListener("keydown", onKey);
42:         document.body.style.overflow = prevOverflow;
43:       };
44:     }, [isOpen, onClose]);
```

**Replace lines 19–44 with:**
```tsx
export const Modal = forwardRef<HTMLDivElement, ModalProps>(
  ({ 
    isOpen, 
    onClose, 
    title,
    children, 
    size = "md", 
    showCloseButton = true,
    className,
    bodyClassName,
    overlayClassName,
    variant = "modal",
    closeOnEscape = true,
    lockScroll = true,
    initialFocusRef,
  }, ref) => {
    // Close on Escape and lock background scroll while open.
    useEffect(() => {
      if (!isOpen) return;
      if (closeOnEscape) {
        const onKey = (event: KeyboardEvent) => {
          if (event.key === "Escape") onClose();
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
      }
    }, [isOpen, onClose, closeOnEscape]);

    useEffect(() => {
      if (!isOpen || !lockScroll) return;
      const prevOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => { document.body.style.overflow = prevOverflow; };
    }, [isOpen, lockScroll]);

    useEffect(() => {
      if (!isOpen || !initialFocusRef?.current) return;
      initialFocusRef.current.focus();
    }, [isOpen, initialFocusRef]);
```

**Current lines 48–53 (`sizeClasses`):**
```tsx
48:     const sizeClasses = {
49:       sm: "max-w-sm",
50:       md: "max-w-md",
51:       lg: "max-w-lg",
52:       xl: "max-w-2xl",
53:     };
```

**Replace lines 48–53 with:**
```tsx
    const isDrawer = variant === "drawer";
    const sizeClasses = {
      sm: isDrawer ? "w-80" : "max-w-sm",
      md: isDrawer ? "w-96" : "max-w-md",
      lg: isDrawer ? "w-[28rem]" : "max-w-lg",
      xl: isDrawer ? "w-[32rem]" : "max-w-2xl",
    };
```

**Current lines 55–75 (overlay + panel markup):**
```tsx
55:     return (
56:       <div 
57:         className={cn(
58:           "fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4",
59:           "animate-fade-in",
60:           overlayClassName
61:         )}
62:         onClick={onClose}
63:         role="dialog"
64:         aria-modal="true"
65:         aria-labelledby={title ? "modal-title" : undefined}
66:       >
67:         <div 
68:           ref={ref}
69:           className={cn(
70:             "glass-panel border rounded-xl shadow-2xl max-h-[80vh] overflow-y-auto",
71:             "animate-scale-in",
72:             sizeClasses[size],
73:             className
74:           )}
75:           onClick={(e) => e.stopPropagation()}
76:         >
```

**Replace lines 55–76 with:**
```tsx
    return (
      <div 
        className={cn(
          "fixed inset-0 z-modal flex items-center justify-center theme-overlay p-4",
          "animate-fade-in",
          isDrawer && "items-end sm:items-center",
          overlayClassName
        )}
        onClick={onClose}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? "modal-title" : undefined}
      >
        <div 
          ref={ref}
          className={cn(
            "glass-panel border rounded-xl shadow-2xl max-h-[80vh] overflow-y-auto",
            "animate-scale-in",
            sizeClasses[size],
            isDrawer && "rounded-b-none sm:rounded-b-xl sm:rounded-t-none",
            className
          )}
          onClick={(e) => e.stopPropagation()}
        >
```

### 2.3 Delete dead `ToastSystem.tsx`

**File:** `frontend/web_app/src/components/ToastSystem.tsx` (85 lines, imported nowhere, exports a component named `ToastContainer` which collides with the real one)

```bash
rm frontend/web_app/src/components/ToastSystem.tsx
```

### 2.4 Unify LoadingSkeleton — keep ui version, delete root duplicate

**Keep:** `frontend/web_app/src/components/ui/shared/LoadingSkeleton.tsx` (63 lines, already canonical)

**Delete:** `frontend/web_app/src/components/LoadingSkeleton.tsx` (if it exists as a root-level duplicate)

```bash
# Verify it exists and is a duplicate before deleting
ls frontend/web_app/src/components/LoadingSkeleton.tsx
# If confirmed duplicate:
rm frontend/web_app/src/components/LoadingSkeleton.tsx
```

### 2.5 Add `Container`, `PageHeader`, `Section`, `Heading` primitives

**New file:** `frontend/web_app/src/components/ui/Container.tsx`

```tsx
"use client";

import { cn } from "@/lib/utils";

type ContainerWidth = "wide" | "default" | "narrow" | "full";

interface ContainerProps {
  children: React.ReactNode;
  width?: ContainerWidth;
  className?: string;
  as?: "div" | "section" | "main";
}

const widthClasses: Record<ContainerWidth, string> = {
  wide: "max-w-[1400px]",
  default: "max-w-[1200px]",
  narrow: "max-w-[880px]",
  full: "max-w-none",
};

export function Container({ children, width = "default", className, as = "div" }: ContainerProps) {
  const Component = as;
  return (
    <Component className={cn("mx-auto w-full px-4 sm:px-6 lg:px-8", widthClasses[width], className)}>
      {children}
    </Component>
  );
}
```

**New file:** `frontend/web_app/src/components/ui/PageHeader.tsx`

```tsx
"use client";

import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, action, className }: PageHeaderProps) {
  return (
    <div className={cn("flex items-start justify-between gap-4 mb-6", className)}>
      <div>
        <h1 className="text-2xl font-bold text-text">{title}</h1>
        {description && <p className="mt-1 text-sm text-text-muted">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
```

**New file:** `frontend/web_app/src/components/ui/Section.tsx`

```tsx
"use client";

import { cn } from "@/lib/utils";

interface SectionProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  className?: string;
  contentClassName?: string;
}

export function Section({ children, title, description, className, contentClassName }: SectionProps) {
  return (
    <section className={cn("mb-8", className)}>
      {(title || description) && (
        <div className="mb-4">
          {title && <h2 className="text-lg font-semibold text-text">{title}</h2>}
          {description && <p className="mt-1 text-sm text-text-muted">{description}</p>}
        </div>
      )}
      <div className={cn(contentClassName)}>{children}</div>
    </section>
  );
}
```

**New file:** `frontend/web_app/src/components/ui/Heading.tsx`

```tsx
"use client";

import { cn } from "@/lib/utils";

type HeadingLevel = 1 | 2 | 3 | 4;

const levelClasses: Record<HeadingLevel, string> = {
  1: "text-4xl font-extrabold tracking-tight text-text",
  2: "text-2xl font-bold text-text",
  3: "text-xl font-semibold text-text",
  4: "text-lg font-medium text-text",
};

interface HeadingProps {
  level: HeadingLevel;
  children: React.ReactNode;
  className?: string;
  id?: string;
}

export function Heading({ level, children, className, id }: HeadingProps) {
  const Tag = `h${level}` as keyof JSX.IntrinsicElements;
  return <Tag className={cn(levelClasses[level], className)} id={id}>{children}</Tag>;
}
```

### 2.6 Add `Alert` primitive

**New file:** `frontend/web_app/src/components/ui/Alert.tsx`

```tsx
"use client";

import { cn } from "@/lib/utils";
import { AlertCircle, CheckCircle, Info, AlertTriangle } from "lucide-react";

type AlertTone = "success" | "danger" | "warning" | "info";

const toneConfig: Record<AlertTone, { bg: string; border: string; text: string; Icon: React.ComponentType<{ className?: string }> }> = {
  success: {
    bg: "bg-success/10",
    border: "border-success/30",
    text: "text-success",
    Icon: CheckCircle,
  },
  danger: {
    bg: "bg-danger/10",
    border: "border-danger/30",
    text: "text-danger",
    Icon: AlertCircle,
  },
  warning: {
    bg: "bg-warning/10",
    border: "border-warning/30",
    text: "text-warning",
    Icon: AlertTriangle,
  },
  info: {
    bg: "bg-info/10",
    border: "border-info/30",
    text: "text-info",
    Icon: Info,
  },
};

interface AlertProps {
  tone: AlertTone;
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Alert({ tone, title, children, className }: AlertProps) {
  const config = toneConfig[tone];
  const Icon = config.Icon;
  return (
    <div className={cn("flex items-start gap-3 rounded-xl border p-4", config.bg, config.border, className)}>
      <Icon className={cn("h-5 w-5 shrink-0 mt-0.5", config.text)} />
      <div className="flex-1">
        {title && <p className={cn("text-sm font-semibold", config.text)}>{title}</p>}
        <p className="text-sm text-text-muted">{children}</p>
      </div>
    </div>
  );
}
```

### 2.7 Add `StatusBadge` primitive

**New file:** `frontend/web_app/src/components/ui/StatusBadge.tsx`

```tsx
"use client";

import { cn } from "@/lib/utils";
import { status } from "@zozi/shared";

type StatusKey = keyof typeof status;

const dotColors: Record<StatusKey, string> = {
  success: "bg-success",
  danger: "bg-danger",
  warning: "bg-warning",
  info: "bg-info",
};

interface StatusBadgeProps {
  status: StatusKey;
  label: string;
  className?: string;
}

export function StatusBadge({ status: statusKey, label, className }: StatusBadgeProps) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border border-glass-border-mid bg-glass-base", className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", dotColors[statusKey])} />
      {label}
    </span>
  );
}
```

### 2.8 Add `Spinner` primitive

**New file:** `frontend/web_app/src/components/ui/Spinner.tsx`

```tsx
"use client";

import { cn } from "@/lib/utils";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-8 w-8 border-3",
};

export function Spinner({ size = "md", className }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn("animate-spin rounded-full border-current border-t-transparent text-brand", sizeClasses[size], className)}
    />
  );
}
```

### 2.9 Delete dead `variables.css` (if not already deleted in 0.4)

Already covered in Phase 0.

### 2.10 Validate Phase 2

```bash
cd frontend/web_app
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest
```

**Expected:** Zero type errors, lint passes, all tests pass, new primitives importable from `@/components/ui`.

---

## Phase 3 — Motion Modernization

### 3.1 Wrap app in `<MotionConfig reducedMotion="user">`

**File:** `frontend/web_app/src/app/layout.tsx`

**Step 1 — Add import after line 3:**

**Current line 3:**
```tsx
3: import { Suspense } from "react";
```

**Replace line 3 with:**
```tsx
3: import { Suspense } from "react";
4: import { MotionConfig } from "framer-motion";
```

**Step 2 — Wrap the app-frame div (lines 97–118):**

**Current lines 97–118:**
```tsx
97:               <div className="relative" data-app-frame style={{ isolation: "isolate", zIndex: 10 }}>
98:                 <LocaleInit />
99:                 <CurrencyInit />
100:                <ErrorHandlerInit />
101:                <UserRealtimeBridge />
102:                <div data-app-header>
103:                  <Header />
104:                </div>
105:                <div data-app-body>
106:                  <ErrorBoundary>
107:                    {children}
108:                  </ErrorBoundary>
109:                </div>
110:                <div data-app-footer>
111:                  <Footer />
112:                </div>
113:                <AuthRequiredModal />
114:                <Suspense fallback={null}>
115:                  <Chatbot />
116:                </Suspense>
117:                <ToastContainer />
118:              </div>
```

**Wrap lines 97–118 in `<MotionConfig>`:**

```tsx
97:               <MotionConfig reducedMotion="user">
98:                 <div className="relative" data-app-frame style={{ isolation: "isolate", zIndex: 10 }}>
99:                   <LocaleInit />
100:                  <CurrencyInit />
101:                  <ErrorHandlerInit />
102:                  <UserRealtimeBridge />
103:                  <div data-app-header>
104:                    <Header />
105:                  </div>
106:                  <div data-app-body>
107:                    <ErrorBoundary>
108:                      {children}
109:                    </ErrorBoundary>
110:                  </div>
111:                  <div data-app-footer>
112:                    <Footer />
113:                  </div>
114:                  <AuthRequiredModal />
115:                  <Suspense fallback={null}>
116:                    <Chatbot />
117:                  </Suspense>
118:                  <ToastContainer />
119:                </div>
120:              </MotionConfig>
```

### 3.2 Add `app/template.tsx` for page transitions

**New file:** `frontend/web_app/src/app/template.tsx`

```tsx
"use client";

import { motion } from "framer-motion";

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
```

### 3.3 Promote `PanelPage.tsx` motion variants to `Reveal` + `Stagger`

**Current PanelPage motion exports (lines 14–46):**
```tsx
14: export const ENTER_VARIANTS = {
15:   hidden: { opacity: 0, y: 12 },
16:   visible: (i: number = 0) => ({
17:     opacity: 1,
18:     y: 0,
19:     transition: { duration: 0.28, delay: i * 0.04, ease: [0.22, 1, 0.36, 1] },
20:   }),
21: };
22: 
23: export const FADE_SCALE = {
24:   hidden: { opacity: 0, scale: 0.96 },
25:   visible: {
26:     opacity: 1,
27:     scale: 1,
28:     transition: { duration: 0.2, ease: "easeOut" },
29:   },
30:   exit: {
31:     opacity: 0,
32:     scale: 0.96,
33:     transition: { duration: 0.15, ease: "easeIn" },
34:   },
35: };
36: 
37: export const staggerItems = (delay: number = 0.04) => ({
38:   hidden: {},
39:   visible: {
40:     transition: {
41:       staggerChildren: delay,
42:     },
43:   },
44: });
```

**New file:** `frontend/web_app/src/components/ui/Reveal.tsx`

```tsx
"use client";

import { motion, type Variants } from "framer-motion";

export const ENTER_VARIANTS: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.28, delay: i * 0.04, ease: [0.22, 1, 0.36, 1] },
  }),
};

export const FADE_SCALE: Variants = {
  hidden: { opacity: 0, scale: 0.96 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.2, ease: "easeOut" },
  },
  exit: {
    opacity: 0,
    scale: 0.96,
    transition: { duration: 0.15, ease: "easeIn" },
  },
};

export function Reveal({
  children,
  variant = ENTER_VARIANTS,
  custom,
  className,
}: {
  children: React.ReactNode;
  variant?: Variants;
  custom?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      exit="exit"
      variants={variant}
      custom={custom}
      className={className}
    >
      {children}
    </motion.div>
  );
}
```

**New file:** `frontend/web_app/src/components/ui/Stagger.tsx`

```tsx
"use client";

import { motion, type Variants } from "framer-motion";

export function staggerItems(delay: number = 0.04): Variants {
  return {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: delay,
      },
    },
  };
}

export function Stagger({
  children,
  stagger = 0.04,
  className,
}: {
  children: React.ReactNode;
  stagger?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerItems(stagger)}
      className={className}
    >
      {children}
    </motion.div>
  );
}
```

### 3.4 Add `Drawer` primitive (promoted from PanelPage)

**New file:** `frontend/web_app/src/components/ui/Drawer.tsx`

```tsx
"use client";

import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { X } from "@/lib/icons";

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  side?: "left" | "right";
  size?: "sm" | "md" | "lg";
}

const sideClasses = { left: "left-0 border-l", right: "right-0 border-r" };
const sizeClasses = { sm: "w-80", md: "w-96", lg: "w-[28rem]" };

export function Drawer({ isOpen, onClose, title, children, side = "right", size = "md" }: DrawerProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-modal theme-overlay"
            onClick={onClose}
          />
          <motion.div
            initial={{ x: side === "right" ? "100%" : "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: side === "right" ? "100%" : "-100%" }}
            transition={{ type: "spring", damping: 24, stiffness: 200 }}
            className={cn(
              "fixed top-0 bottom-0 glass-panel border shadow-2xl flex flex-col",
              sideClasses[side],
              sizeClasses[size]
            )}
          >
            {title && (
              <div className="flex items-center justify-between p-4 border-b border-glass-border-mid">
                <h3 className="text-sm font-bold text-text">{title}</h3>
                <button onClick={onClose} className="text-text-muted hover:text-text rounded-lg p-1" aria-label="Close drawer">
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}
            <div className="flex-1 overflow-y-auto p-4">{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

### 3.5 Validate Phase 3

```bash
cd frontend/web_app
npx playwright test e2e/smoke.spec.ts
```

**Manual check:** OS "Reduce motion" ON → no entrance/hover/modal animation. OFF → smooth. Page transitions work on navigation.

---

## Phase 4 — Modern Look & Polish

### 4.1 Replace focus-kill block (already done in 1.11)

### 4.2 Add glass cross-browser `-webkit-backdrop-filter` twins

**File:** `frontend/web_app/src/styles/globals.css`

**After line 275 (after the `.glass` block at lines 268–275), add:**

```css
/* -- Webkit backdrop-filter twins (Safari/Chrome) ---------------------------- */
.glass,
.glass-strong,
.theme-card,
.glass-product-card,
.glass-dropdown,
.theme-panel,
.theme-elevated {
  -webkit-backdrop-filter: blur(14px) saturate(140%);
  backdrop-filter: blur(14px) saturate(140%);
}
```

**Insert after line 275:**
```css

/* -- Webkit backdrop-filter twins (Safari/Chrome) ---------------------------- */
.glass,
.glass-strong,
.theme-card,
.glass-product-card,
.glass-dropdown,
.theme-panel,
.theme-elevated {
  -webkit-backdrop-filter: blur(14px) saturate(140%);
  backdrop-filter: blur(14px) saturate(140%);
}
```

### 4.3 Add hero gradient utility

**File:** `frontend/web_app/src/styles/globals.css`

**Insert after line 117 (after `--gradient-hero` in `:root`):**

```css
  --gradient-hero-multi:
    radial-gradient(60% 80% at 15% 0%, color-mix(in srgb, var(--color-brand) 16%, transparent), transparent 60%),
    radial-gradient(50% 70% at 100% 10%, color-mix(in srgb, var(--color-accent) 14%, transparent), transparent 55%),
    linear-gradient(160deg, var(--color-surface-0), var(--color-surface-1) 60%, var(--color-surface-2));
```

### 4.4 Add `@media (prefers-reduced-motion)` view-transition utilities

**File:** `frontend/web_app/src/styles/globals.css`

**Insert after line 2271 (after the focus-visible block):**

```css
/* -- View Transitions (progressive) ------------------------------------------- */
@media (prefers-reduced-motion: no-preference) {
  ::view-transition-old(root),
  ::view-transition-new(root) {
    animation-duration: 220ms;
    animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
  }
}
```

### 4.5 Add `.theme-range` input styling (referenced in forms)

**File:** `frontend/web_app/src/styles/globals.css`

**Insert after line 607 (after `.theme-input:focus-visible` block):**

```css
  /* Range inputs */
  .theme-range {
    -webkit-appearance: none;
    appearance: none;
    height: 0.375rem;
    background: var(--color-border);
    border-radius: 9999px;
    outline: none;
  }
  .theme-range::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 1rem;
    height: 1rem;
    border-radius: 50%;
    background: var(--color-brand);
    cursor: pointer;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-brand) 20%, transparent);
  }
  .theme-range::-moz-range-thumb {
    width: 1rem;
    height: 1rem;
    border-radius: 50%;
    background: var(--color-brand);
    cursor: pointer;
    border: none;
  }
```

### 4.6 Delete `!important` panel overrides (after Phase 2 migration complete)

**File:** `frontend/web_app/src/styles/globals.css`

**Delete lines 908–976 (the entire `:where(.supplier, .logistics-partner, .admin)` block):**

```css
908:   /* Make all panel pages use consistent button styling by default.
909:      Uses :where() so specificity stays at (0,0,1) — individual
910:      Tailwind utilities (0,1,0) always win over this fallback. */
911:   :where(.supplier, .logistics-partner, .admin) button {
...
976:   }
```

**Validate:** `grep -n ":where(.supplier" globals.css` returns nothing after deletion.

### 4.7 Validate Phase 4

```bash
cd frontend/web_app
npm run lint
npx jest
```

**Manual QA:**
- Tab through a form → focus-visible ring appears on every interactive element
- Safari/Chrome → glass panels render with backdrop blur
- Toggle light/dark → status chips, glass panels, gradients re-theme
- Page navigation → smooth fade+slide transition

---

## Phase 5 — Rollout, Validation & Gates

### 5.1 Per-phase gate checklist

After each phase, run this full suite:

```bash
cd frontend/web_app

# 1. Token test (must pass after Phase 0)
npx jest src/__tests__/designSystemTokens.test.ts

# 2. Full typecheck (after Phases 1, 2)
npx tsc --noEmit --skipLibCheck

# 3. Lint (after Phases 1, 2, 4)
npm run lint

# 4. Unit tests
npx jest

# 5. E2E smoke
npx playwright test e2e/smoke.spec.ts

# 6. a11y (if jest-axe tests exist)
npx jest --testPathPattern a11y
```

### 5.2 Migration priority order for Phase 2

Migrate per-PR in this order (highest traffic first):

1. **Product card buttons** → `ui/Button` (BannerCanvasEditor.tsx has 40+ raw `theme-btn-secondary`)
2. **Cart / checkout buttons** → `ui/Button`
3. **Auth modals** (AuthRequiredModal, QuickViewModal) → `ui/Modal`
4. **Admin panel modals** → `ui/Modal`
5. **Supplier panel modals** → `ui/Modal`
6. **Remaining modals** → `ui/Modal`

Each PR: migrate one component family, run the gate suite, land, repeat.

### 5.3 Codemod scripts (run once, review, then commit)

Create these two scripts in `frontend/web_app/scripts/`:

**`scripts/codemod-fontsize.mjs`:**
```js
// Migrate text-[10px] → text-xs, text-[9px] → text-3xs, text-[8px] → text-4xs, text-[7px] → text-5xs
import { readdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";

const root = join(process.cwd(), "src");
const map = [
  [/text-\[10px\]/g, "text-xs"],
  [/text-\[9px\]/g,  "text-3xs"],
  [/text-\[8px\]/g,  "text-4xs"],
  [/text-\[7px\]/g,  "text-5xs"],
];

function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.name.endsWith(".tsx") || entry.name.endsWith(".ts")) {
      let src = readFileSync(full, "utf8");
      let changed = false;
      for (const [re, replacement] of map) {
        if (re.test(src)) { src = src.replace(re, replacement); changed = true; }
      }
      if (changed) writeFileSync(full, src);
    }
  }
}
walk(root);
console.log("Font-size codemod complete.");
```

**`scripts/codemod-zindex.mjs`:**
```js
// Migrate z-[200] → z-modal, z-[999] → z-modal, z-[300] → z-dropdown, z-200 → z-toast
import { readdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";

const root = join(process.cwd(), "src");
const map = [
  [/z-\[200\]/g,  "z-modal"],
  [/z-200/g,      "z-toast"],
  [/z-\[999\]/g,  "z-modal"],
  [/z-\[300\]/g,  "z-dropdown"],
];

function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.name.endsWith(".tsx") || entry.name.endsWith(".ts")) {
      let src = readFileSync(full, "utf8");
      let changed = false;
      for (const [re, replacement] of map) {
        if (re.test(src)) { src = src.replace(re, replacement); changed = true; }
      }
      if (changed) writeFileSync(full, src);
    }
  }
}
walk(root);
console.log("Z-index codemod complete.");
```

Run with:
```bash
cd frontend/web_app
node scripts/codemod-fontsize.mjs
node scripts/codemod-zindex.mjs
git diff  # review before committing
```

### 5.4 What we keep (do NOT change)

- Current lime/gold brand: `--color-brand: #32CD32`, `--color-accent: #FFD700`
- `globals.css` existing vocabulary (glass, theme-card, theme-panel, shimmer, seasonal-banner-*, etc.)
- `tailwind.config.js` `scaleIn`/`spring`/`expo-out`/`smooth` easing tokens
- Rich `BackgroundEffect.tsx` seasonal engine
- `BannerCanvasEditor.tsx` (legitimate canvas/SVG colors)
- Chart color palettes

### 5.5 What we drop

- `frontend/web_app/src/styles/variables.css` (orphan, orange/purple, conflicts with brand)
- `frontend/web_app/src/components/ToastSystem.tsx` (dead code, imported nowhere)
- `frontend/web_app/src/components/LoadingSkeleton.tsx` (root duplicate — keep `ui/shared/Loadingkeleton.tsx`)
- `globals.css:2004–2012` dead `fadeIn`/`slideUp` keyframes
- `globals.css:2255–2271` focus-kill block (replaced by 1.11)
- `globals.css:908–976` `!important` panel overrides (replaced by component system in Phase 2)
- All raw `theme-btn-*` usages outside `ui/Button.tsx` (migrated in Phase 2)
- All raw `glass-panel` modal markup outside `ui/Modal.tsx` (migrated in Phase 2)
- All `text-[10px]…[7px]` arbitrarys (migrated in 1.2 + codemod)

---

## Complete File Change Summary

| Phase | File | Lines | Action |
|-------|------|-------|--------|
| 0 | `src/styles/globals.css` | 2 | Insert `@import "./tokens.css"` |
| 0 | `src/app/layout.tsx` | 5–6 | Insert `import "@/styles/tokens.css"` + `import "@/styles/glow.css"` |
| 0 | `src/styles/variables.css` | 90 | DELETE |
| 0 | `src/styles/comm.css` | 292 | RESTORE from HEAD |
| 0 | `src/styles/panel-modern.css` | 74 | RESTORE from HEAD |
| 0 | `src/styles/glow.css` | 43 | RESTORE from HEAD |
| 0 | `src/styles/tokens.css` | 246 | RESTORE from HEAD |
| 1 | `shared/src/theme.ts` | 197–213 | Extend `applyCssTheme` with status/glass vars |
| 1 | `tailwind.config.js` | 72–88 | Add 3xs–5xs font sizes |
| 1 | `tailwind.config.js` | 194–203 | Replace z-index with named scale |
| 1 | `tailwind.config.js` | 205–211 | Add `max-w-450` |
| 1 | `tailwind.config.js` | 127–139 | Add gradient-brand-to-* keys |
| 1 | `tailwind.config.js` | 100–109 | Map borderRadius to `--zozi-radius-*` |
| 1 | `tailwind.config.js` | 144–154 | Map transitionDuration to `--zozi-duration-*` |
| 1 | `src/styles/globals.css` | 2004–2014 | Delete dead fadeIn/slideUp keyframes |
| 1 | `src/styles/globals.css` | ~2003 | Insert `@keyframes scaleIn` |
| 1 | `src/styles/globals.css` | ~49 | Insert `--color-background` |
| 1 | `src/styles/globals.css` | ~278 | Insert `.theme-btn-secondary` at top level |
| 1 | `src/styles/globals.css` | ~319 | Insert `.theme-btn-danger` + `.theme-btn-danger-outline` |
| 1 | `src/styles/globals.css` | 2255–2271 | Replace focus-kill with focus-visible ring |
| 1 | `src/components/ToastContainer.tsx` | 37 | Replace `z-200` with `z-toast` |
| 2 | `src/components/ui/index.ts` | NEW | Barrel export all primitives |
| 2 | `src/components/ui/shared/Modal.tsx` | 7–76 | Add drawer variant + a11y props |
| 2 | `src/components/ToastSystem.tsx` | 85 | DELETE |
| 2 | `src/components/LoadingSkeleton.tsx` | — | DELETE (root duplicate) |
| 2 | `src/components/ui/Container.tsx` | NEW | Container primitive |
| 2 | `src/components/ui/PageHeader.tsx` | NEW | PageHeader primitive |
| 2 | `src/components/ui/Section.tsx` | NEW | Section primitive |
| 2 | `src/components/ui/Heading.tsx` | NEW | Heading primitive |
| 2 | `src/components/ui/Alert.tsx` | NEW | Alert primitive |
| 2 | `src/components/ui/StatusBadge.tsx` | NEW | StatusBadge primitive |
| 2 | `src/components/ui/Spinner.tsx` | NEW | Spinner primitive |
| 2 | `src/components/ui/Drawer.tsx` | NEW | Drawer primitive |
| 2 | 20+ modal files | — | Migrate to `<Modal>` (per-PR) |
| 2 | 80+ button files | — | Migrate to `<Button>` (per-PR) |
| 3 | `src/app/layout.tsx` | 3–4, 97–120 | Import `MotionConfig` + wrap app |
| 3 | `src/app/template.tsx` | NEW | Page transition wrapper |
| 3 | `src/components/ui/Reveal.tsx` | NEW | Promote ENTER_VARIANTS + FADE_SCALE |
| 3 | `src/components/ui/Stagger.tsx` | NEW | Promote staggerItems |
| 3 | `src/components/ui/Drawer.tsx` | NEW | Drawer primitive (also in Phase 2) |
| 4 | `src/styles/globals.css` | ~275 | Insert webkit backdrop-filter twins |
| 4 | `src/styles/globals.css` | ~117 | Insert `--gradient-hero-multi` |
| 4 | `src/styles/globals.css` | ~2271 | Insert view-transition media query |
| 4 | `src/styles/globals.css` | ~607 | Insert `.theme-range` input styling |
| 4 | `src/styles/globals.css` | 908–976 | Delete `!important` panel overrides |
| 5 | `scripts/codemod-fontsize.mjs` | NEW | Font-size codemod |
| 5 | `scripts/codemod-zindex.mjs` | NEW | Z-index codemod |

---

## Validation Matrix

| Phase | Command | Expected result |
|-------|---------|-----------------|
| 0 | `npx jest src/__tests__/designSystemTokens.test.ts` | 9/9 pass |
| 1 | `npx tsc --noEmit --skipLibCheck` | 0 errors |
| 1 | `npm run lint` | 0 errors |
| 1 | `npx jest src/__tests__/designSystemTokens.test.ts` | 9/9 pass |
| 2 | `npx jest` | All pass, new primitives importable |
| 2 | `npm run lint` | 0 errors |
| 3 | `npx playwright test e2e/smoke.spec.ts` | Pass |
| 3 | Manual OS "Reduce motion" toggle | Animations on/off correctly |
| 4 | `npm run lint` + `npx jest` | 0 errors, all pass |
| 4 | Manual Tab through form | Focus-visible ring visible |
| 4 | Manual light/dark toggle | Status chips + glass re-theme |
| 5 | Full gate suite (5.1) | All pass |

---

## Key Architectural Decisions

1. **Keep brand lime/gold** (`#32CD32`/`#FFD700`) — do NOT restore old orange/purple `variables.css`.
2. **Keep `globals.css` existing vocabulary** — do NOT restore `globals_old.css` (3,400 generated Tailwind v3 utilities).
3. **Keep `scaleIn`/`spring`/`expo-out`/`smooth` Tailwind easing tokens** — already declared in config.
4. **Keep `BackgroundEffect.tsx` seasonal engine** — untouched.
5. **Keep `BannerCanvasEditor.tsx` canvas/SVG colors** — untouched.
6. **Delete `variables.css`** — orphan, conflicts, imported nowhere.
7. **Delete `ToastSystem.tsx`** — dead code, imported nowhere.
8. **Phase 2 is the long pole** — migrate per-PR, highest-traffic first.
