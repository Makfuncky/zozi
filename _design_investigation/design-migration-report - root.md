# Design Migration Report: F: Drive → D: Drive

> **Source (good design):** `F:\Projects\10- E-COMMERCE WEBSITE\zozi\`  
> **Target (current):** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\`  
> **Date:** 2026-08-30

---

## Executive Summary

The F: drive contains **5 CSS/design files** that are completely missing from the D: drive project. These files contain complete, production-ready component styling (buttons, inputs, product cards, ticker bar) and a root-level Tailwind config. The D: drive has 5 other CSS files that F: lacks, but those are auxiliary (banner effects, admin HUD, print styles).

**Core finding:** The F: drive CSS modules use the **legacy design token system** (`variables.css` — orange/purple palette), while the current `globals.css` uses the **new token system** (green/yellow palette). Both files exist in both projects but the CSS modules only reference the legacy tokens. Migration requires either importing `variables.css` or porting the module styles to the new token system.

---

## Part 1: Files to Copy from F: → D:

### 1.1 — `frontend/web_app/src/components/Button.module.css` (192 lines)

**Status:** EXISTS in F:, MISSING in D:  
**What it does:** Complete button styling with 7 variants, 6 sizes, ripple effect, loading spinner

```css
/* Button.module.css */
.button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  border-radius: 9999px;
  transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1);
  cursor: pointer;
  border: none;
  white-space: nowrap;
  letter-spacing: 0.01em;
  overflow: hidden;
  outline: none;
}

.button:focus-visible {
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.25);
}

.button:disabled {
  opacity: 0.45;
  pointer-events: none;
  cursor: not-allowed;
}

/* Variants */
.default {
  background: linear-gradient(135deg, #f97316 0%, #a855f7 100%);
  color: #fff;
  box-shadow: 0 4px 20px rgba(249, 115, 22, 0.35);
}

.default:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 32px rgba(249, 115, 22, 0.5);
}

.gold {
  background: linear-gradient(135deg, #fbbf24 0%, #fde68a 100%);
  color: #1a1200;
  box-shadow: 0 4px 16px rgba(245, 158, 11, 0.3);
}

.gold:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 28px rgba(245, 158, 11, 0.45);
}

.outline {
  background: rgba(255, 255, 255, 0.04);
  color: #fafaf9;
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
}

.outline:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}

.ghost {
  color: rgba(250, 250, 249, 0.7);
  background: transparent;
}

.ghost:hover:not(:disabled) {
  color: #fafaf9;
  background: rgba(255, 255, 255, 0.08);
}

.glass {
  background: rgba(255, 255, 255, 0.06);
  color: #fafaf9;
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
}

.glass:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.15);
}

.destructive {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.destructive:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.25);
}

/* Sizes */
.xs {
  height: 32px;
  padding: 0 12px;
  font-size: 0.75rem;
  border-radius: 16px;
}

.sm {
  height: 36px;
  padding: 0 16px;
  font-size: 0.875rem;
  border-radius: 20px;
}

.default {
  height: 44px;
  padding: 0 24px;
  font-size: 0.875rem;
  border-radius: 20px;
}

.lg {
  height: 48px;
  padding: 0 32px;
  font-size: 1rem;
  border-radius: 24px;
}

.xl {
  height: 56px;
  padding: 0 40px;
  font-size: 1rem;
  border-radius: 24px;
}

.icon {
  height: 40px;
  width: 40px;
  padding: 0;
  border-radius: 20px;
}

.iconSm {
  height: 32px;
  width: 32px;
  padding: 0;
  border-radius: 16px;
}

/* Ripple effect */
.ripple {
  position: relative;
  overflow: hidden;
}

.rippleSpan {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  transform: scale(0);
  animation: ripple 0.7s ease-out;
  pointer-events: none;
}

@keyframes ripple {
  to {
    transform: scale(4);
    opacity: 0;
  }
}

/* Loading spinner */
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid #fff;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Icon spacing */
.iconLeft {
  margin-right: 8px;
}

