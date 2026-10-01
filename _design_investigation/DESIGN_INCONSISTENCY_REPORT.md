# ZOZI Frontend — Design Inconsistency Investigation Report

> **Date:** 2026-08-31
> **Scope:** `frontend/web_app/src/styles/globals.css`, `tokens.css`, `tailwind.config.js`, and component files
> **Findings:** 25+ critical inconsistencies, duplicates, and missing definitions

---

## Critical Issues (Must Fix)

### 1. Token Conflicts Between tokens.css and globals.css

**Problem:** `tokens.css` and `globals.css` define the SAME variables with DIFFERENT values. Since `globals.css` is imported after `tokens.css`, globals wins — but the tokens.css values are silently ignored, creating confusion.

| Variable | tokens.css (ignored) | globals.css (active) | Impact |
|----------|---------------------|---------------------|--------|
| `--color-brand` | `#2ecc4f` | `#32CD32` | Brand color confusion |
| `--color-brand-light` | `#5fe57a` | `#7CFC00` | Light brand confusion |
| `--color-brand-dark` | `#1f9e3c` | `#228B22` | Dark brand confusion |
| `--color-surface-1` | `#0f172a` | `#111111` | Surface color confusion |
| `--color-surface-2` | `#1e293b` | `#1A1A1A` | Surface color confusion |
| `--color-surface-3` | `#334155` | `#2A2A2A` | Surface color confusion |
| `--color-text-primary` | `#f8fafc` | N/A (uses `--color-text`) | Naming inconsistency |
| `--color-text-secondary` | `#94a3b8` | N/A (uses `--color-text-muted`) | Naming inconsistency |
| `--color-error` | `#ef4444` | N/A (uses `--color-danger`) | Naming inconsistency |

**Fix:** Remove duplicate definitions from `tokens.css` OR remove from `globals.css` and let tokens.css be the single source of truth.

---

### 2. Missing Keyframes (Referenced But Not Defined)

**Problem:** The following keyframes are referenced in CSS classes but NEVER defined in `globals.css`:

| Class | Referenced Keyframe | Line | Status |
|-------|-------------------|------|--------|
| `.anim-fade-up` | `slideUp` | globals.css:2310 | **MISSING** |
| `.anim-fade-in` | `fadeIn` | globals.css:2311 | **MISSING** |

**Impact:** These animation classes do NOTHING — elements won't animate.

