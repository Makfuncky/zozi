"use client";

import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  ShoppingBag,
  Sparkles,
  Tag,
  Star,
  Camera,
  Mic,
  X,
  ChevronDown,
  Zap,
  TrendingUp,
  Package2,
  ArrowLeft,
  History,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useSearchHistory } from "@/hooks/useSearchHistory";

// ── Category definitions ────────────────────────────────────────────────
const CATEGORIES = [
  { value: "all", label: "All Products", icon: ShoppingBag },
  { value: "electronics", label: "Electronics", icon: Zap },
  { value: "fashion", label: "Fashion", icon: Sparkles },
  { value: "accessories", label: "Accessories", icon: Star },
  { value: "furniture", label: "Furniture", icon: Package2 },
  { value: "beauty", label: "Beauty", icon: Sparkles },
  { value: "sports", label: "Sports", icon: TrendingUp },
  { value: "home", label: "Home & Living", icon: ShoppingBag },
  { value: "books", label: "Books", icon: Sparkles },
  { value: "baby", label: "Baby & Kids", icon: Star },
  { value: "automotive", label: "Automotive", icon: Zap },
  { value: "crafts", label: "Crafts", icon: Sparkles },
  { value: "grocery", label: "Grocery", icon: ShoppingBag },
];

const PRICE_PRESETS = [
  { label: "Under $25", min: "", max: "25" },
  { label: "$25 – $100", min: "25", max: "100" },
  { label: "$100 – $250", min: "100", max: "250" },
  { label: "$250+", min: "250", max: "" },
];

const RATING_OPTIONS = ["4", "3", "2", "1"];

// ── Props ──────────────────────────────────────────────────────────────
interface MobileSearchOverlayProps {
  open: boolean;
  onClose: () => void;
  search: string;
  onSetSearch: (v: string) => void;
  category: string;
  onSetCategory: (v: string) => void;
  minPrice: string;
  maxPrice: string;
  onSetMinPrice: (v: string) => void;
  onSetMaxPrice: (v: string) => void;
  minRating: string;
  onSetMinRating: (v: string) => void;
  sort: string;
  onSetSort: (v: string) => void;
  supplier: string;
  onSetSupplier: (v: string) => void;
  onImageSearch?: () => void;
}

// ── Speech check ───────────────────────────────────────────────────────
function isSpeechSupported(): boolean {
  return typeof window !== "undefined" && (
    "SpeechRecognition" in window || "webkitSpeechRecognition" in window
  );
}

// ── Overlay overlay variants ───────────────────────────────────────────
const overlayVariants = {
  hidden: { y: "100%", opacity: 0 },
  visible: { y: 0, opacity: 1 },
  exit: { y: "100%", opacity: 0 },
};

const overlayTransition = {
  type: "spring" as const,
  damping: 32,
  stiffness: 400,
  mass: 0.8,
};

// ── Helper: stars ──────────────────────────────────────────────────────
function renderStars(value: string, max = 5) {
  const parsed = Number.parseInt(value, 10);
  const filled = Number.isFinite(parsed) ? Math.max(0, Math.min(max, parsed)) : 0;
  const empty = Math.max(0, max - filled);
  return `${"★".repeat(filled)}${"☆".repeat(empty)}`;
}

