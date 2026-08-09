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
  Store,
  Camera,
  Mic,
  X,
  ChevronDown,
  Zap,
  TrendingUp,
  Package2,
  CheckCircle,
  Filter,
  History,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import type { SupplierPublicSummary } from "@/lib/types";
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

const PRICE_RANGES = [
  { label: "Under $25", min: "", max: "25" },
  { label: "$25 – $100", min: "25", max: "100" },
  { label: "$100 – $250", min: "100", max: "250" },
  { label: "$250+", min: "250", max: "" },
];

// ── Dropdown variants ─────────────────────────────────────────────────
const dropVariants = {
  hidden: { opacity: 0, y: 6, scale: 0.97 },
  show: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: 6, scale: 0.97 },
};
const dropTransition = { duration: 0.14, ease: [0.16, 1, 0.3, 1] };

// ── Props ──────────────────────────────────────────────────────────────
interface HeaderSearchBarProps {
  search: string;
  onSetSearch: (v: string) => void;
  onCommitSearch?: () => void;
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
  onResetVisibleCount?: () => void;
  onImageSearch?: () => void;
  onVoiceSearch?: () => void;
  supplierSuggestions?: SupplierPublicSummary[];
  suggestions?: string[];
}

type DropKey = "category" | "price" | "rating" | "supplier";