**Fix:** Add the missing keyframes:
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
```

---

### 3. Duplicate CSS Classes (Defined Multiple Times)

#### 3.1 `.glass` — Defined TWICE

| Location | Definition | Line |
|----------|-----------|------|
| First | `background: var(--color-glass-panel); backdrop-filter: blur(10px) saturate(120%);` | globals.css:252-259 |
| Second | `background: color-mix(in srgb, var(--color-surface-0) 72%, transparent); backdrop-filter: blur(16px);` | globals.css:1258-1262 |

**Impact:** Second definition wins (blur 16px vs 10px). First definition is dead code.

**Fix:** Remove the first definition at line 252-259. Keep only the second at line 1258-1262.

---

#### 3.2 `.theme-btn-primary` — Defined THREE times

| Location | Line | Notes |
|----------|------|-------|
| Base definition | globals.css:262-279 | Outside @layer |
| Inside @layer utilities | globals.css:863-890 | With !important overrides |
| Light theme override | globals.css:281-290 | .light .theme-btn-primary |
| Light theme override 2 | globals.css:873-877 | .light .theme-btn-primary with !important |
| Light theme override 3 | globals.css:1798-1803 | .light .theme-btn-primary at end of file |

**Impact:** Confusing cascade, !important fights, hard to maintain.

**Fix:** Consolidate into a single definition with proper light/dark variants.

---

#### 3.3 `.theme-btn-accent` — Defined THREE times

| Location | Line | Notes |
|----------|------|-------|
| Base definition | globals.css:292-309 | Outside @layer |
| Inside @layer utilities | globals.css:907-925 | With !important overrides |
| Light theme override | globals.css:1805-1814 | .light .theme-btn-accent at end of file |

**Fix:** Consolidate into a single definition.

---

#### 3.4 `.theme-btn-secondary` — Defined TWO times

| Location | Line | Notes |
|----------|------|-------|
| Inside @layer utilities | globals.css:892-905 | First definition |
| Spring transition override | globals.css:2318-2321 | Transition override at end of file |

**Fix:** Consolidate into a single definition.

---

#### 3.5 `.text-gradient` — Defined TWO times

| Location | Definition | Line |
|----------|-----------|------|
| First | `background: linear-gradient(135deg, var(--color-text), var(--color-text-muted));` | globals.css:1680-1685 |
| Second | `background: linear-gradient(135deg, var(--color-brand-light), var(--color-accent));` | globals.css:2275 |

**Impact:** Second definition wins. First is dead code.

**Fix:** Remove the first definition at line 1680-1685.

---

### 4. Duplicate Keyframes (Defined in Both globals.css and tailwind.config.js)

**Problem:** The following keyframes are defined in BOTH files:

| Keyframe | globals.css Line | tailwind.config.js Line |
|----------|-----------------|------------------------|
| `scaleIn` | 1913 | 190-194 |
| `shimmer` | 1914-1917 | 181-184 |
| `float` | 1919-1922 | 177-180 |
| `fadeIn` | N/A (missing!) | 185 |
| `slideUp` | N/A (missing!) | 186-189 |

**Impact:** Duplicate maintenance, potential conflicts.

**Fix:** Remove keyframes from `tailwind.config.js` and define ONLY in `globals.css`. Add missing `fadeIn` and `slideUp` to globals.css.

---

### 5. Misplaced Code Blocks (At End of globals.css)

**Problem:** The following code blocks are at the END of the file (lines 2220-2367) instead of with their related classes:

| Block | Current Line | Should Be With |
|-------|-------------|----------------|
| `.theme-btn-danger` | 2225-2238 | Other button classes (lines 262-309) |
| `.theme-btn-danger-outline` | 2240-2249 | Other button classes |
| `.theme-btn-outline` | 2251-2260 | Other button classes |
| `.hero-display`, `.btn`, `.btn-primary`, `.btn-secondary` | 2262-2269 | Other component classes |
| `.bg-gradient-brand-to-success` | 2272 | Other gradient utilities |
| `.text-gradient` (duplicate) | 2275 | Other text utilities |
| `--zozi-ext-*` tokens | 2280-2286 | Other tokens (:root block) |
| `bcu-*` keyframes | 2291-2297 | Other keyframes (lines 1913-2002) |
| `--zozi-ease-*` motion tokens | 2302-2305 | Other tokens (:root block) |
| `.anim-fade-up`, `.anim-fade-in`, `.anim-scale-in` | 2310-2312 | Other animation utilities |
| Card hover lift | 2315 | Other hover utilities |
| Spring transitions | 2318-2321 | Other transition utilities |
| Glass cross-browser twins | 2324-2327 | Other glass utilities |
| Hero gradient | 2330-2335 | Other gradient utilities |
| View transitions | 2338-2343 | Other media queries |
| Print styles | 2346-2367 | Other media queries |

**Fix:** Move all misplaced blocks to their logical locations within the file.

---

### 6. Duplicate `@media (prefers-reduced-motion: reduce)` Blocks

**Problem:** Two separate blocks for the same media query:

| Block | Lines | Content |
|-------|-------|---------|
| First | 2104-2122 | Targets specific animation classes |
| Second | 2123-2130 | Targets ALL elements with `!important` |

**Impact:** Redundant, the second block overrides the first.

**Fix:** Consolidate into a single block.

---

### 7. Inconsistent Color Naming Between tokens.css and globals.css

**Problem:** Different naming conventions for the same concept:

| tokens.css | globals.css | Should Be |
|------------|-------------|-----------|
| `--color-text-primary` | `--color-text` | Single convention |
| `--color-text-secondary` | `--color-text-muted` | Single convention |
| `--color-error` | `--color-danger` | Single convention |
| `--color-background-rgb` | N/A | Add to globals |

**Fix:** Standardize on one naming convention.

---

### 8. Button Component Uses Undefined Classes

**Problem:** `Button.tsx` references classes that may not exist or are inconsistently defined:

| Class | Used In | Status |
|-------|---------|--------|
| `theme-btn-danger` | Button.tsx:36 | Defined at line 2225 (misplaced) |
| `theme-btn-danger-outline` | Button.tsx:37 | Defined at line 2240 (misplaced) |
| `theme-btn-admin` | Button.tsx:39 | **NOT DEFINED anywhere** |

**Fix:** Add `.theme-btn-admin` class definition.

---

### 9. Modal Component Uses `z-50` Instead of Named Z-Index

**Problem:** `Modal.tsx` uses `z-50` but the design system defines named z-index scale (`z-modal: "1050"`).

**Fix:** Change `z-50` to `z-modal` in Modal.tsx.

---

### 10. Animation Classes Reference Non-Existent Keyframes

**Problem:** The following animation classes are defined but their keyframes don't exist:

| Class | Referenced Keyframe | Status |
|-------|-------------------|--------|
| `.animate-fade-in` | `fadeIn` | Keyframe MISSING in globals.css |
| `.anim-fade-up` | `slideUp` | Keyframe MISSING in globals.css |

**Fix:** Add the missing keyframes to globals.css.

---

## Summary of Required Fixes

### globals.css Fixes

1. **Remove duplicate `.glass` definition** (lines 252-259)
2. **Remove duplicate `.text-gradient` definition** (lines 1680-1685)
3. **Consolidate `.theme-btn-primary`** into single definition
4. **Consolidate `.theme-btn-accent`** into single definition
5. **Consolidate `.theme-btn-secondary`** into single definition
6. **Add missing keyframes:** `fadeIn`, `slideUp`
7. **Move misplaced blocks** to logical locations
8. **Consolidate `@media (prefers-reduced-motion: reduce)`** into single block
9. **Add `.theme-btn-admin` class** (referenced by Button.tsx but not defined)
10. **Remove duplicate `.light .theme-btn-primary`** overrides (keep only one)

### tokens.css Fixes

11. **Remove duplicate variable definitions** that conflict with globals.css
12. **Standardize naming** with globals.css conventions

### tailwind.config.js Fixes

13. **Remove duplicate keyframes** (scaleIn, shimmer, float) — keep only in globals.css
14. **Add missing keyframes** (fadeIn, slideUp) OR remove from config

### Component Fixes

15. **Modal.tsx:** Change `z-50` to `z-modal`
16. **Button.tsx:** Verify all referenced classes exist

---

## Priority Order

| Priority | Fix | Impact |
|----------|-----|--------|
| **P0** | Add missing `fadeIn` and `slideUp` keyframes | Animations don't work |
| **P0** | Add `.theme-btn-admin` class | Admin buttons unstyled |
| **P1** | Remove duplicate `.glass` definition | Confusing cascade |
| **P1** | Consolidate `.theme-btn-primary` | Maintenance nightmare |
| **P1** | Consolidate `.theme-btn-accent` | Maintenance nightmare |
| **P1** | Remove duplicate `.text-gradient` | Confusing cascade |
| **P2** | Move misplaced code blocks | Code organization |
| **P2** | Consolidate `@media (prefers-reduced-motion)` | Redundant code |
| **P2** | Fix token conflicts | Single source of truth |
| **P3** | Standardize naming conventions | Long-term maintainability |
| **P3** | Fix Modal z-index | Design system compliance |
| **P3** | Remove duplicate keyframes from tailwind config | Single source of truth |

---

## Detailed Line-by-Line Fix List

### Fix 1: Remove Duplicate `.glass` (globals.css:252-259)

```css
/* DELETE lines 252-259:
.glass {
  background: var(--color-glass-panel);
  backdrop-filter: blur(10px) saturate(120%);
  -webkit-backdrop-filter: blur(10px) saturate(120%);
  border: 1px solid var(--color-glass-border);
  box-shadow: var(--shadow-card);
  border-radius: var(--radius-card);
}
*/
```

### Fix 2: Remove Duplicate `.text-gradient` (globals.css:1680-1685)

```css
/* DELETE lines 1680-1685:
.text-gradient {
  background: linear-gradient(135deg, var(--color-text), var(--color-text-muted));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
*/
```

### Fix 3: Add Missing Keyframes (globals.css:1913)

```css
/* ADD after line 1913 (after the existing scaleIn keyframe):
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
*/
```

### Fix 4: Add `.theme-btn-admin` Class

```css
/* ADD with other button classes (after .theme-btn-accent):
.theme-btn-admin {
  background-color: var(--color-warning);
  color: var(--color-on-warning);
  transition: background-color 0.2s ease;
}
.theme-btn-admin:hover {
  background-color: color-mix(in srgb, var(--color-warning) 85%, white);
}
*/
```

### Fix 5: Fix Modal z-index (Modal.tsx:58)

```tsx
/* CHANGE line 58 in Modal.tsx:
FROM: "fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4"
TO:   "fixed inset-0 z-modal flex items-center justify-center theme-overlay p-4"
*/
```

### Fix 6: Consolidate `.theme-btn-primary` (globals.css)

```css
/* REPLACE all .theme-btn-primary definitions with a single consolidated version:
.theme-btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-accent) 14%, var(--color-brand-light)) 0%, color-mix(in srgb, var(--color-accent) 10%, var(--color-brand)) 58%, var(--color-brand-dark) 100%);
  color: var(--color-on-brand);
  padding: 0.5rem 1rem;
  border-radius: 0.75rem;
  box-shadow: 0 18px 32px -22px rgba(47, 180, 61, 0.68), 0 10px 24px -20px rgba(242, 201, 76, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  border: 1px solid color-mix(in srgb, var(--color-brand-light) 40%, rgba(255, 255, 255, 0.14));
  transition: transform 0.12s ease, box-shadow 0.2s ease;
}
.theme-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 36px -22px rgba(47, 180, 61, 0.8), 0 14px 28px -24px rgba(242, 201, 76, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.24);
  filter: saturate(1.05);
}
.theme-btn-primary:focus-visible {
  outline: none;
  box-shadow: 0 6px 28px color-mix(in srgb, var(--color-brand) 28%, black / 12%), 0 0 0 4px color-mix(in srgb, var(--color-brand) 22%, transparent);
}
.light .theme-btn-primary {
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-accent) 18%, var(--color-brand-light)) 0%, color-mix(in srgb, var(--color-accent) 11%, var(--color-brand)) 58%, var(--color-brand-dark));
  box-shadow: 0 18px 32px -18px rgba(47, 180, 61, 0.48), 0 10px 20px -20px rgba(242, 201, 76, 0.3), inset 0 1px 0 rgba(255,255,255,0.3);
}
*/
```

### Fix 7: Consolidate `.theme-btn-accent` (globals.css)

```css
/* REPLACE all .theme-btn-accent definitions with a single consolidated version:
.theme-btn-accent {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-brand-light) 12%, var(--color-accent-light)) 0%, var(--color-accent) 54%, color-mix(in srgb, var(--color-brand) 14%, var(--color-accent-dark)) 100%);
  color: var(--color-on-accent);
  padding: 0.48rem 0.98rem;
  border-radius: 0.75rem;
  box-shadow: 0 18px 30px -22px rgba(242, 201, 76, 0.72), 0 10px 22px -20px rgba(47, 180, 61, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.24);
  border: 1px solid color-mix(in srgb, var(--color-accent-light) 42%, rgba(255, 255, 255, 0.14));
  transition: transform 0.12s ease, box-shadow 0.2s ease;
}
.theme-btn-accent:hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 34px -20px rgba(242, 201, 76, 0.86), 0 14px 26px -22px rgba(47, 180, 61, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.28);
  filter: saturate(1.03);
}
.theme-btn-accent:focus-visible {
  outline: none;
  box-shadow: 0 6px 28px color-mix(in srgb, var(--color-accent) 28%, black / 12%), 0 0 0 4px color-mix(in srgb, var(--color-accent) 18%, transparent);
}
.light .theme-btn-accent {
  background: linear-gradient(135deg, var(--color-accent-light) 0%, var(--color-accent) 55%, color-mix(in srgb, var(--color-brand) 8%, var(--color-accent)) 100%);
  box-shadow: 0 20px 36px -14px rgba(242, 201, 76, 0.68), 0 10px 22px -18px rgba(47, 180, 61, 0.22), inset 0 1.5px 0 rgba(255, 255, 255, 0.56), inset 0 -1px 0 rgba(163, 126, 14, 0.1);
}
*/
```

### Fix 8: Consolidate `@media (prefers-reduced-motion: reduce)` (globals.css:2104-2130)

```css
/* REPLACE both blocks (lines 2104-2130) with a single consolidated block:
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
*/
```

### Fix 9: Remove Duplicate Keyframes from tailwind.config.js

```js
/* REMOVE from tailwind.config.js keyframes (lines 172-194):
keyframes: {
  ticker: { ... },
  float: { ... },      // REMOVE - duplicate
  shimmer: { ... },    // REMOVE - duplicate
  fadeIn: { ... },     // REMOVE - duplicate
  slideUp: { ... },    // REMOVE - duplicate
  scaleIn: { ... },    // REMOVE - duplicate
},

/* KEEP only:
keyframes: {
  ticker: {
    "0%": { transform: "translateX(0)" },
    "100%": { transform: "translateX(-50%)" },
  },
},
*/
```

### Fix 10: Move Misplaced Code Blocks

```css
/* MOVE the following blocks from the end of globals.css to their logical locations:

1. `.theme-btn-danger` → After `.theme-btn-accent` (around line 310)
2. `.theme-btn-danger-outline` → After `.theme-btn-danger`
3. `.theme-btn-outline` → After `.theme-btn-danger-outline`
4. `.hero-display`, `.btn`, `.btn-primary`, `.btn-secondary` → After button classes
5. `.bg-gradient-brand-to-success` → With other gradient utilities
6. `.text-gradient` → With other text utilities (keep only one)
7. `--zozi-ext-*` tokens → Inside :root block (lines 29-106)
8. `bcu-*` keyframes → With other keyframes (after line 2002)
9. `--zozi-ease-*` motion tokens → Inside :root block
10. `.anim-fade-up`, `.anim-fade-in`, `.anim-scale-in` → With other animation utilities
11. Card hover lift → With other hover utilities
12. Spring transitions → With other transition utilities
13. Glass cross-browser twins → With other glass utilities
14. Hero gradient → With other gradient utilities
15. View transitions → With other media queries
16. Print styles → With other media queries
*/
```

---

## Verification Checklist

After applying all fixes, verify:

- [ ] No duplicate CSS class definitions
- [ ] No duplicate keyframe definitions
- [ ] All referenced keyframes exist
- [ ] All referenced classes exist
- [ ] No token conflicts between files
- [ ] Code blocks are in logical locations
- [ ] Single `@media (prefers-reduced-motion: reduce)` block
- [ ] Consistent naming conventions
- [ ] Modal uses `z-modal` instead of `z-50`
- [ ] Button component references all exist classes
- [ ] Animations work correctly
- [ ] Light/dark theme switching works
- [ ] No console errors about missing classes

---

## Files Modified

| File | Changes |
|------|---------|
| `globals.css` | Remove duplicates, add missing keyframes, consolidate classes, move misplaced blocks |
| `tokens.css` | Remove conflicting definitions, standardize naming |
| `tailwind.config.js` | Remove duplicate keyframes |
| `Modal.tsx` | Change `z-50` to `z-modal` |
| `Button.tsx` | Verify all classes exist (no changes needed after globals.css fixes) |