// ═══════════════════════════════════════════════════════════════════════════
//  FILTER CHIP (reusable inline chip for the mobile overlay)
// ═══════════════════════════════════════════════════════════════════════════
function FilterChip({
  label,
  active,
  onClick,
  icon,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  icon?: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[12px] font-medium transition-all duration-150 ${
        active
          ? "bg-primary/20 text-primary border-primary/30 shadow-sm"
          : "bg-surface-1 text-text-muted border-border hover:border-primary/30 hover:text-text"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
//  CATEGORIES SHEET (expandable section inside the overlay)
// ═══════════════════════════════════════════════════════════════════════════
function CategorySheet({
  category,
  onSetCategory,
}: {
  category: string;
  onSetCategory: (v: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const activeCat = CATEGORIES.find((c) => c.value === category) ?? CATEGORIES[0];
  const ActiveIcon = activeCat.icon;

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between text-sm font-medium text-text"
      >
        <span className="flex items-center gap-2">
          <ActiveIcon className="w-4 h-4 text-primary" />
          <span>{activeCat.label}</span>
        </span>
        <ChevronDown className={`w-4 h-4 text-text-faint transition-transform ${expanded ? "rotate-180" : ""}`} />
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="flex flex-wrap gap-1.5 pt-1">
              {CATEGORIES.map((cat) => {
                const CatIcon = cat.icon;
                return (
                  <FilterChip
                    key={cat.value}
                    label={cat.label}
                    active={category === cat.value}
                    onClick={() => { onSetCategory(cat.value); setExpanded(false); }}
                    icon={<CatIcon className="w-3 h-3" />}
                  />
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
//  MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════
export default function MobileSearchOverlay({
  open,
  onClose,
  search,
  onSetSearch,
  category,
  onSetCategory,
  minPrice,
  maxPrice,
  onSetMinPrice,
  onSetMaxPrice,
  minRating,
  onSetMinRating,
  sort,
  onSetSort,
  supplier,
  onSetSupplier,
  onImageSearch,
}: MobileSearchOverlayProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [autocomplete, setAutocomplete] = useState<string[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [showTrending, setShowTrending] = useState(false);
  const [trending, setTrending] = useState<string[]>([]);

  const { items: historyItems, addToHistory, removeFromHistory, clearHistory } = useSearchHistory();

  // Focus input on open
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 300);
      // Fetch trending searches
      apiFetch("/search/trending?limit=5")
        .then((r) => r.ok ? r.json() : { queries: [] })
        .then((d) => setTrending(d.queries ?? []))
        .catch(() => {});
    }
  }, [open]);

  // Debounced autocomplete
  useEffect(() => {
    if (!open || search.trim().length < 2) {
      setAutocomplete([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await apiFetch(
          `/search/autocomplete?q=${encodeURIComponent(search)}&limit=6`,
          { disableCache: true },
        );
        if (res.ok) {
          const data = await res.json();
          setAutocomplete(data.suggestions ?? []);
        }
      } catch { /* ignore */ }
    }, 200);
    return () => clearTimeout(timer);
  }, [search, open]);

  // Commit search: navigate to /products with all active filters
  const commitSearch = useCallback((query?: string) => {
    const q = query ?? search.trim();
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (category && category !== "all") params.set("category", category);
    if (minPrice) params.set("minPrice", minPrice);
    if (maxPrice) params.set("maxPrice", maxPrice);
    if (minRating) params.set("minRating", minRating);
    if (sort && sort !== "default") params.set("sort", sort);
    if (supplier) params.set("supplier", supplier);
    const qs = params.toString();
    // Record in search history
    if (q) addToHistory(q);
    onClose();
    router.push(`/products${qs ? `?${qs}` : ""}`);
  }, [search, category, minPrice, maxPrice, minRating, sort, supplier, router, onClose, addToHistory]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      commitSearch();
    }
  };

  // Voice search
  const startVoiceSearch = useCallback(() => {
    if (!isSpeechSupported()) return;
    setIsListening(true);
    try {
      const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SR();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        onSetSearch(transcript);
        setIsListening(false);
        setTimeout(() => commitSearch(transcript), 300);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognition.start();
    } catch { setIsListening(false); }
  }, [onSetSearch, commitSearch]);

  const activeFilterCount = [
    category !== "all", !!minPrice, !!maxPrice, !!minRating, sort !== "default", !!supplier,
  ].filter(Boolean).length;

  const clearAllFilters = () => {
    onSetCategory("all");
    onSetMinPrice("");
    onSetMaxPrice("");
    onSetMinRating("");
    onSetSort("default");
    onSetSupplier("");
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[200] bg-black/40 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Overlay panel — slides up from bottom */}
          <motion.div
            variants={overlayVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={overlayTransition}
            className="fixed inset-x-0 bottom-0 z-[201] max-h-[92vh] flex flex-col rounded-t-2xl bg-surface-base border-t border-border shadow-2xl safe-area-inset-bottom"
            style={{ maxHeight: "92dvh" }}
          >
            {/* ── Handle bar ──────────────────────── */}
            <div className="flex items-center justify-center pt-2 pb-1 shrink-0">
              <div className="w-10 h-1 rounded-full bg-border" />
            </div>

            {/* ── Header row ──────────────────────── */}
            <div className="flex items-center justify-between px-4 pb-2 shrink-0">
              <button
                type="button"
                onClick={onClose}
                className="flex items-center gap-1 text-sm text-text-muted hover:text-text transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                Back
              </button>
              <span className="text-sm font-semibold text-text">Search</span>
              {activeFilterCount > 0 && (
                <button
                  type="button"
                  onClick={clearAllFilters}
                  className="text-xs text-danger hover:text-danger/80 transition-colors"
                >
                  Clear all
                </button>
              )}
              {activeFilterCount === 0 && <div className="w-16" />}
            </div>

            {/* ── Search input row ────────────────── */}
            <div className="px-4 pb-3 shrink-0">
              <div className="relative flex items-center rounded-xl border border-border bg-surface-1 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/10 transition-all">
                <Search className="pointer-events-none absolute left-3 w-4 h-4 text-text-faint" />
                <input
                  ref={inputRef}
                  type="text"
                  value={search}
                  onChange={(e) => {
                    onSetSearch(e.target.value);
                    setShowTrending(false);
                  }}
                  onFocus={() => {
                    if (!search.trim() && trending.length > 0) setShowTrending(true);
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder={trending.length > 0 && !search
                    ? `Try: ${trending.slice(0, 3).join(", ")}`
                    : "Search products, brands, suppliers..."
                  }
                  className="flex-1 h-11 bg-transparent pl-9 pr-8 text-sm text-text placeholder:text-text-faint focus:outline-none"
                />
                {search && (
                  <button
                    type="button"
                    onClick={() => { onSetSearch(""); setAutocomplete([]); inputRef.current?.focus(); }}
                    className="absolute right-2 p-1 text-text-faint hover:text-text transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {/* ── Autocomplete / Trending / History ──── */}
            <div className="px-4 shrink-0">
              {/* History section (only when input is empty) */}
              {historyItems.length > 0 && !search.trim() && !showTrending && (
                <div className="mb-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-text-faint">
                      <History className="w-3 h-3" />
                      Recent Searches
                    </span>
                    <button
                      type="button"
                      onClick={clearHistory}
                      className="text-[11px] text-danger hover:text-danger/80 transition-colors"
                    >
                      Clear all
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {historyItems.slice(0, 10).map((q) => (
                      <FilterChip
                        key={q}
                        label={q}
                        active={false}
                        onClick={() => { onSetSearch(q); commitSearch(q); }}
                        icon={<History className="w-3 h-3" />}
                      />
                    ))}
                  </div>
                </div>
              )}

              <AnimatePresence>
                {showTrending && trending.length > 0 && !search.trim() && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden mb-2"
                  >
                    <div className="flex items-center gap-1.5 mb-2 text-[11px] font-semibold uppercase tracking-wider text-text-faint">
                      <TrendingUp className="w-3 h-3 text-danger" />
                      Trending
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {trending.map((term) => (
                        <FilterChip
                          key={term}
                          label={term}
                          active={false}
                          onClick={() => { onSetSearch(term); setShowTrending(false); commitSearch(term); }}
                          icon={<TrendingUp className="w-3 h-3" />}
                        />
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* History when typing — filtered by current input */}
              {search.trim().length >= 1 && historyItems.some(h => h.toLowerCase().includes(search.toLowerCase())) && (
                <div className="mb-3">
                  <div className="flex items-center gap-1.5 mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-text-faint">
                    <History className="w-3 h-3" />
                    Recent
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {historyItems
                      .filter(h => h.toLowerCase().includes(search.toLowerCase()))
                      .slice(0, 5)
                      .map((q) => (
                        <FilterChip
                          key={q}
                          label={q}
                          active={false}
                          onClick={() => { onSetSearch(q); commitSearch(q); }}
                          icon={<History className="w-3 h-3" />}
                        />
                      ))}
                  </div>
                </div>
              )}

              {/* Autocomplete */}
              {autocomplete.length > 0 && search.trim().length >= 2 && (
                <div className="mb-3">
                  <div className="flex items-center gap-1.5 mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-primary">
                    <Sparkles className="w-3 h-3" />
                    Suggestions
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {autocomplete.slice(0, 5).map((s) => (
                      <FilterChip
                        key={s}
                        label={s}
                        active={false}
                        onClick={() => { onSetSearch(s); commitSearch(s); }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* ── Filters section (scrollable) ────── */}
            <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-4">
              {/* Categories */}
              <CategorySheet category={category} onSetCategory={onSetCategory} />

              {/* Price range */}
              <div className="space-y-2">
                <span className="flex items-center gap-1.5 text-sm font-medium text-text">
                  <Tag className="w-4 h-4 text-accent" />
                  Price
                </span>
                {/* Sort chips */}
                <div className="flex gap-1.5">
                  {[
                    { value: "price_asc", label: "Low → High" },
                    { value: "price_desc", label: "High → Low" },
                  ].map(({ value, label }) => (
                    <FilterChip
                      key={value}
                      label={label}
                      active={sort === value}
                      onClick={() => onSetSort(sort === value ? "default" : value)}
                    />
                  ))}
                </div>
                {/* Range presets */}
                <div className="flex flex-wrap gap-1.5">
                  {PRICE_PRESETS.map((p) => (
                    <FilterChip
                      key={p.label}
                      label={p.label}
                      active={minPrice === p.min && maxPrice === p.max}
                      onClick={() => {
                        onSetMinPrice(p.min);
                        onSetMaxPrice(p.max);
                      }}
                    />
                  ))}
                </div>
                {(minPrice || maxPrice) && (
                  <button
                    type="button"
                    onClick={() => { onSetMinPrice(""); onSetMaxPrice(""); }}
                    className="text-xs text-danger hover:text-danger/80 transition-colors"
                  >
                    Clear price
                  </button>
                )}
              </div>

              {/* Rating */}
              <div className="space-y-2">
                <span className="flex items-center gap-1.5 text-sm font-medium text-text">
                  <Star className="w-4 h-4 text-accent" />
                  Rating
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {RATING_OPTIONS.map((r) => (
                    <FilterChip
                      key={r}
                      label={`${renderStars(r)} ${r}+`}
                      active={minRating === r}
                      onClick={() => onSetMinRating(minRating === r ? "" : r)}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* ── Action buttons row ───────────────── */}
            <div className="shrink-0 border-t border-border px-4 py-3 flex items-center gap-2">
              {/* Camera */}
              <button
                type="button"
                onClick={onImageSearch}
                title="Search by image"
                className="flex items-center justify-center w-11 h-11 rounded-xl border border-border bg-surface-1 text-text-faint hover:text-primary hover:border-primary/40 transition-all"
              >
                <Camera className="w-5 h-5" />
              </button>

              {/* Voice */}
              <button
                type="button"
                onClick={startVoiceSearch}
                disabled={!isSpeechSupported()}
                title="Voice search"
                className={`flex items-center justify-center w-11 h-11 rounded-xl border border-border bg-surface-1 transition-all ${
                  isListening
                    ? "text-danger border-danger/40 bg-danger/10 animate-pulse"
                    : "text-text-faint hover:text-primary hover:border-primary/40"
                } disabled:opacity-30`}
              >
                <Mic className="w-5 h-5" />
              </button>

              {/* Search button */}
              <button
                type="button"
                onClick={() => commitSearch()}
                className="flex-1 flex items-center justify-center gap-2 h-11 rounded-xl theme-btn-primary text-sm font-semibold transition-colors"
              >
                <Search className="w-4 h-4" />
                {activeFilterCount > 0
                  ? `Search (${activeFilterCount} filter${activeFilterCount > 1 ? "s" : ""})`
                  : "Search"}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
