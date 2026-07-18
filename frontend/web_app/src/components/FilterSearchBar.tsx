"use client";

import { Button } from "@/components/ui/Button";

/**
 * FilterSearchBar — dedicated filter + search bar component.
 *
 * Key fixes baked in:
 *  • Uses `.glass-dropdown` (in @layer components) for all floating panels so
 *    Tailwind's `absolute` / `overflow` utilities are NOT overridden by
 *    unlayered CSS – fixing the "bar expands instead of dropdown floating" bug.
 *  • `glass-search` is applied ONLY to the bar container, NOT to the input.
 *  • Outer wrapper carries `z-[60]` so the filter bar stacks above page content.
 *  • All dropdowns use `z-[999]` consistently.
 *  • RTL support via `dir` attribute + logical CSS properties throughout.
 *  • Component owns its dropdown-visibility state and outside-click handling.
 */

import {
  useRef,
  useState,
  useEffect,
  useMemo,
  type MouseEvent as ReactMouseEvent,
  memo,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Tag,
  Percent,
  Store,
  Sparkles,
  TrendingUp,
  Star,
  ShoppingBag,
  X,
  ChevronDown,
  Camera,
  Zap,
  CheckCircle,
  Bell,
  Filter,
  Package2,
} from "@/lib/icons";
import { isRtlLocale } from "@shared/localization";
import type { TranslationKey } from "@/lib/i18n";
import { supplierStorefrontPath } from "@/lib/utils";
import type { SupplierPublicSummary } from "@/lib/types";

const Check = CheckCircle;

/* ─── Category definitions (exported so page.tsx FiltersPanel can reuse) ─── */
export const CATEGORIES: {
  value: string;
  labelKey: TranslationKey;
  icon: React.ElementType;
}[] = [
  { value: "all",         labelKey: "allProducts",  icon: ShoppingBag },
  { value: "electronics", labelKey: "electronics",  icon: Zap         },
  { value: "fashion",     labelKey: "fashion",      icon: Sparkles    },
  { value: "accessories", labelKey: "accessories",  icon: Star        },
  { value: "furniture",   labelKey: "furniture",    icon: Package2    },
  { value: "beauty",      labelKey: "beauty",       icon: Sparkles    },
  { value: "sports",      labelKey: "sports",       icon: TrendingUp  },
  { value: "home",        labelKey: "homeLiving",   icon: ShoppingBag },
  { value: "books",       labelKey: "books",        icon: Sparkles    },
  { value: "baby",        labelKey: "babyKids",     icon: Star        },
  { value: "automotive",  labelKey: "automotive",   icon: Zap         },
  { value: "crafts",      labelKey: "crafts",       icon: Sparkles    },
  { value: "grocery",     labelKey: "grocery",      icon: ShoppingBag },
];

function renderStars(value: string, max = 5) {
  const parsed = Number.parseInt(value, 10);
  const filled = Number.isFinite(parsed) ? Math.max(0, Math.min(max, parsed)) : 0;
  const empty = Math.max(0, max - filled);
  return `${"★".repeat(filled)}${"☆".repeat(empty)}`;
}

/* ─── Props ─────────────────────────────────────────────────────────────── */
export interface FilterSearchBarProps {
  /** Filter values */
  category: string;
  sort: string;
  minPrice: string;
  maxPrice: string;
  minRating: string;
  discountPct: string;
  newArrivals: boolean;
  trendingOnly: boolean;
  activeFilterCount: number;

  /** Filter callbacks */
  onSetCategory: (v: string) => void;
  onSetSort: (v: string) => void;
  onSetMinPrice: (v: string) => void;
  onSetMaxPrice: (v: string) => void;
  onSetMinRating: (v: string) => void;
  onSetDiscountPct: (v: string) => void;
  onToggleNewArrivals: () => void;
  onToggleTrending: () => void;
  onResetFilters: () => void;