.iconRight {
  margin-left: 8px;
}
```

---

### 1.2 — `frontend/web_app/src/components/Input.module.css` (182 lines)

**Status:** EXISTS in F:, MISSING in D:  
**What it does:** Complete form input styling with states, floating labels, icons, helper text

```css
/* Input.module.css */
.input {
  flex: 1;
  height: 44px;
  width: 100%;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px 16px;
  font-size: 14px;
  color: #fafaf9;
  background: rgba(255, 255, 255, 0.04);
  transition: all 0.3s ease;
  outline: none;
}

.input:focus {
  border-color: rgba(249, 115, 22, 0.5);
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.25);
}

.input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input.error {
  border-color: rgba(239, 68, 68, 0.5);
  background: rgba(239, 68, 68, 0.06);
}

.input.error:focus {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.3);
}

.input.success {
  border-color: rgba(16, 185, 129, 0.5);
  background: rgba(16, 185, 129, 0.06);
}

.input.success:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3);
}

.input.luxury {
  border-color: rgba(249, 115, 22, 0.2);
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 20px rgba(249, 115, 22, 0.05);
}

.input.luxury:focus {
  border-color: rgba(249, 115, 22, 0.5);
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.25), 0 0 20px rgba(249, 115, 22, 0.1);
}

/* Sizes */
.input.sm {
  height: 36px;
  padding: 8px 12px;
  font-size: 14px;
}

.input.lg {
  height: 52px;
  padding: 16px 20px;
  font-size: 16px;
}

/* Container */
.container {
  position: relative;
}

/* Label */
.label {
  display: block;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(250, 250, 249, 0.5);
  margin-bottom: 8px;
}

/* Floating label */
.floatingLabel {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  color: rgba(250, 250, 249, 0.3);
  pointer-events: none;
  transition: all 0.2s ease;
  background: transparent;
  padding: 0 4px;
}

.floatingLabel.floated {
  top: -8px;
  left: 12px;
  font-size: 12px;
  color: rgba(249, 115, 22, 0.8);
  background: #08070a;
  transform: none;
}

/* Input wrapper */
.inputWrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.inputWrapper .input {
  padding-left: 44px;
}

.inputWrapper .input.hasRightIcon {
  padding-right: 44px;
}

/* Icons */
.icon {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(250, 250, 249, 0.4);
  pointer-events: none;
  z-index: 1;
}

.icon.left {
  left: 12px;
}

.icon.right {
  right: 12px;
}

.icon.clickable {
  pointer-events: auto;
  cursor: pointer;
}

.icon.clickable:hover {
  color: rgba(250, 250, 249, 0.6);
}

/* Helper text */
.helperText {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(250, 250, 249, 0.4);
}

.helperText.error {
  color: #ef4444;
}

.helperText.success {
  color: #10b981;
}

/* Status icons */
.statusIcon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}

.statusIcon.error {
  color: #ef4444;
}

.statusIcon.success {
  color: #10b981;
}
```

---

### 1.3 — `frontend/web_app/src/components/ProductCard.module.css` (491 lines)

**Status:** EXISTS in F:, MISSING in D:  
**What it does:** Complete product card with image zoom, badges, quick view modal, add-to-cart states

```css
/* ProductCard.module.css */
.card {
  position: relative;
  border-radius: var(--radius-xl);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  background: var(--color-surface-2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all var(--transition-fast);
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-xl), 0 0 0 1px rgba(79, 70, 229, 0.2);
}

.imageContainer {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  background: var(--color-surface-3);
}

.skeleton {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, var(--color-surface-3) 25%, var(--color-surface-4) 50%, var(--color-surface-3) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.productImage {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--transition-smooth);
}

.card:hover .productImage {
  transform: scale(1.07);
}

.gradientOverlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(to bottom, transparent 30%, rgba(13, 13, 20, 0.7) 100%);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.card:hover .gradientOverlay {
  opacity: 1;
}

.discountBadge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: var(--color-error);
  color: white;
  font-size: 10px;
  font-weight: var(--font-weight-black);
  padding: 4px 8px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  line-height: 1;
}