// ── Component ──────────────────────────────────────────────────────────
export default function HeaderSearchBar({
  search, onSetSearch, onCommitSearch,
  category, onSetCategory,
  minPrice, maxPrice, onSetMinPrice, onSetMaxPrice,
  minRating, onSetMinRating,
  sort, onSetSort,
  supplier, onSetSupplier,
  onResetVisibleCount,
  onImageSearch, onVoiceSearch,
  supplierSuggestions = [],
  suggestions = [],
}: HeaderSearchBarProps) {
  const router = useRouter();
  const [openDrop, setOpenDrop] = useState<DropKey | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [localSuggestions, setLocalSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [supplierSearchText, setSupplierSearchText] = useState("");
  const [showSupplierSuggest, setShowSupplierSuggest] = useState(false);

  const { items: historyItems, addToHistory, removeFromHistory, clearHistory } = useSearchHistory();

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const supplierInputRef = useRef<HTMLInputElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpenDrop(null);
        setShowSuggestions(false);
        setShowSupplierSuggest(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Debounced autocomplete for products
  useEffect(() => {
    if (!search.trim() || search.length < 2) {
      setLocalSuggestions([]);
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
          setLocalSuggestions(data.suggestions ?? data ?? []);
        }
      } catch { /* ignore */ }
    }, 200);
    return () => clearTimeout(timer);
  }, [search]);

  // Filter supplier suggestions based on search text
  const filteredSuppliers = useMemo(() => {
    if (!supplierSearchText) return supplierSuggestions.slice(0, 8);
    return supplierSuggestions.filter(s =>
      s.business_name?.toLowerCase().includes(supplierSearchText.toLowerCase()) ||
      s.username?.toLowerCase().includes(supplierSearchText.toLowerCase())
    ).slice(0, 8);
  }, [supplierSuggestions, supplierSearchText]);

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

    const queryString = params.toString();
    router.push(`/products${queryString ? `?${queryString}` : ""}`);
    
    if (q) addToHistory(q);
    
    onSetSearch(q);
    setShowSuggestions(false);
    setShowSupplierSuggest(false);
    setOpenDrop(null);
    onCommitSearch?.();
  }, [search, category, minPrice, maxPrice, minRating, sort, supplier, router, onSetSearch, onCommitSearch, addToHistory]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      commitSearch();
    }
  };

  // Detect speech support after mount (hydration-safe)
  useEffect(() => {
    setSpeechSupported(
      typeof window !== "undefined" && (
        "SpeechRecognition" in window || "webkitSpeechRecognition" in window
      )
    );
  }, []);

  // Voice search with Web Speech API
  const startVoiceSearch = useCallback(() => {
    if (!speechSupported) return;
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
  }, [onSetSearch, commitSearch, speechSupported]);

  const activeCat = CATEGORIES.find((c) => c.value === category) ?? CATEGORIES[0];

  return (
    <div ref={containerRef} className="relative flex-1 max-w-4xl mx-auto">
      {/* Glass search bar */}
      <div className="glass-search rounded-[1.2rem] transition-shadow duration-300 ring-0 focus-within:ring-2 focus-within:ring-primary/20">
        <div className="flex items-center h-12">
          {/* ── Categories dropdown ────────────────── */}
          <div className="relative border-r border-border/50">
            <button
              onClick={() => setOpenDrop(openDrop === "category" ? null : "category")}
              className="flex items-center gap-1.5 px-3 h-12 text-[11px] font-medium text-text-muted hover:text-text transition-colors"
            >
              <activeCat.icon className="w-3.5 h-3.5 text-primary shrink-0" />
              <span className="hidden lg:inline max-w-20 truncate">{activeCat.label}</span>
              <ChevronDown className={`w-3 h-3 transition-transform ${openDrop === "category" ? "rotate-180" : ""}`} />
            </button>
            <AnimatePresence>
              {openDrop === "category" && (
                <motion.div
                  variants={dropVariants}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                  transition={dropTransition}
                  className="absolute top-full left-0 mt-1 w-52 rounded-xl glass-dropdown overflow-hidden z-[999]"
                >
                  <div className="p-1">
                    <div className="flex items-center gap-2 px-3 py-2 text-[10px] font-semibold uppercase tracking-widest text-text-faint border-b border-border">
                      <Filter className="h-3 w-3 text-primary" />
                      Department
                    </div>
                    {CATEGORIES.map((cat) => (
                      <button
                        key={cat.value}
                        onClick={() => { onSetCategory(cat.value); setOpenDrop(null); onResetVisibleCount?.(); }}
                        className={`flex w-full items-center gap-2 px-3 py-2 text-xs transition-colors ${
                          category === cat.value
                            ? "bg-primary/15 text-primary"
                            : "text-text-muted hover:bg-surface-2 hover:text-text"
                        }`}
                      >
                        <cat.icon className="w-3 h-3 shrink-0" />
                        {cat.label}
                        {category === cat.value && <CheckCircle className="ms-auto w-3.5 h-3.5 text-primary" />}
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* ── Price dropdown ─────────────────────── */}
          <div className="relative border-r border-border/50">
            <button
              onClick={() => setOpenDrop(openDrop === "price" ? null : "price")}
              className={`flex items-center gap-1.5 px-3 h-12 text-[11px] font-medium transition-colors ${
                minPrice || maxPrice ? "text-primary" : "text-text-muted hover:text-text"
              }`}
            >
              <Tag className="w-3 h-3 text-accent shrink-0" />
              <span className="hidden lg:inline whitespace-nowrap">
                {minPrice || maxPrice ? `${minPrice || "0"}–${maxPrice || "∞"}` : "Price"}
              </span>
              <ChevronDown className={`w-3 h-3 transition-transform ${openDrop === "price" ? "rotate-180" : ""}`} />
            </button>
            <AnimatePresence>
              {openDrop === "price" && (
                <motion.div
                  variants={dropVariants}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                  transition={dropTransition}
                  className="absolute top-full left-0 mt-1 w-52 rounded-xl glass-dropdown overflow-hidden z-[999]"
                >
                  <div className="p-2 space-y-1">
                    <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-text-faint">
                      Sort Direction
                    </div>
                    <div className="flex flex-wrap gap-1 px-2 mb-2">
                      {[
                        { value: "price_asc", label: "Low to High" },
                        { value: "price_desc", label: "High to Low" },
                      ].map(({ value, label }) => (
                        <button
                          key={value}
                          onClick={() => { onSetSort(sort === value ? "default" : value); onResetVisibleCount?.(); }}
                          className={`rounded-full border px-2.5 py-1 text-[10px] transition-colors ${
                            sort === value
                              ? "border-primary/30 bg-primary/20 text-primary"
                              : "border-border text-text-muted hover:text-text"
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                    
                    <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-text-faint">
                      Price Range
                    </div>
                    {PRICE_RANGES.map((r) => (
                      <button
                        key={r.label}
                        onClick={() => {
                          onSetMinPrice(r.min);
                          onSetMaxPrice(r.max);
                          setOpenDrop(null);
                          onResetVisibleCount?.();
                        }}
                        className={`flex w-full px-3 py-2 rounded-lg text-xs transition-colors ${
                          minPrice === r.min && maxPrice === r.max
                            ? "bg-primary/15 text-primary"
                            : "text-text-muted hover:bg-surface-2 hover:text-text"
                        }`}
                      >
                        {r.label}
                      </button>
                    ))}
                    {(minPrice || maxPrice) && (
                      <button
                        onClick={() => { onSetMinPrice(""); onSetMaxPrice(""); onSetSort("default"); setOpenDrop(null); }}
                        className="flex w-full px-3 py-2 rounded-lg text-xs text-danger hover:bg-danger/10"
                      >
                        Clear Price
                      </button>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* ── Rating dropdown ────────────────────── */}
          <div className="relative border-r border-border/50">
            <button
              onClick={() => setOpenDrop(openDrop === "rating" ? null : "rating")}
              className={`flex items-center gap-1.5 px-3 h-12 text-[11px] font-medium transition-colors ${
                minRating ? "text-warning" : "text-text-muted hover:text-text"
              }`}
            >
              <Star className="w-3 h-3 text-accent shrink-0" />
              <span className="hidden lg:inline whitespace-nowrap">{minRating ? `${minRating}+` : "Rating"}</span>
              <ChevronDown className={`w-3 h-3 transition-transform ${openDrop === "rating" ? "rotate-180" : ""}`} />
            </button>
            <AnimatePresence>
              {openDrop === "rating" && (
                <motion.div
                  variants={dropVariants}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                  transition={dropTransition}
                  className="absolute top-full left-0 mt-1 w-40 rounded-xl glass-dropdown overflow-hidden z-[999]"
                >
                  <div className="p-1">
                    <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-text-faint">
                      Min Rating
                    </div>
                    {["4", "3", "2", "1"].map((r) => (
                      <button
                        key={r}
                        onClick={() => { onSetMinRating(minRating === r ? "" : r); setOpenDrop(null); onResetVisibleCount?.(); }}
                        className={`flex w-full items-center gap-2 px-3 py-2 text-xs transition-colors ${
                          minRating === r
                            ? "bg-warning/15 text-warning"
                            : "text-text-muted hover:bg-surface-2 hover:text-text"
                        }`}
                      >
                        <span className="text-warning">{"★".repeat(Number(r))}{"☆".repeat(5 - Number(r))}</span>
                        <span>{r}+ Stars</span>
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* ── Supplier dropdown ──────────────────── */}
          <div className="relative border-r border-border/50 hidden sm:block">
            <button
              onClick={() => setOpenDrop(openDrop === "supplier" ? null : "supplier")}
              className={`flex items-center gap-1.5 px-3 h-12 text-[11px] font-medium transition-colors ${
                supplier ? "text-primary" : "text-text-muted hover:text-text"
              }`}
            >
              <Store className="w-3 h-3 text-primary/70 shrink-0" />
              <span className="hidden lg:inline whitespace-nowrap max-w-20 truncate">
                {supplier || "Supplier"}
              </span>
              <ChevronDown className={`w-3 h-3 transition-transform ${openDrop === "supplier" ? "rotate-180" : ""}`} />
            </button>
            <AnimatePresence>
              {openDrop === "supplier" && (
                <motion.div
                  variants={dropVariants}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                  transition={dropTransition}
                  className="absolute top-full left-0 mt-1 w-56 rounded-xl glass-dropdown overflow-hidden z-[999]"
                >
                  <div className="p-2">
                    <input
                      ref={supplierInputRef}
                      type="text"
                      value={supplierSearchText}
                      onChange={(e) => setSupplierSearchText(e.target.value)}
                      placeholder="Search suppliers..."
                      className="w-full h-8 px-3 rounded-lg border border-border bg-surface-2 text-xs text-text placeholder:text-text-faint focus:outline-none focus:ring-1 focus:ring-primary/40 mb-2"
                    />
                    <div className="max-h-48 overflow-y-auto">
                      {filteredSuppliers.length > 0 ? (
                        filteredSuppliers.map((s) => (
                          <button
                            key={s.id}
                            onClick={() => {
                              onSetSupplier(s.business_name || s.username);
                              setSupplierSearchText("");
                              setOpenDrop(null);
                              onResetVisibleCount?.();
                            }}
                            className={`flex w-full items-center gap-2 px-3 py-2 text-xs transition-colors ${
                              supplier === (s.business_name || s.username)
                                ? "bg-primary/15 text-primary"
                                : "text-text-muted hover:bg-surface-2 hover:text-text"
                            }`}
                          >
                            <Store className="w-3 h-3 shrink-0" />
                            <span className="truncate">{s.business_name || s.username}</span>
                          </button>
                        ))
                      ) : (
                        <p className="px-3 py-2 text-xs text-text-faint">No suppliers found</p>
                      )}
                    </div>
                    {supplier && (
                      <button
                        onClick={() => { onSetSupplier(""); setOpenDrop(null); onResetVisibleCount?.(); }}
                        className="flex w-full px-3 py-2 rounded-lg text-xs text-danger hover:bg-danger/10 mt-1"
                      >
                        Clear Supplier
                      </button>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* ── AI-powered Search input ────────────── */}
          <div className="relative flex-1 flex items-center min-w-0">
            <Sparkles className="pointer-events-none absolute left-3 h-4 w-4 text-primary" />
            <input
              ref={inputRef}
              type="text"
              value={search}
              onChange={(e) => onSetSearch(e.target.value)}
              onFocus={() => setShowSuggestions(localSuggestions.length > 0 || suggestions.length > 0 || historyItems.length > 0)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              onKeyDown={handleKeyDown}
              placeholder="Search products, brands, suppliers..."
              className="w-full h-12 bg-transparent pl-9 pr-8 text-[13px] text-text placeholder:text-text-faint focus:outline-none"
            />
            {search && (
              <button
                onClick={() => { onSetSearch(""); setLocalSuggestions([]); }}
                className="absolute right-2 p-1 text-text-faint hover:text-text rounded"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}

            {/* ── AI Suggestions + Search History dropdown ── */}
            <AnimatePresence>
              {showSuggestions && (localSuggestions.length > 0 || suggestions.length > 0 || historyItems.length > 0) && (
                <motion.ul
                  variants={dropVariants}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                  transition={dropTransition}
                  className="absolute top-full left-0 right-0 mt-1 rounded-xl glass-dropdown overflow-hidden z-[999]"
                >
                  {(localSuggestions.length > 0 || suggestions.length > 0) && (
                    <>
                      <li className="flex items-center gap-2 px-3 py-2 text-[10px] font-semibold uppercase tracking-widest text-primary border-b border-border">
                        <Sparkles className="h-3 w-3" />
                        AI Suggestions
                      </li>
                      {(localSuggestions.length > 0 ? localSuggestions : suggestions).slice(0, 6).map((s, i) => (
                        <li key={'sug-' + s + i}>
                          <button
                            onMouseDown={(e) => { e.preventDefault(); onSetSearch(s); commitSearch(s); }}
                            className="flex w-full items-center gap-2 px-3 py-2 text-xs text-text-muted hover:bg-surface-2 transition-colors"
                          >
                            <Search className="w-3 h-3 shrink-0 text-text-faint" />
                            {s}
                          </button>
                        </li>
                      ))}
                    </>
                  )}

                  {historyItems.length > 0 && (!search.trim() || historyItems.some(h => h.toLowerCase().includes(search.toLowerCase()))) && (
                    <>
                      {(localSuggestions.length > 0 || suggestions.length > 0) && (
                        <li className="border-t border-border" />
                      )}
                      <li className="flex items-center justify-between px-3 py-2 text-[10px] font-semibold uppercase tracking-widest text-text-faint border-b border-border">
                        <span className="flex items-center gap-2">
                          <History className="h-3 w-3" />
                          Recent Searches
                        </span>
                        <button
                          onMouseDown={(e) => { e.preventDefault(); clearHistory(); }}
                          className="text-[10px] text-danger hover:text-danger/80 transition-colors"
                        >
                          Clear all
                        </button>
                      </li>
                      {(search.trim()
                        ? historyItems.filter(h => h.toLowerCase().includes(search.toLowerCase()))
                        : historyItems
                      ).slice(0, 8).map((q) => (
                        <li key={'hist-' + q} className="group relative">
                          <button
                            onMouseDown={(e) => { e.preventDefault(); onSetSearch(q); commitSearch(q); }}
                            className="flex w-full items-center gap-2 px-3 py-2 text-xs text-text-muted hover:bg-surface-2 transition-colors pr-10"
                          >
                            <History className="w-3 h-3 shrink-0 text-text-faint" />
                            <span className="truncate">{q}</span>
                          </button>
                          <button
                            onMouseDown={(e) => { e.stopPropagation(); e.preventDefault(); removeFromHistory(q); }}
                            title="Remove from history"
                            className="absolute right-1 top-1/2 -translate-y-1/2 p-1.5 rounded text-text-faint opacity-0 group-hover:opacity-100 hover:text-danger hover:bg-danger/10 transition-all"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </li>
                      ))}
                    </>
                  )}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>

          {/* ── Camera ─────────────────────────────── */}
          <button
            onClick={onImageSearch}
            title="Search by image"
            className="flex items-center justify-center w-10 h-12 text-text-faint hover:text-primary transition-colors border-l border-border/50"
          >
            <Camera className="w-4 h-4" />
          </button>

          {/* ── Mic ────────────────────────────────── */}
          <button
            onClick={startVoiceSearch}
            title={isListening ? "Listening..." : "Voice search"}
            disabled={!speechSupported}
            className={`flex items-center justify-center w-10 h-12 transition-colors border-l border-border/50 ${
              isListening
                ? "text-primary animate-pulse bg-primary/10"
                : "text-text-faint hover:text-primary"
            } disabled:opacity-30`}
          >
            <Mic className="w-4 h-4" />
          </button>

          {/* ── Search button ──────────────────────── */}
          <button
            onClick={() => commitSearch()}
            className="theme-btn-primary flex items-center justify-center gap-2 w-28 h-12 rounded-r-[1.2rem] text-sm font-semibold transition-colors shrink-0"
          >
            <Search className="w-4 h-4" />
            <span className="hidden sm:inline">Search</span>
          </button>
        </div>
      </div>
    </div>
  );
}