  /** Search */
  search: string;
  onSetSearch: (v: string) => void;
  suggestions: string[];
  supplierSuggestions: SupplierPublicSummary[];
  showSuggestions: boolean;
  onSetShowSuggestions: (v: boolean) => void;
  onCommitSearch: () => void;
  onImageSearch: () => void;

  /** Supplier */
  supplierSearch: string;
  onSetSupplierSearch: (v: string) => void;
  supplierNames: string[];
  selectedSuppliers: string[];
  onToggleSupplier: (name: string) => void;
  onClearSuppliers: () => void;

  /** Computed helpers */
  presetRanges: Array<{ label: string; min: string; max: string }>;

  /** I18n / currency */
  tr: (key: TranslationKey) => string;
  formatCurrent: (n: number) => string;
  currency: { code: string };

  /** Navigation */
  router: { push: (url: string) => void };

  /** Current locale (for RTL detection) */
  locale: string;

  /** Reset pagination when a filter changes */
  onResetVisibleCount: () => void;

  /** Optional route-specific styling for the outer shell */
  searchShellClassName?: string;
  searchShellTestId?: string;
}

/* ─── Dropdown visibility state ─────────────────────────────────────────── */
type DropKey = "category" | "price" | "rating" | "discount";
const CLOSED_DROPS: Record<DropKey, boolean> = {
  category: false,
  price: false,
  rating: false,
  discount: false,
};

/* ─── Framer variants ────────────────────────────────────────────────────── */
const dropVariants = {
  hidden: { opacity: 0, y: 6, scale: 0.97 },
  show:   { opacity: 1, y: 0, scale: 1    },
  exit:   { opacity: 0, y: 6, scale: 0.97 },
};
const dropTransition = { duration: 0.14, ease: [0.16, 1, 0.3, 1] as const };