.statusBadges {
  position: absolute;
  top: 10px;
  left: 60px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.statusBadge {
  font-size: 9px;
  font-weight: var(--font-weight-black);
  padding: 2px 8px;
  border-radius: var(--radius-md);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  line-height: 1;
}

.statusBadgeNew {
  background: rgba(249, 115, 22, 0.9);
  color: white;
}

.statusBadgeLowStock {
  background: rgba(249, 115, 22, 0.9);
  color: white;
}

.statusBadgeSoldOut {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
}

.topActions {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.actionButton {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-xl);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.wishlistButton {
  background: rgba(8, 8, 14, 0.7);
}

.wishlistButtonActive {
  background: rgba(239, 68, 68, 0.9);
  border-color: rgba(239, 68, 68, 0.4);
}

.wishlistButton:hover {
  transform: scale(1.12);
}

.quickViewButton {
  background: rgba(79, 70, 229, 0.85);
  border-color: rgba(79, 70, 229, 0.5);
}

.cardBody {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 14px;
}

.categoryRating {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.category {
  font-size: 10px;
  font-weight: var(--font-weight-bold);
  color: var(--color-primary-light);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rating {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.ratingStar {
  width: 12px;
  height: 12px;
  color: var(--color-gold);
  fill: currentColor;
}

.ratingText {
  font-size: 10px;
  font-weight: var(--font-weight-black);
  color: rgba(255, 255, 255, 0.7);
}

.productName {
  font-size: 14px;
  font-weight: var(--font-weight-bold);
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.4;
  margin-bottom: 8px;
  min-height: 40px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color var(--transition-fast);
}

.card:hover .productName {
  color: white;
}

.priceSection {
  margin-top: auto;
}

.priceRow {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
}

.price {
  font-size: 16px;
  font-weight: var(--font-weight-black);
  color: white;
  letter-spacing: -0.02em;
}

.originalPrice {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  text-decoration: line-through;
}

.freeShipping {
  font-size: 10px;
  font-weight: var(--font-weight-bold);
  color: var(--color-success);
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: auto;
}

.freeShippingIcon {
  width: 10px;
  height: 10px;
}

.addToCartButton {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  border-radius: var(--radius-xl);
  font-size: 12px;
  font-weight: var(--font-weight-black);
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.addToCartButton:not(:disabled):hover {
  box-shadow: 0 0 16px rgba(79, 70, 229, 0.35);
}

.addToCartButtonDefault {
  background: rgba(79, 70, 229, 0.15);
  color: var(--color-primary);
  border-color: rgba(79, 70, 229, 0.2);
}

.addToCartButtonDefault:hover {
  background: var(--color-primary);
  color: white;
  border-color: transparent;
}

.addToCartButtonAdded {
  background: rgba(16, 185, 129, 0.2);
  color: var(--color-success);
  border-color: rgba(16, 185, 129, 0.3);
}

.addToCartButtonDisabled {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.25);
  cursor: not-allowed;
}

/* Quick View Modal */
.modalOverlay {
  position: fixed;
  inset: 0;
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(20px);
}

.modalContent {
  border-radius: var(--radius-2xl);
  max-width: 400px;
  width: 100%;
  overflow: hidden;
  background: var(--color-surface-1);
  border: 1px solid rgba(79, 70, 229, 0.2);
  box-shadow: 0 40px 80px rgba(0, 0, 0, 0.8);
}

.modalImageContainer {
  position: relative;
  aspect-ratio: 4/3;
  overflow: hidden;
}

.modalImage {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modalGradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(13, 13, 26, 0.9), transparent 50%);
}

.modalDiscountBadge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: var(--color-error);
  color: white;
  font-size: 12px;
  font-weight: var(--font-weight-black);
  padding: 6px 10px;
  border-radius: var(--radius-xl);
}

.modalCloseButton {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  transition: all var(--transition-fast);
}

.modalCloseButton:hover {
  background: rgba(0, 0, 0, 0.8);
}

.modalBody {
  padding: 20px;
}

.modalCategory {
  font-size: 10px;
  font-weight: var(--font-weight-black);
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--color-primary-light);
  margin-bottom: 4px;
}

.modalTitle {
  font-size: 18px;
  font-weight: var(--font-weight-black);
  color: white;
  margin-bottom: 6px;
  line-height: 1.3;
}

.modalDescription {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  margin-bottom: 16px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.modalPriceRating {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.modalPrice {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.modalCurrentPrice {
  font-size: 24px;
  font-weight: var(--font-weight-black);
  color: white;
}

.modalOriginalPrice {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.3);
  text-decoration: line-through;
}

.modalRating {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.2);
}

.modalRatingStar {
  width: 14px;
  height: 14px;
  color: var(--color-gold);
  fill: currentColor;
}

.modalRatingText {
  font-size: 14px;
  font-weight: var(--font-weight-black);
  color: white;
}

.modalActions {
  display: flex;
  gap: 10px;
}

.modalViewDetails {
  flex: 1;
  padding: 12px;
  border-radius: var(--radius-xl);
  font-size: 14px;
  font-weight: var(--font-weight-bold);
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all var(--transition-fast);
}

.modalViewDetails:hover {
  color: white;
  border-color: rgba(255, 255, 255, 0.2);
}

.modalAddToCart {
  flex: 1;
  padding: 12px;
  border-radius: var(--radius-xl);
  font-size: 14px;
  font-weight: var(--font-weight-black);
  color: white;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  transition: all var(--transition-fast);
}

.modalAddToCart:hover {
  box-shadow: 0 0 20px rgba(79, 70, 229, 0.4);
}

.modalAddToCart:disabled {
  background: rgba(255, 255, 255, 0.05);
  cursor: not-allowed;
}
```

---

### 1.4 — `frontend/web_app/src/components/TickerBar.module.css` (88 lines)

**Status:** EXISTS in F:, MISSING in D:  
**What it does:** Scrolling marquee ticker bar with fade edges and accent line

```css
/* TickerBar.module.css */
.tickerBar {
  width: 100%;
  overflow: hidden;
  position: relative;
  z-index: 50;
  padding: 10px 0;
  background: linear-gradient(90deg, #08070a 0%, #100e14 20%, #100e14 80%, #08070a 100%);
  border-bottom: 1px solid rgba(249, 115, 22, 0.12);
}

.accentLine {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(249, 115, 22, 0.6), rgba(168, 85, 247, 0.6), transparent);
}

.fadeLeft {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 96px;
  z-index: 10;
  pointer-events: none;
  background: linear-gradient(to right, #08070a, transparent);
}

.fadeRight {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 96px;
  z-index: 10;
  pointer-events: none;
  background: linear-gradient(to left, #08070a, transparent);
}

.marquee {
  display: flex;
  white-space: nowrap;
  animation: marquee 50s linear infinite;
}

.tickerItem {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.tickerContent {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 32px;
}

.icon {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
}

.text {
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.22em;
  color: rgba(250, 250, 249, 0.40);
}

.separator {
  margin-left: 16px;
  color: rgba(249, 115, 22, 0.25);
}

@keyframes marquee {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}
```

---

### 1.5 — `frontend/tailwind.config.js` (Root Level, 218 lines)

**Status:** EXISTS in F:, MISSING in D:  
**What it does:** Root-level Tailwind config with Outfit/Plus Jakarta Sans font stack and indigo/amber glow shadows

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      /* -- Brand Palette -------------------------------------------- */
      colors: {
        primary: "var(--color-brand)",
        "primary-light": "var(--color-brand-light)",
        "primary-dark": "var(--color-brand-dark)",
        accent: "var(--color-accent)",
        "accent-light": "var(--color-accent-light)",
        success: "var(--color-success)",
        danger: "var(--color-danger)",
        warning: "var(--color-warning)",
        info: "var(--color-info)",
        "on-brand": "var(--color-on-brand)",
        "on-accent": "var(--color-on-accent)",
        "on-warning": "var(--color-on-warning)",
        surface: {
          base: "var(--color-surface-0)",
          1: "var(--color-surface-1)",
          2: "var(--color-surface-2)",
          3: "var(--color-surface-3)",
        },
        text: "var(--color-text)",
        "text-muted": "var(--color-text-muted)",
        "text-faint": "var(--color-text-faint)",
        border: "var(--color-border)",
        "border-light": "var(--color-border-light)",

        /* Glass / frosted-layer tokens — mirrors CSS color-mix vars */
        "glass-base":         "var(--color-glass-base)",
        "glass-mid":          "var(--color-glass-mid)",
        "glass-hi":           "var(--color-glass-hi)",
        "glass-solid":        "var(--color-glass-solid)",
        "glass-panel":        "var(--color-glass-panel)",
        "glass-faint":        "var(--color-glass-faint)",
        "glass-panel-hover":  "var(--color-glass-panel-hover)",
        "glass-border":       "var(--color-glass-border)",
        "glass-border-mid":   "var(--color-glass-border-mid)",
        "glass-border-soft":  "var(--color-glass-border-soft)",

        /* Legacy aliases (still supported) */
        charcoal: "#0f172a",
        "zozi-primary": "var(--color-brand)",
        "zozi-primary-light": "var(--color-brand-light)",
        "zozi-primary-dark": "var(--color-brand-dark)",
        "zozi-secondary": "var(--color-accent)",
        "zozi-secondary-light": "var(--color-accent-light)",
        "zozi-secondary-dark": "var(--color-accent-dark)",
        "zozi-accent": "var(--color-accent)",
        "zozi-highlight": "var(--color-danger)",
        "zozi-neutral": "var(--color-white)",
        "zozi-neutral-light": "var(--color-text-muted)",
      },

      /* -- Typography ----------------------------------------------- */
      fontFamily: {
        heading: ["var(--font-outfit)", "Outfit", "sans-serif"],
        display: ["var(--font-outfit)", "Outfit", "sans-serif"],
        body: ["var(--font-jakarta)", "Plus Jakarta Sans", "Inter", "sans-serif"],
        outfit: ["var(--font-outfit)", "Outfit", "sans-serif"],
        jakarta: ["var(--font-jakarta)", "Plus Jakarta Sans", "sans-serif"],
        sans: ["var(--font-jakarta)", "Plus Jakarta Sans", "Inter", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }],
        xs: ["0.75rem", { lineHeight: "1.125rem" }],
        sm: ["0.875rem", { lineHeight: "1.375rem" }],
        base: ["1rem", { lineHeight: "1.625rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.875rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
        "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
        "5xl": ["3rem", { lineHeight: "1.15" }],
        "6xl": ["3.75rem", { lineHeight: "1.1" }],
        display: ["clamp(2.5rem,6vw,4.5rem)", { lineHeight: "1.1" }],
      },

      /* -- Spacing -------------------------------------------------- */
      spacing: {
        4.5: "1.125rem",
        13: "3.25rem",
        15: "3.75rem",
        18: "4.5rem",
        22: "5.5rem",
        30: "7.5rem",
        88: "22rem",
        128: "32rem",
      },

      /* -- Border Radius -------------------------------------------- */
      borderRadius: {
        sm: "0.375rem",
        md: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem",
        "4xl": "2rem",
        pill: "9999px",
      },

      /* -- Shadows -------------------------------------------------- */
      boxShadow: {
        "card-sm": "0 1px 3px rgb(0 0 0 / 0.06), 0 1px 2px rgb(0 0 0 / 0.04)",
        card: "0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05)",
        "card-lg": "0 10px 25px -5px rgb(0 0 0 / 0.08), 0 8px 10px -6px rgb(0 0 0 / 0.04)",
        "card-xl": "0 20px 40px -10px rgb(0 0 0 / 0.1)",
        "glow-primary": "0 0 20px rgb(79 70 229 / 0.25)",
        "glow-accent": "0 0 20px rgb(245 158 11 / 0.25)",
        "glow-primary-lg": "0 8px 30px rgb(79 70 229 / 0.3)",
        glass: "0 8px 32px rgb(0 0 0 / 0.08), inset 0 1px 0 rgb(255 255 255 / 0.06)",
        "btn-primary": "0 4px 14px rgb(79 70 229 / 0.25)",
        "btn-primary-hover": "0 8px 24px rgb(79 70 229 / 0.35)",
        focus: "0 0 0 3px rgb(79 70 229 / 0.25)",
      },

      /* -- Gradients ------------------------------------------------ */
      backgroundImage: {
        "gradient-primary": "var(--gradient-banner)",
        "gradient-accent": "var(--gradient-banner-alt)",
        "gradient-hero": "var(--gradient-hero)",
        "gradient-logo": "var(--gradient-logo)",
        "gradient-card": "var(--gradient-card)",
        "gradient-radial": "radial-gradient(ellipse at center, var(--tw-gradient-stops))",
        "gradient-text": "var(--gradient-brand-text)",
        "gradient-logo-text": "var(--gradient-logo-text)",
      },

      /* -- Transitions ---------------------------------------------- */
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.4, 0, 0.2, 1)",
        spring: "cubic-bezier(0.22, 1, 0.36, 1)",
        "expo-out": "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      transitionDuration: {
        250: "250ms",
        350: "350ms",
        400: "400ms",
      },

      /* -- Animations ----------------------------------------------- */
      animation: {
        ticker: "ticker 60s linear infinite",
        float: "float 6s ease-in-out infinite",
        shimmer: "shimmer 2s infinite",
        "fade-in": "fadeIn 0.4s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        "scale-in": "scaleIn 0.3s ease-out",
        "spin-slow": "spin 8s linear infinite",
      },
      keyframes: {
        ticker: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: {
          from: { transform: "translateY(12px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        scaleIn: {
          from: { transform: "scale(0.95)", opacity: "0" },
          to: { transform: "scale(1)", opacity: "1" },
        },
      },

      /* -- Backdrop blur -------------------------------------------- */
      backdropBlur: {
        xs: "2px",
        sm: "4px",
        md: "8px",
        lg: "16px",
        xl: "24px",
      },

      /* -- Z-index -------------------------------------------------- */
      zIndex: {
        60: "60",
        70: "70",
        80: "80",
        90: "90",
        100: "100",
      },

      /* -- Max width ------------------------------------------------ */
      maxWidth: {
        "8xl": "88rem",
        "9xl": "96rem",
        "10xl": "120rem",
        "11xl": "140rem",
      },

      minHeight: {
        12: "3rem",
        16: "4rem",
        32: "8rem",
      },
    },
  },
  plugins: [],
};
```

**Key differences from D: drive's `frontend/web_app/tailwind.config.js`:**

| Feature | F: (root config) | D: (web_app config) |
|---|---|---|
| Font stack | `Outfit` / `Plus Jakarta Sans` | `Fraunces` / `Sora` |
| Glow shadows | Indigo `rgb(79 70 229)` / Amber `rgb(245 158 11)` | Lime `rgb(50 205 50)` / Gold `rgb(255 215 0)` |
| Focus ring | Indigo `rgb(79 70 229 / 0.25)` | Lime `rgb(50 205 50 / 0.18)` |
| Z-index values | Up to 100 | Up to 1201 (has 1200, 1201) |

---

## Part 2: Files That Are IDENTICAL (No Action Needed)

These files exist in both F: and D: and are **byte-for-byte identical**:

| File | Lines | Status |
|---|---|---|
| `frontend/web_app/src/styles/globals.css` | 2311 | ✅ Identical |
| `frontend/web_app/src/styles/variables.css` | 90 | ✅ Identical |
| `frontend/web_app/tailwind.config.js` | 220 | ✅ Identical |
| `frontend/web_app/src/app/layout.tsx` | 124 | ✅ Identical |
| `frontend/web_app/postcss.config.mjs` | 8 | ✅ Identical |

---

## Part 3: Files Only in D: Drive (Keep These)

These files exist in D: but NOT in F:. They should be **kept** as they contain newer functionality:

| File | Purpose |
|---|---|
| `frontend/web_app/src/components/banner-effects.module.css` | Confetti/snow/spark/balloon/aurora/lantern banner effects |
| `frontend/web_app/src/components/ticker-bar.css` | Minimal marquee animation (replaced by TickerBar.module.css) |
| `frontend/web_app/src/components/admin/commandCenter/hud.css` | HUD scan/pulse/shimmer keyframes for admin command center |
| `frontend/web_app/src/components/supplier/editor-buttons.css` | Editor toolbar buttons |
| `frontend/web_app/src/app/supplier/labels/[id]/print.css` | Print stylesheet for parcel labels |

---

## Part 4: Critical Compatibility Issue — Token System Mismatch

### The Problem

The F: drive CSS modules reference **legacy design tokens** from `variables.css`:

```css
/* These variables are defined in variables.css, NOT in globals.css */
var(--color-primary)        /* #f97316 (orange) in legacy */
var(--color-primary-light)  /* #fb923c in legacy */
var(--color-gold)           /* #fbbf24 in legacy */
var(--color-error)          /* #ef4444 in legacy */
var(--color-success)        /* #14b8a6 in legacy */
var(--radius-xl)            /* 20px in legacy */
var(--radius-2xl)           /* 24px in legacy */
var(--radius-lg)            /* 16px in legacy */
var(--radius-md)            /* 12px in legacy */
var(--transition-fast)      /* 0.15s ease in legacy */
var(--transition-smooth)    /* 0.3s ease in legacy */
var(--font-weight-black)    /* 900 in legacy */
var(--font-weight-bold)     /* 700 in legacy */
var(--shadow-sm)            /* legacy shadow */
var(--shadow-xl)            /* legacy shadow */
```

But the current `globals.css` uses a **completely different token system**:

```css
/* Current tokens in globals.css */
--color-brand: #32CD32 (lime green)
--color-brand-light: #7CFC00
--color-accent: #FFD700 (gold)
--color-surface-0: #000000
--color-surface-1: #111111
/* etc. */
```

### Two Migration Options

**Option A: Import `variables.css` alongside `globals.css`**
- Add `@import "./variables.css";` to `globals.css` or import it in the layout
- Pros: Quick, CSS modules work immediately
- Cons: Two competing token systems, potential conflicts, bloated CSS

**Option B: Port CSS modules to new token system (RECOMMENDED)**
- Rewrite the CSS modules to use the new `globals.css` tokens
- Pros: Single source of truth, cleaner architecture
- Cons: More work, but produces better long-term result

---

## Part 5: Implementation Plan

### Step 1: Copy the 4 CSS Module Files

Copy these files from F: to D::

```
F:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\Button.module.css
  → D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\Button.module.css

F:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\Input.module.css
  → D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\Input.module.css

F:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\ProductCard.module.css
 → D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\ProductCard.module.css

F:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\TickerBar.module.css
 → D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\TickerBar.module.css
```

### Step 2: Copy the Root Tailwind Config

```
F:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\tailwind.config.js
 → D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\tailwind.config.js
```

### Step 3: Port CSS Modules to New Token System

Replace all legacy token references in the 4 CSS module files with the new token system:

| Legacy Token (variables.css) | New Token (globals.css) |
|---|---|
| `var(--color-primary)` | `var(--color-brand)` |
| `var(--color-primary-light)` | `var(--color-brand-light)` |
| `var(--color-gold)` | `var(--color-accent)` |
| `var(--color-error)` | `var(--color-danger)` |
| `var(--color-success)` | `var(--color-success)` |
| `var(--radius-sm)` | `0.375rem` |
| `var(--radius-md)` | `0.5rem` |
| `var(--radius-lg)` | `0.75rem` |
| `var(--radius-xl)` | `1rem` |
| `var(--radius-2xl)` | `1.25rem` |
| `var(--radius-pill)` | `9999px` |
| `var(--transition-fast)` | `0.15s ease` |
| `var(--transition-smooth)` | `0.3s ease` |
| `var(--font-weight-black)` | `900` |
| `var(--font-weight-bold)` | `700` |
| `var(--shadow-sm)` | `0 1px 3px rgb(0 0 0 / 0.06)` |
| `var(--shadow-md)` | `0 4px 6px -1px rgb(0 0 0 / 0.07)` |
| `var(--shadow-lg)` | `0 10px 25px -5px rgb(0 0 0 / 0.08)` |
| `var(--shadow-xl)` | `0 20px 40px -10px rgb(0 0 0 / 0.1)` |

### Step 4: Update Hardcoded Colors in CSS Modules

The F: CSS modules also use hardcoded colors that need updating:

| Hardcoded (F:) | New (D: current palette) |
|---|---|
| `#f97316` (orange) | `var(--color-brand)` → `#32CD32` |
| `#a855f7` (purple) | `var(--color-brand-dark)` → `#228B22` |
| `#fbbf24` (amber) | `var(--color-accent)` → `#FFD700` |
| `#fde68a` (light amber) | `var(--color-accent-light)` → `#FFEA00` |
| `#08070a` (legacy bg) | `var(--color-surface-0)` → `#000000` |
| `#100e14` (legacy surface-1) | `var(--color-surface-1)` → `#111111` |
| `rgba(79, 70, 229, ...)` (indigo) | `rgba(50, 205, 50, ...)` (lime) |
| `rgba(249, 115, 22, ...)` (orange) | `rgba(50, 205, 50, ...)` (lime) |
| `#fafaf9` (legacy text) | `var(--color-text)` → `#FFFFFF` |
| `rgba(250, 250, 249, ...)` | `rgba(255, 255, 255, ...)` |

### Step 5: Update Components to Use CSS Modules

Update the D: drive components to import and use the new CSS modules:

**`components/Button.tsx`** — Change from Tailwind `cn()` to:
```tsx
import styles from "./Button.module.css";
// Use styles.button, styles.default, styles.gold, etc.
```

**`components/Input.tsx`** — Change from Tailwind `cn()` to:
```tsx
import styles from "./Input.module.css";
// Use styles.input, styles.error, styles.success, etc.
```

**`components/ProductCard.tsx`** — Change from Tailwind `cn()` to:
```tsx
import styles from "./ProductCard.module.css";
// Use styles.card, styles.imageContainer, etc.
```

**`components/TickerBar.tsx`** — Change from `import "./ticker-bar.css"` to:
```tsx
import styles from "./TickerBar.module.css";
// Use styles.tickerBar, styles.marquee, etc.
```

### Step 6: Clean Up Redundant Files

After migration, these D:-only files become redundant and can be removed:
- `frontend/web_app/src/components/ticker-bar.css` (replaced by TickerBar.module.css)

### Step 7: Verify

1. Run `npm run dev` and check all pages
2. Run `npm run lint` — must pass
3. Run `npx tsc --noEmit --skipLibCheck` — must pass
4. Verify dark/light theme switching works
5. Check RTL layout still works

---

## Part 6: Quick Reference — What Each CSS Module Provides

| Module | Classes | Key Features |
|---|---|---|
| `Button.module.css` | `.button`, `.default`, `.gold`, `.outline`, `.ghost`, `.glass`, `.destructive`, `.xs`-`.xl`, `.icon`, `.ripple`, `.spinner` | Gradient buttons, hover lift, ripple click effect, loading spinner |
| `Input.module.css` | `.input`, `.error`, `.success`, `.luxury`, `.sm`, `.lg`, `.container`, `.label`, `.floatingLabel`, `.inputWrapper`, `.icon`, `.helperText`, `.statusIcon` | 3 input states, floating labels, left/right icons, helper text |
| `ProductCard.module.css` | `.card`, `.imageContainer`, `.skeleton`, `.productImage`, `.gradientOverlay`, `.discountBadge`, `.statusBadges`, `.topActions`, `.wishlistButton`, `.quickViewButton`, `.cardBody`, `.categoryRating`, `.rating`, `.productName`, `.priceSection`, `.addToCartButton*`, `.modal*` | Image zoom on hover, skeleton loading, discount/status badges, quick view modal, add-to-cart states |
| `TickerBar.module.css` | `.tickerBar`, `.accentLine`, `.fadeLeft`, `.fadeRight`, `.marquee`, `.tickerItem`, `.tickerContent`, `.icon`, `.text`, `.separator` | Infinite marquee, edge fade gradients, accent gradient line |

---

## Part 7: File Copy Commands

Run these commands to copy the files from F: to D::

```powershell
# Create directories if needed
New-Item -ItemType Directory -Force -Path "D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components"

# Copy CSS module files
Copy-Item "F:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\Button.module.css" -Destination "D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\Button.module.css"
Copy-Item "F:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\Input.module.css" -Destination "D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\Input.module.css"
Copy-Item "F:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\ProductCard.module.css" -Destination "D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\ProductCard.module.css"
Copy-Item "F:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\TickerBar.module.css" -Destination "D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\components\TickerBar.module.css"

# Copy root tailwind config
Copy-Item "F:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\tailwind.config.js" -Destination "D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\tailwind.config.js"
```

---

*End of report.*