/* ─── Component ──────────────────────────────────────────────────────────── */
function FilterSearchBar({
  category, sort, minPrice, maxPrice, minRating, discountPct,
  newArrivals, trendingOnly, activeFilterCount,
  onSetCategory, onSetSort, onSetMinPrice, onSetMaxPrice,
  onSetMinRating, onSetDiscountPct,
  onToggleNewArrivals, onToggleTrending, onResetFilters,
  search, onSetSearch, suggestions, supplierSuggestions,
  showSuggestions, onSetShowSuggestions, onCommitSearch, onImageSearch,
  supplierSearch, onSetSupplierSearch, supplierNames,
  selectedSuppliers, onToggleSupplier, onClearSuppliers,
  presetRanges, tr, formatCurrent, currency,
  router, locale, onResetVisibleCount,
  searchShellClassName = "",
  searchShellTestId,
}: FilterSearchBarProps) {
  const isRtl = isRtlLocale(locale);

  /* -- Dropdown open state -- */
  const [open, setOpen] = useState<Record<DropKey, boolean>>(CLOSED_DROPS);
  const [showSupplierSuggest, setShowSupplierSuggest] = useState(false);

  const toggleDrop = (key: DropKey) =>
    setOpen((prev) => ({ ...CLOSED_DROPS, [key]: !prev[key] }));
  const closeAll = () => {
    setOpen(CLOSED_DROPS);
    setShowSupplierSuggest(false);
  };

  /* -- Outside-click refs -- */
  const categoryRef = useRef<HTMLDivElement>(null);
  const priceRef    = useRef<HTMLDivElement>(null);
  const ratingRef   = useRef<HTMLDivElement>(null);
  const discountRef = useRef<HTMLDivElement>(null);
  const supplierRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handle = (e: MouseEvent) => {
      const allRefs = [categoryRef, priceRef, ratingRef, discountRef, supplierRef];
      const inside = allRefs.some((r) => r.current?.contains(e.target as Node));
      if (!inside) closeAll();
    };
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, []);

  /* -- Derived -- */
  const activeCat = useMemo(
    () => CATEGORIES.find((c) => c.value === category) ?? CATEGORIES[0],
    [category],
  );
  const CurrentCategoryIcon = activeCat.icon;

  const fuzzySuppliers = useMemo(
    () =>
      supplierSearch
        ? supplierNames.filter((s) =>
            s.toLowerCase().includes(supplierSearch.toLowerCase()),
          )
        : supplierNames,
    [supplierNames, supplierSearch],
  );

  /* ── Shared class helpers ──────────────────────────────────── */
  // Divider between bar sections. Uses logical `border-e` (= border-right in LTR).
  const divider = "border-e border-border shrink-0";

  /* ── Dropdown panel base: glass-dropdown + absolute positioning ── */
  // Note: glass-dropdown is in @layer components so `absolute`, `z-*`,
  // `overflow-*` Tailwind utilities correctly override it.
  const panelBase =
    "glass-dropdown absolute top-[calc(100%+6px)] z-[999] rounded-2xl overflow-hidden";
  const panelStart = `${panelBase} start-0`; // logical: left in LTR, right in RTL

  return (
    <div dir={isRtl ? "rtl" : "ltr"} className="relative z-60 w-full max-w-2xl mx-auto">
      {/* ══════════════════════════════════════════════
          FILTER + SEARCH BAR
      ══════════════════════════════════════════════ */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
      >
        {/* Glass bar */}
        <div className="group relative w-full">
          <div
            data-testid={searchShellTestId}
            aria-hidden="true"
            className={[
              "glass-search",
              searchShellClassName,
              "pointer-events-none absolute inset-0 rounded-[1.6rem]",
              "transition-shadow duration-300",
              "group-focus-within:border-primary/60",
              "group-focus-within:ring-2 group-focus-within:ring-primary/20",
            ].join(" ")}
          />
          <div className="relative flex items-stretch rounded-[1.6rem]">
          {/* ─── Category ─────────────────────────────────────── */}
          <div ref={categoryRef} className={`relative ${divider}`}>
            <button
              type="button"
              onClick={() => toggleDrop("category")}
              className="flex h-12 items-center gap-1.5 whitespace-nowrap rounded-s-[1.6rem] ps-4 pe-3 text-sm font-medium text-text-muted transition-colors duration-200 hover:bg-surface-2/50 hover:text-text"
              aria-expanded={open.category}
              aria-haspopup="listbox"
            >
              <CurrentCategoryIcon className="h-3.5 w-3.5 shrink-0 text-primary" />
              <span className="hidden max-w-28 truncate sm:inline">
                {category === "all"
                  ? tr("categoriesLabel")
                  : tr(activeCat.labelKey)}
              </span>
              <ChevronDown
                className={`h-3.5 w-3.5 text-text-faint transition-transform duration-200 ${
                  open.category ? "rotate-180" : ""
                }`}
              />
            </button>

            <AnimatePresence>
              {open.category && (
                <motion.ul
                  role="listbox"
                  variants={dropVariants}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                  transition={dropTransition}
                  className={`${panelStart} w-56 max-h-[70vh] overflow-y-auto`}
                >
                  <li className="flex items-center gap-2 border-b border-border px-4 py-2 text-[10px] font-semibold uppercase tracking-widest text-text-faint">
                    <Filter className="h-3 w-3 text-primary" />
                    {tr("department")}
                  </li>
                  {CATEGORIES.map((cat) => {
                    const CatIcon = cat.icon;
                    const active = category === cat.value;
                    return (
                      <motion.li
                        key={cat.value}
                        whileHover={{ x: isRtl ? -3 : 3 }}
                        transition={{ duration: 0.1 }}
                      >
                        <button
                          type="button"
                          role="option"
                          aria-selected={active}
                          onClick={() => {
                            onSetCategory(cat.value);
                            closeAll();
                            onResetVisibleCount();
                          }}
                          className={`flex w-full items-center gap-2.5 px-4 py-2.5 text-sm transition-colors duration-150 ${
                            active
                              ? "bg-primary/15 text-primary"
                              : "text-text-muted hover:bg-surface-2 hover:text-text"
                          }`}
                        >
                          <CatIcon
                            className={`h-3.5 w-3.5 shrink-0 ${
                              active ? "text-primary" : "text-text-faint"
                            }`}
                          />
                          {tr(cat.labelKey)}
                          {active && (
                            <Check className="ms-auto h-3.5 w-3.5 text-primary" />
                          )}
                        </button>
                      </motion.li>
                    );
                  })}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>

          {/* ─── Price ────────────────────────────────────────── */}
          <div ref={priceRef} className={`relative ${divider}`}>
            <button
              type="button"
              onClick={() => toggleDrop("price")}
              aria-label="Price filter"
              className={`flex h-12 items-center gap-1.5 px-3 text-sm font-medium transition-colors duration-200 hover:bg-surface-2/50 ${
                minPrice || maxPrice ? "text-primary" : "text-text-muted hover:text-text"
              }`}
              aria-expanded={open.price}
            >
              <Tag className="h-3.5 w-3.5 shrink-0 text-accent" />
              <span className="hidden md:inline whitespace-nowrap">
                {minPrice || maxPrice
                  ? `${minPrice ? formatCurrent(Number(minPrice)) : ""}${
                      minPrice && maxPrice ? " – " : ""
                    }${maxPrice ? formatCurrent(Number(maxPrice)) : "+"}`
                  : tr("price")}
              </span>
              <ChevronDown
                className={`h-3.5 w-3.5 transition-transform duration-200 ${
                  open.price ? "rotate-180" : ""
                }`}
              />
            </button>

            <AnimatePresence>
              {open.price && (
                <motion.div
                  variants={dropVariants}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                  transition={dropTransition}
                  className={`${panelStart} w-52 p-3`}
                >
                  <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-text-faint">
                    Sort Direction
                  </p>
                  <div className="mb-3 flex flex-wrap gap-1">
                    {(
                      [
                        { value: "price:asc",  label: "Low to High" },
                        { value: "price:desc", label: "High to Low" },
                      ] as const
                    ).map(({ value, label }) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => {
                          onSetSort(sort === value ? "default" : value);
                          onResetVisibleCount();
                        }}
                        className={`rounded-full border px-2.5 py-1 text-[10px] transition-colors duration-150 ${
                          sort === value
                            ? "border-primary/30 bg-primary/20 text-primary"
                            : "border-border text-text-muted hover:text-text"
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>

                  <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-text-faint">
                    {tr("priceRange")}
                  </p>
                  {(() => {
                    const PRICE_FLOOR = 0;
                    const PRICE_CEIL = 100000;
                    const step = Math.max(1, Math.round((PRICE_CEIL - PRICE_FLOOR) / 100));
                    const loNum = minPrice ? Number(minPrice) : PRICE_FLOOR;
                    const hiNum = maxPrice ? Number(maxPrice) : PRICE_CEIL;
                    const lo = Math.min(Math.max(loNum, PRICE_FLOOR), PRICE_CEIL);
                    const hi = Math.max(Math.min(hiNum, PRICE_CEIL), PRICE_FLOOR);
                    const pctMin = ((lo - PRICE_FLOOR) / (PRICE_CEIL - PRICE_FLOOR)) * 100;
                    const pctMax = ((hi - PRICE_FLOOR) / (PRICE_CEIL - PRICE_FLOOR)) * 100;
                    return (
                      <div className="mb-3">
                        <div className="theme-range-dual" role="group" aria-label="Price range">
                          <div className="theme-range-track">
                            <div className="theme-range-track-fill" style={{ left: `${pctMin}%`, right: `${100 - pctMax}%` }} />
                          </div>
                          <input
                            type="range"
                            className="theme-range"
                            min={PRICE_FLOOR}
                            max={PRICE_CEIL}
                            step={step}
                            value={lo}
                            aria-label="Minimum price"
                            onChange={(e) => {
                              const next = Math.min(Number(e.target.value), hi - step);
                              onSetMinPrice(next > PRICE_FLOOR ? String(next) : "");
                              onResetVisibleCount();
                            }}
                          />
                          <input
                            type="range"
                            className="theme-range"
                            min={PRICE_FLOOR}
                            max={PRICE_CEIL}
                            step={step}
                            value={hi}
                            aria-label="Maximum price"
                            onChange={(e) => {
                              const next = Math.max(Number(e.target.value), lo + step);
                              onSetMaxPrice(next < PRICE_CEIL ? String(next) : "");
                              onResetVisibleCount();
                            }}
                          />
                        </div>
                        <div className="mt-1 flex justify-between text-[10px] text-text-faint">
                          <span>{formatCurrent(lo)}</span>
                          <span>{formatCurrent(hi)}</span>
                        </div>
                      </div>
                    );
                  })()}
                  <div className="mb-2 flex gap-2">
                    <input
                      type="number"
                      placeholder={`Min ${currency.code}`}
                      value={minPrice}
                      onChange={(e) => onSetMinPrice(e.target.value)}
                      className="h-8 w-full rounded-lg border border-border bg-surface-2 px-2 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary/40"
                    />
                    <input
                      type="number"
                      placeholder={`Max ${currency.code}`}
                      value={maxPrice}
                      onChange={(e) => onSetMaxPrice(e.target.value)}
                      className="h-8 w-full rounded-lg border border-border bg-surface-2 px-2 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary/40"
                    />
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {presetRanges.map(({ label, min: mn, max: mx }) => (
                      <button
                        key={label}
                        type="button"
                        onClick={() => {
                          onSetMinPrice(mn);
                          onSetMaxPrice(mx);
                          closeAll();
                          onResetVisibleCount();
                        }}
                        className={`rounded-full border px-2.5 py-1 text-[10px] transition-colors duration-150 ${
                          minPrice === mn && maxPrice === mx
                            ? "border-primary/30 bg-primary/20 text-primary"
                            : "border-border text-text-muted hover:text-text"
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                    {(minPrice || maxPrice) && (
                      <Button variant="danger" className="rounded-full border border-danger/30 px-2.5 py-1 text-[10px] text-danger transition-colors duration-150" type="button"
                        onClick={() => {
                          onSetMinPrice("");
                          onSetMaxPrice("");
                          if (sort === "price:asc" || sort === "price:desc")
                            onSetSort("default");
                          closeAll();
                        }}
                      >
                        Clear
                      </Button>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* ─── Rating ───────────────────────────────────────── */}
          <div ref={ratingRef} className={`relative ${divider}`}>
            <button
              type="button"
              onClick={() => toggleDrop("rating")}
              className={`flex h-12 items-center gap-1.5 px-3 text-sm font-medium transition-colors duration-200 hover:bg-surface-2/50 ${
                minRating ? "text-warning" : "text-text-muted hover:text-text"
              }`}
              aria-expanded={open.rating}
            >
              <Star className="h-3.5 w-3.5 shrink-0 text-accent" />
              <span className="hidden md:inline whitespace-nowrap">
                {minRating ? `${minRating}+` : tr("rating")}
              </span>
              <ChevronDown
                className={`h-3.5 w-3.5 transition-transform duration-200 ${
                  open.rating ? "rotate-180" : ""
                }`}
              />
            </button>

            <AnimatePresence>
              {open.rating && (
                <motion.ul
                  variants={dropVariants}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                  transition={dropTransition}
                  className={`${panelStart} w-44`}
                >
                  <li className="border-b border-border px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-text-faint">
                    {tr("minRating")}
                  </li>
                  {(["4", "3", "2", "1"] as const).map((r) => (
                    <li key={r}>
                      <button
                        type="button"
                        onClick={() => {
                          onSetMinRating(minRating === r ? "" : r);
                          closeAll();
                          onResetVisibleCount();
                        }}
                        className={`flex w-full items-center gap-2 px-3 py-2 text-xs transition-colors duration-150 ${
                          minRating === r
                            ? "bg-warning/15 text-warning"
                            : "text-text-muted hover:bg-surface-2 hover:text-text"
                        }`}
                      >
                        <span className="text-warning">
                          {renderStars(r)}
                        </span>
                        {r}+ {tr("starsSuffix")}
                        {minRating === r && (
                          <span className="ms-auto text-xs text-warning">✓</span>
                        )}
                      </button>
                    </li>
                  ))}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>

          {/* ─── Supplier (hidden on mobile) ──────────────────── */}
          <div
            ref={supplierRef}
            className={`relative hidden sm:flex items-center w-40 lg:w-48 ${divider}`}
          >
            <Store className="pointer-events-none absolute inset-s-3 z-10 h-3.5 w-3.5 text-primary/70" />
            <input
              type="text"
              value={supplierSearch}
              onChange={(e) => {
                onSetSupplierSearch(e.target.value);
                setShowSupplierSuggest(true);
              }}
              onFocus={() => setShowSupplierSuggest(true)}
              placeholder={
                selectedSuppliers.length > 0
                  ? `${selectedSuppliers.length} selected`
                  : tr("supplierFilter")
              }
              className="h-12 w-full bg-transparent ps-8 pe-7 text-xs text-text placeholder:text-text-faint focus:outline-none"
            />
            {selectedSuppliers.length > 0 && (
              <button
                type="button"
                onClick={onClearSuppliers}
                className="absolute inset-e-2 p-0.5 text-text-faint transition-colors hover:text-text"
              >
                <X className="h-3 w-3" />
              </button>
            )}

            <AnimatePresence>
              {showSupplierSuggest && fuzzySuppliers.length > 0 && (
                <motion.ul
                  variants={dropVariants}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                  transition={dropTransition}
                  className={`${panelStart} max-h-52 w-56 overflow-y-auto`}
                >
                  <li className="flex items-center gap-2 border-b border-border px-4 py-1.5 text-[10px] text-text-faint">
                    <Store className="h-3 w-3" />
                    {tr("allSuppliers")}
                  </li>
                  {fuzzySuppliers.map((s, i) => (
                    <motion.li
                      key={s}
                      initial={{ opacity: 0, x: isRtl ? 4 : -4 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.03 }}
                      onMouseDown={(e: ReactMouseEvent<HTMLLIElement>) => {
                        e.preventDefault();
                        onToggleSupplier(s);
                      }}
                      className={`flex cursor-pointer items-center gap-2 px-4 py-2 text-xs transition-colors duration-150 ${
                        selectedSuppliers.includes(s)
                          ? "bg-primary/15 text-primary"
                          : "text-text-muted hover:bg-surface-2 hover:text-text"
                      }`}
                    >
                      <Store className="h-3 w-3 shrink-0 text-text-faint" />
                      {s}
                      {selectedSuppliers.includes(s) && (
                        <Check className="ms-auto h-3 w-3 text-primary" />
                      )}
                    </motion.li>
                  ))}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>

          {/* ─── Search input ─────────────────────────────────── */}
          <div className="relative flex flex-1 items-center gap-2 px-4 min-w-0">
            <Sparkles className="h-4 w-4 shrink-0 text-primary" />
            <input
              type="text"
              value={search}
              onChange={(e) => onSetSearch(e.target.value)}
              onFocus={() => onSetShowSuggestions(true)}
              onBlur={() => setTimeout(() => onSetShowSuggestions(false), 150)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  onCommitSearch();
                }
              }}
              placeholder={tr("searchProductsBrandsSuppliers")}
              /* ⚠️  No glass-search here — that class belongs on the container */
              className="h-12 min-w-0 flex-1 bg-transparent text-sm text-text placeholder:text-text-faint focus:outline-none"
            />
            {search && (
              <button
                type="button"
                onClick={() => onSetSearch("")}
                className="rounded-lg p-1 text-text-faint transition-colors hover:text-text"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}

            {/* Autocomplete dropdown */}
            <AnimatePresence>
              {showSuggestions &&
                (suggestions.length > 0 || supplierSuggestions.length > 0) && (
                  <motion.ul
                    variants={dropVariants}
                    initial="hidden"
                    animate="show"
                    exit="exit"
                    transition={dropTransition}
                    className={`${panelStart} min-w-[18rem] w-full`}
                  >
                    <li className="flex items-center gap-2 border-b border-border px-4 py-2 text-[10px] text-primary">
                      <Sparkles className="h-3 w-3" />
                      {tr("aiSuggestions")}
                    </li>

                    {supplierSuggestions.length > 0 && (
                      <>
                        <li className="border-b border-border/70 px-4 py-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-text-faint">
                          Supplier storefronts
                        </li>
                        {supplierSuggestions.map((item, index) => (
                          <motion.li
                            key={`supplier-${item.id}`}
                            initial={{ opacity: 0, x: isRtl ? 4 : -4 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.04 }}
                            onMouseDown={(event: ReactMouseEvent<HTMLLIElement>) => {
                              event.preventDefault();
                              onSetShowSuggestions(false);
                              onSetSearch(item.business_name || item.username);
                              router.push(supplierStorefrontPath(item));
                            }}
                            className="flex cursor-pointer items-start gap-3 px-4 py-2 text-sm text-text-muted transition-colors hover:bg-surface-2"
                          >
                            <Store className="mt-0.5 h-3.5 w-3.5 shrink-0 text-text-faint" />
                            <span className="min-w-0">
                              <span className="block truncate font-semibold text-text">
                                {item.business_name || item.username}
                              </span>
                              <span className="block truncate text-[11px] text-text-faint">
                                {item.username}
                              </span>
                            </span>
                          </motion.li>
                        ))}
                      </>
                    )}

                    {suggestions.length > 0 && (
                      <>
                        <li className="border-y border-border/70 px-4 py-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-text-faint">
                          Products
                        </li>
                        {suggestions.map((s, i) => (
                          <motion.li
                            key={`product-${s}-${i}`}
                            initial={{ opacity: 0, x: isRtl ? 4 : -4 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{
                              delay: (supplierSuggestions.length + i) * 0.04,
                            }}
                            onMouseDown={(e: ReactMouseEvent<HTMLLIElement>) => {
                              e.preventDefault();
                              onSetSearch(s);
                              onSetShowSuggestions(false);
                            }}
                            className="flex cursor-pointer items-center gap-3 px-4 py-2 text-sm text-text-muted transition-colors hover:bg-surface-2"
                          >
                            <Search className="h-3.5 w-3.5 text-text-faint" />
                            {s}
                          </motion.li>
                        ))}
                      </>
                    )}
                  </motion.ul>
                )}
            </AnimatePresence>
          </div>

          {/* ─── Camera search ────────────────────────────────── */}
          <button
            type="button"
            onClick={onImageSearch}
            title={tr("searchByImage")}
            className="border-s border-border px-3 text-text-faint transition-colors duration-200 hover:text-primary"
          >
            <Camera className="h-4 w-4 text-primary/80" />
          </button>

          {/* ─── Notifications ────────────────────────────────── */}
          <a
            href="/notifications"
            className="flex h-12 items-center border-s border-border px-3 text-text-faint transition-colors duration-200 hover:text-primary"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4 text-accent" />
          </a>

          {/* ─── Search button ────────────────────────────────── */}
          <button
            type="button"
            onClick={onCommitSearch}
            className="theme-btn-primary flex h-12 shrink-0 items-center gap-2 rounded-e-[1.6rem] px-5 text-sm font-semibold shadow-lg shadow-primary/25 transition-colors duration-200"
          >
            <Search className="h-4 w-4" />
            <span className="hidden sm:inline">{tr("searchButton")}</span>
          </button>
        </div>
        </div>

        {/* ══════════════════════════════════════════════
            QUICK FILTER PILLS
        ══════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="mt-4 flex flex-wrap items-center justify-center gap-2.5"
        >
          {/* New Arrivals */}
          <button
            type="button"
            onClick={() => {
              onToggleNewArrivals();
              onResetVisibleCount();
            }}
            className={`flex h-8 items-center gap-1.5 rounded-full border px-3.5 text-[11px] font-semibold transition-all duration-200 ${
              newArrivals
                ? "border-info/40 bg-info/20 text-info shadow-lg shadow-info/10"
                : "banner-glass-chip text-text-faint hover:border-border-light hover:text-text"
            }`}
          >
            <Sparkles className={`h-3 w-3 ${newArrivals ? "" : "text-primary/70"}`} />
            {tr("newArrivals")}
          </button>

          {/* Trending */}
          <button
            type="button"
            onClick={() => {
              onToggleTrending();
              onResetVisibleCount();
            }}
            className={`flex h-8 items-center gap-1.5 rounded-full border px-3.5 text-[11px] font-semibold transition-all duration-200 ${
              trendingOnly
                ? "border-danger/40 bg-danger/20 text-danger shadow-lg shadow-danger/10"
                : "banner-glass-chip text-text-faint hover:border-border-light hover:text-text"
            }`}
          >
            <TrendingUp className={`h-3 w-3 ${trendingOnly ? "" : "text-danger/60"}`} />
            {tr("trending")}
          </button>

          {/* Discount % pill with dropdown */}
          <div ref={discountRef} className="relative shrink-0">
            <button
              type="button"
              onClick={() => toggleDrop("discount")}
              className={`flex h-8 items-center gap-1.5 rounded-full border px-3.5 text-[11px] font-semibold transition-all duration-200 ${
                discountPct
                  ? "border-success/40 bg-success/20 text-success shadow-lg shadow-success/10"
                  : "banner-glass-chip text-text-faint hover:border-border-light hover:text-text"
              }`}
              aria-expanded={open.discount}
            >
              <Tag className={`h-3 w-3 ${discountPct ? "" : "text-accent/70"}`} />
              {discountPct ? `${discountPct}%+ Off` : tr("discountPercent")}
              <ChevronDown
                className={`h-3 w-3 transition-transform duration-200 ${
                  open.discount ? "rotate-180" : ""
                }`}
              />
            </button>

            <AnimatePresence>
              {open.discount && (
                <motion.ul
                  variants={dropVariants}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                  transition={dropTransition}
                  className={`${panelStart} w-44`}
                >
                  <li className="border-b border-border px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-text-faint">
                    {tr("minDiscount")}
                  </li>
                  {(["10", "20", "30", "50"] as const).map((val) => (
                    <li key={val}>
                      <button
                        type="button"
                        onClick={() => {
                          onSetDiscountPct(discountPct === val ? "" : val);
                          closeAll();
                          onResetVisibleCount();
                        }}
                        className={`flex w-full items-center gap-2 px-3 py-2 text-xs transition-colors duration-150 ${
                          discountPct === val
                            ? "bg-success/15 text-success"
                            : "text-text-muted hover:bg-surface-2 hover:text-text"
                        }`}
                      >
                        <Percent className="h-3 w-3 text-accent" />
                        {val}%+
                        {discountPct === val && (
                          <Check className="ms-auto h-3 w-3 text-success" />
                        )}
                      </button>
                    </li>
                  ))}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>

          {/* Mobile: show selected supplier count */}
          {selectedSuppliers.length > 0 && (
            <Button variant="primary" type="button"
              onClick={onClearSuppliers}>
              <Store className="h-3 w-3" />
              {selectedSuppliers.length} {tr("supplierFilter")}
              <X className="ms-0.5 h-3 w-3" />
            </Button>
          )}

          {/* Clear all filters */}
          {activeFilterCount > 0 && (
            <Button variant="danger" type="button"
              onClick={onResetFilters}>
              <X className="h-3 w-3" />
              {tr("clearFilters")}
            </Button>
          )}
        </motion.div>
      </motion.div>
    </div>
  );
}

export default memo(FilterSearchBar);
