"use client";

import Image from "next/image";
import { startTransition, Suspense, useCallback, useEffect, useMemo, useRef, useState, memo, Component } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, Loader2, Tag, Percent, Store,
  Sparkles, TrendingUp, Star, ShoppingBag, X, ChevronDown, Flame, Award,
  Package2, Filter, ArrowUp, CheckCircle, History, Zap,
} from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { Product, SupplierPublicSummary } from "@/lib/types";
import { useToastStore } from "@/lib/toastStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { useCurrencyStore } from "@/lib/currencyStore";
import type { ReactNode } from "react";
import type { TranslationKey } from "@/lib/i18n";
import { resolveImage, supplierStorefrontPath } from "@/lib/utils";
import ProductCard from "@/components/ProductCard";
import AdvancedFilter from "@/components/AdvancedFilter";
import { ProductCardSkeleton } from "@/components/LoadingSkeleton";
import BrandLoading from "@/components/BrandLoading";
import { buildProductQueryParams } from "@shared/productQuery";
import { getPartnerBadgeStyle } from "@shared/statusColors";
import { CATEGORIES } from "@/components/FilterSearchBar";
import BannerCarousel from "@/components/BannerCarousel";

type ProductsUiFlag = "showBackToTop";

type ProductsUiState = {
  showBackToTop: boolean;
};

function renderStars(value: string, max = 5) {
  const parsed = Number.parseInt(value, 10);
  const filled = Number.isFinite(parsed) ? Math.max(0, Math.min(max, parsed)) : 0;
  const empty = Math.max(0, max - filled);
  return `${"★".repeat(filled)}${"☆".repeat(empty)}`;
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<BrandLoading fullscreen label="Loading products..." />}>
      <ProductsErrorBoundary>
        <ProductsContent />
      </ProductsErrorBoundary>
    </Suspense>
  );
}

class ProductsErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <p className="text-lg font-bold text-danger">Something went wrong loading products.</p>
          <p className="mt-2 text-sm text-text-muted">Please refresh the page to try again.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

function ProductsContent() {
  const params = useSearchParams();
  const router = useRouter();
  const tr = useLocaleStore((s) => s.t);
  const addToast = useToastStore((s) => s.addToast);
  const currency = useCurrencyStore((s) => s.currency);
  const formatCurrent = useCurrencyStore((s) => s.format);
  const locale = useLocaleStore((s) => s.locale);

  // Visual search / image upload
  const [isVisualSearch, setIsVisualSearch] = useState(false);

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [search, setSearch] = useState(params?.get("q") || params?.get("search") || "");
  const [debouncedSearch, setDebouncedSearch] = useState(params?.get("q") || params?.get("search") || "");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [supplierSuggestions, setSupplierSuggestions] = useState<SupplierPublicSummary[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [trendingSearches, setTrendingSearches] = useState<string[]>([]);
  const [showTrending, setShowTrending] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [category, setCategory] = useState(params?.get("category") || "all");
  const [sort, setSort] = useState(params?.get("sort") || "default");
  const [view, setView] = useState<"grid" | "list">(
    params?.get("view") === "list" ? "list" : "grid"
  );
  const [visibleCount, setVisibleCount] = useState(24);
  const [trendingOnly, setTrendingOnly] = useState(params?.get("trending") === "1");
  const [newArrivals, setNewArrivals] = useState(params?.get("newArrivals") === "1");
  const [bestSellers, setBestSellers] = useState(params?.get("bestSellers") === "1");
  const [discountPct, setDiscountPct] = useState(params?.get("discountPct") || "");
  const [minPrice, setMinPrice] = useState(params?.get("minPrice") || "");
  const [maxPrice, setMaxPrice] = useState(params?.get("maxPrice") || "");
  const [brand, setBrand] = useState(params?.get("brand") || "");
  const [color, setColor] = useState(params?.get("color") || "");
  const [minRating, setMinRating] = useState(params?.get("minRating") || "");
  const [inStock, setInStock] = useState(params?.get("inStock") === "true");
  const [selectedTag, setSelectedTag] = useState(params?.get("tag") || "");
  const [supplier, setSupplier] = useState(params?.get("supplier") || "");
  const [brands, setBrands] = useState<string[]>(params?.get("brands") ? params.get("brands")!.split(",").filter(Boolean) : []);
  const [supplierSearch, setSupplierSearch] = useState("");
  const [selectedSuppliers, setSelectedSuppliers] = useState<string[]>([]);
  const [deals, setDeals] = useState(params?.get("deals") === "1");
  const [hasVideo, setHasVideo] = useState(params?.get("hasVideo") === "1");
  const [hasDiscount, setHasDiscount] = useState(params?.get("hasDiscount") === "1");
  const [attributes, setAttributes] = useState<Record<string, string[]>>(() => {
    try {
      return params?.get("attributes") ? JSON.parse(params.get("attributes")!) : {};
    } catch {
      return {};
    }
  });
  const [saleId, setSaleId] = useState(params?.get("sale_id") || "");
  const [supplierNames, setSupplierNames] = useState<string[]>([]);
  const [supplierResults, setSupplierResults] = useState<SupplierPublicSummary[]>([]);
  const [supplierResultTotal, setSupplierResultTotal] = useState(0);
  const [loadingSupplierResults, setLoadingSupplierResults] = useState(false);
  const [redirectingSupplierStorefront, setRedirectingSupplierStorefront] = useState(false);
  const visualSearchInputRef = useRef<HTMLInputElement>(null);

  const [showBackToTop, setShowBackToTop] = useState(false);

  const setUiFlag = useCallback(
    (key: ProductsUiFlag, nextValue: boolean | ((current: boolean) => boolean)) => {
      if (key === "showBackToTop") {
        setShowBackToTop((prev) => typeof nextValue === "function" ? (nextValue as (current: boolean) => boolean)(prev) : nextValue);
      }
    },
    [],
  );

  const effectiveSupplierFilter = useMemo(() => {
    const normalizedSelected = selectedSuppliers.map((value) => value.trim()).filter(Boolean);
    if (normalizedSelected.length > 0) return normalizedSelected.join(",");
    return supplier.trim();
  }, [selectedSuppliers, supplier]);

  const translatedProductNames = useMemo(() => {
    return products.map((p) => p.name);
  }, [products]);

  const showSupplierSection = useMemo(() => {
    return !!effectiveSupplierFilter || selectedSuppliers.length > 0;
  }, [effectiveSupplierFilter, selectedSuppliers]);

  const deferredSupplierResults = supplierResults;

  const fetchProducts = useCallback(async (reset = false) => {
    // If visual search is active, results are already set via setProducts
    if (isVisualSearch) {
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const qs = buildProductQueryParams({
        search: debouncedSearch,
        category,
        sort,
        minPrice,
        maxPrice,
        brand,
        color,
        minRating,
        inStock,
        selectedTag,
        supplier: effectiveSupplierFilter,
        deals,
        hasVideo,
        hasDiscount,
        attributes,
        limit: visibleCount,
        offset: reset ? 0 : products.length,
      });

      const res = await apiFetch(`/products?${qs}`);
      if (!res.ok) {
        const body = await res.text().catch(() => "(no body)");
        console.error(`Products fetch failed: HTTP ${res.status} ${res.statusText}`, body.slice(0, 500));
        throw new Error(`Failed to fetch products (HTTP ${res.status})`);
      }
      const data = await parseJsonResponse(res);
      const items = Array.isArray(data) ? data : (data?.items ?? []);
      const total = Array.isArray(data) ? data.length : (data?.total ?? 0);

      if (reset) {
        setProducts(items);
      } else {
        setProducts((prev) => [...prev, ...items]);
      }
      setTotalCount(total);
      setHasMore(items.length === visibleCount);
    } catch (error) {
      console.error("Error fetching products:", error);
      if (reset) setProducts([]);
      setTotalCount(0);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, category, sort, minPrice, maxPrice, brand, color, minRating, inStock, selectedTag, effectiveSupplierFilter, deals, hasVideo, hasDiscount, attributes, visibleCount, products.length]);

  useEffect(() => {
    fetchProducts(true);
  }, [fetchProducts]);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    const trimmed = search.trim();
    if (trimmed.length >= 2) {
      timer = setTimeout(() => {
        Promise.all([
          // Use the advanced search/autocomplete endpoint for fuzzy suggestions
          apiFetch(`/search/autocomplete?q=${encodeURIComponent(trimmed)}&limit=8`)
            .then((r) => (r.ok ? r.json() : { suggestions: [] }))
            .then((d: { suggestions: string[] }) => d.suggestions ?? [])
            .catch(() => [] as string[]),
          apiFetch(`/suppliers?limit=4&q=${encodeURIComponent(trimmed)}`)
            .then((r) => (r.ok ? r.json() : { items: [] }))
            .catch(() => ({ items: [] })),
        ])
          .then(([productData, supplierData]: [string[], { items?: SupplierPublicSummary[] }]) => {
            const nextProductSuggestions = Array.isArray(productData) ? productData : [];
            const nextSupplierSuggestions = Array.isArray(supplierData?.items) ? supplierData.items : [];
            setSuggestions(nextProductSuggestions);
            setSupplierSuggestions(nextSupplierSuggestions);
            setShowSuggestions(nextProductSuggestions.length > 0 || nextSupplierSuggestions.length > 0);
          })
          .catch(() => {
            setSuggestions([]);
            setSupplierSuggestions([]);
            setShowSuggestions(false);
          });
      }, 140);
    } else {
      setSuggestions([]);
      setSupplierSuggestions([]);
      setShowSuggestions(false);
    }
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 160);
    return () => clearTimeout(timer);
  }, [search]);

  const resolveSupplierStorefrontTarget = useCallback(async (query: string) => {
    try {
      const res = await apiFetch(`/suppliers/resolve/${encodeURIComponent(query)}`);
      if (!res.ok) return null;
      const data = await res.json();
      const target = typeof data?.canonical_path === "string" && data.canonical_path
        ? data.canonical_path
        : supplierStorefrontPath(data);
      return !target || target === "/products" ? null : target;
    } catch {
      return null;
    }
  }, []);

  const tryOpenSupplierStorefront = useCallback(async (query: string) => {
    const target = await resolveSupplierStorefrontTarget(query);
    if (!target) return false;
    router.push(target);
    return true;
  }, [resolveSupplierStorefrontTarget, router]);

  const commitSearch = useCallback(() => {
    const normalized = search.trim();
    if (normalized !== search) setSearch(normalized);
    setShowSuggestions(false);
    setVisibleCount(24);
    // Clear visual search when user enters a text query
    if (isVisualSearch) setIsVisualSearch(false);

    if (!normalized) {
      setDebouncedSearch("");
      return;
    }

    void (async () => {
      const redirected = await tryOpenSupplierStorefront(normalized);
      if (!redirected) setDebouncedSearch(normalized);
    })();
  }, [search, tryOpenSupplierStorefront, isVisualSearch]);

  const uniqueTags = useMemo(() => {
    const s = new Set<string>();
    products.forEach((p) => {
      if (p.tags) p.tags.split(",").map((t) => t.trim()).filter(Boolean).forEach((t) => s.add(t));
    });
    return Array.from(s).slice(0, 20);
  }, [products]);

  const resetFilters = useCallback(() => {
    setSearch(""); setCategory("all"); setSort("default"); setView("grid");
    setTrendingOnly(false); setNewArrivals(false); setBestSellers(false);
    setDiscountPct(""); setMinPrice(""); setMaxPrice(""); setBrand("");
    setBrands([]); setColor(""); setMinRating(""); setInStock(false);
    setSelectedTag(""); setSupplier(""); setSelectedSuppliers([]); setSupplierSearch("");
    setDeals(false); setHasVideo(false); setHasDiscount(false); setAttributes({});
    setVisibleCount(24);
  }, []);

  const activeFilterCount = [
    category !== "all", trendingOnly, newArrivals, bestSellers, deals,
    !!discountPct, !!minPrice, !!maxPrice, !!brand, brands.length > 0, !!color, !!minRating,
    inStock, !!selectedTag, selectedSuppliers.length > 0 || !!supplier,
    hasVideo, hasDiscount, Object.values(attributes).some(arr => arr.length),
  ].filter(Boolean).length;

  // Handle visual search results from header (passed via sessionStorage)
  useEffect(() => {
    const visualData = params?.get("visualSearch");
    if (visualData === "1") {
      try {
        const stored = sessionStorage.getItem("zozi_visual_search");
        if (stored) {
          const parsed = JSON.parse(stored);
          // Only use results if stored within last 30 seconds
          if (parsed.timestamp && Date.now() - parsed.timestamp < 30000) {
            if (parsed.products?.length > 0) {
              setIsVisualSearch(true);
              setProducts(parsed.products);
              setTotalCount(parsed.products.length);
            }
          }
          // Clean up regardless
          sessionStorage.removeItem("zozi_visual_search");
        }
      } catch { /* ignore parse errors */ }
    }
  }, [params]);

  useEffect(() => {
    setSearch(params?.get("q") || params?.get("search") || "");
    setCategory(params?.get("category") || "all");
    setSort(params?.get("sort") || "default");
    setView(params?.get("view") === "list" ? "list" : "grid");
    setTrendingOnly(params?.get("trending") === "1");
    setNewArrivals(params?.get("newArrivals") === "1");
    setBestSellers(params?.get("bestSellers") === "1");
    setDiscountPct(params?.get("discountPct") || "");
    setMinPrice(params?.get("minPrice") || "");
    setMaxPrice(params?.get("maxPrice") || "");
    setBrand(params?.get("brand") || "");
    setBrands(params?.get("brands") ? params.get("brands")!.split(",").filter(Boolean) : []);
    setColor(params?.get("color") || "");
    setMinRating(params?.get("minRating") || "");
    setInStock(params?.get("inStock") === "true");
    setSelectedTag(params?.get("tag") || "");
    setSupplier(params?.get("supplier") || "");
    setSelectedSuppliers(params?.get("supplier") ? params.get("supplier")!.split(",").filter(Boolean) : []);
    setDeals(params?.get("deals") === "1");
    setHasVideo(params?.get("hasVideo") === "1");
    setHasDiscount(params?.get("hasDiscount") === "1");
    setAttributes(() => {
      try {
        return params?.get("attributes") ? JSON.parse(params.get("attributes")!) : {};
      } catch {
        return {};
      }
    });
    setSaleId(params?.get("sale_id") || "");
  }, [params]);

  useEffect(() => {
    apiFetch("/products/suppliers")
      .then((r) => (r.ok ? r.json() : []))
      .then((d: string[]) => setSupplierNames(d))
      .catch(() => {});
    
    // Fetch trending searches for the autocomplete placeholder
    apiFetch("/search/trending?limit=6")
      .then((r) => (r.ok ? r.json() : { queries: [] }))
      .then((d: { queries: string[] }) => setTrendingSearches(d.queries ?? []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const selectedNames = selectedSuppliers.map((value) => value.trim()).filter(Boolean);
    const query = supplier.trim() || debouncedSearch.trim();
    if (selectedNames.length === 0 && !query) {
      setSupplierResults([]);
      setSupplierResultTotal(0);
      setLoadingSupplierResults(false);
      return;
    }

    const qs = new URLSearchParams({ limit: "6", offset: "0" });
    if (selectedNames.length > 0) qs.set("names", selectedNames.join(","));
    else qs.set("q", query);

    let cancelled = false;
    setLoadingSupplierResults(true);

    apiFetch(`/suppliers?${qs.toString()}`)
      .then((r) => (r.ok ? r.json() : { items: [], total: 0 }))
      .then((data: { items?: SupplierPublicSummary[]; total?: number }) => {
        if (cancelled) return;
        setSupplierResults(data.items ?? []);
        setSupplierResultTotal(data.total ?? data.items?.length ?? 0);
      })
      .catch(() => {
        if (cancelled) return;
        setSupplierResults([]);
        setSupplierResultTotal(0);
      })
      .finally(() => {
        if (!cancelled) setLoadingSupplierResults(false);
      });

    return () => {
      cancelled = true;
    };
  }, [debouncedSearch, selectedSuppliers, supplier]);

  useEffect(() => {
    if (redirectingSupplierStorefront) return;
    const qs = new URLSearchParams();
    if (debouncedSearch)    qs.set("q",      debouncedSearch);
    if (category !== "all") qs.set("category",    category);
    if (brand)              qs.set("brand",        brand);
    if (color)              qs.set("color",        color);
    if (effectiveSupplierFilter) qs.set("supplier", effectiveSupplierFilter);
    if (sort !== "default") qs.set("sort",         sort);
    if (view === "list")    qs.set("view",         "list");
    if (trendingOnly)       qs.set("trending",     "1");
    if (newArrivals)        qs.set("newArrivals",  "1");
    if (bestSellers)        qs.set("bestSellers",  "1");
    if (discountPct)        qs.set("discountPct",  discountPct);
    if (deals)              qs.set("deals",        "1");
    if (saleId)             qs.set("sale_id",      saleId);
    if (minPrice)           qs.set("minPrice",     minPrice);
    if (maxPrice)           qs.set("maxPrice",     maxPrice);
    if (minRating)          qs.set("minRating",    minRating);
    if (inStock)            qs.set("inStock",      "true");
    if (selectedTag)        qs.set("tag",          selectedTag);
    router.replace(`/products${qs.toString() ? `?${qs.toString()}` : ""}`, { scroll: false });
  }, [debouncedSearch, category, brand, color, effectiveSupplierFilter, sort, view, trendingOnly, newArrivals,
    bestSellers, discountPct, deals, saleId, minPrice, maxPrice, minRating, inStock, selectedTag, router, redirectingSupplierStorefront]);

  // Visual search — handle image upload from FilterSearchBar camera button
  const handleImageFile = useCallback(async (file: File) => {
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append("image", file);
      const res = await apiFetch("/search/visual", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        addToast("Visual search complete", "success");
        if (data.similarProductIds?.length > 0) {
          setIsVisualSearch(true);
          setProducts(data.similarProducts || []);
          setTotalCount(data.similarProducts?.length || 0);
        }
      } else {
        addToast("Visual search failed. Try a different image.", "error");
      }
    } catch {
      addToast("Network error during visual search.", "error");
    }
  }, [addToast]);

  const presetRanges = useMemo(() => {
    const presets = [
      { key: "under", min: "", max: "25" },
      { key: "mid", min: "25", max: "100" },
      { key: "high", min: "100", max: "" },
    ];
    return presets.map((preset) => ({
      ...preset,
      label:
        preset.min && preset.max
          ? `${formatCurrent(Number(preset.min))} - ${formatCurrent(Number(preset.max))}`
          : preset.max
          ? `Under ${formatCurrent(Number(preset.max))}`
          : `${formatCurrent(Number(preset.min))}+`,
    }));
  }, [formatCurrent]);

  const handleOpenSupplier = useCallback((supplierResult: SupplierPublicSummary) => {
    router.push(supplierStorefrontPath(supplierResult));
  }, [router]);

  const handleLoadMore = useCallback(() => {
    setVisibleCount((v) => v + 24);
  }, []);

  if (redirectingSupplierStorefront) {
    return <BrandLoading fullscreen label="Opening supplier storefront..." />;
  }


  function PriceRangeSlider({
    min, max, valueMin, valueMax, onChange, format,
  }: {
    min: number;
    max: number;
    valueMin: number;
    valueMax: number;
    onChange: (lo: number, hi: number) => void;
    format: (n: number) => string;
  }) {
    const step = Math.max(1, Math.round((max - min) / 100));
    const lo = Math.min(Math.max(valueMin, min), max);
    const hi = Math.max(Math.min(valueMax, max), min);
    const pctMin = ((lo - min) / (max - min)) * 100;
    const pctMax = ((hi - min) / (max - min)) * 100;
    const handleLo = (raw: number) => {
      const next = Math.min(raw, hi - step);
      onChange(next, hi);
    };
    const handleHi = (raw: number) => {
      const next = Math.max(raw, lo + step);
      onChange(lo, next);
    };
    return (
      <div className="space-y-2">
        <div className="theme-range-dual" role="group" aria-label="Price range">
          <div className="theme-range-track">
            <div className="theme-range-track-fill" style={{ left: `${pctMin}%`, right: `${100 - pctMax}%` }} />
          </div>
          <input
            type="range"
            className="theme-range"
            min={min}
            max={max}
            step={step}
            value={lo}
            aria-label="Minimum price"
            onChange={(e) => handleLo(Number(e.target.value))}
          />
          <input
            type="range"
            className="theme-range"
            min={min}
            max={max}
            step={step}
            value={hi}
            aria-label="Maximum price"
            onChange={(e) => handleHi(Number(e.target.value))}
          />
        </div>
        <div className="flex justify-between text-[10px] text-text-faint">
          <span>{format(lo)}</span>
          <span>{format(hi)}</span>
        </div>
      </div>
    );
  }



  return (
    <main className="min-h-screen bg-theme-bg">
      {/* Main Content Container */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Promotional banner — after header, before the search engine bar */}
        <BannerCarousel position="promotional" className="mb-6" />

        {/* ═══════════════════════════════════════════════════════
            QUICK FILTER PILLS — search bar is in the header
        ═══════════════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mb-4 flex flex-wrap items-center justify-center gap-2.5"
        >
          {/* New Arrivals */}
          <button
            type="button"
            onClick={() => { setNewArrivals((p) => !p); setVisibleCount(24); }}
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
            onClick={() => { setTrendingOnly((p) => !p); setVisibleCount(24); }}
            className={`flex h-8 items-center gap-1.5 rounded-full border px-3.5 text-[11px] font-semibold transition-all duration-200 ${
              trendingOnly
                ? "border-danger/40 bg-danger/20 text-danger shadow-lg shadow-danger/10"
                : "banner-glass-chip text-text-faint hover:border-border-light hover:text-text"
            }`}
          >
            <TrendingUp className={`h-3 w-3 ${trendingOnly ? "" : "text-danger/60"}`} />
            {tr("trending")}
          </button>

          {/* Deals */}
          <button
            type="button"
            onClick={() => { setDeals((p) => !p); setVisibleCount(24); }}
            className={`flex h-8 items-center gap-1.5 rounded-full border px-3.5 text-[11px] font-semibold transition-all duration-200 ${
              deals
                ? "border-success/40 bg-success/20 text-success shadow-lg shadow-success/10"
                : "banner-glass-chip text-text-faint hover:border-border-light hover:text-text"
            }`}
          >
            <Percent className={`h-3 w-3 ${deals ? "" : "text-accent/70"}`} />
            {tr("deals")}
          </button>

          {/* Discount % */}
          {(["10", "20", "30", "50"] as const).map((val) => (
            <button
              key={val}
              type="button"
              onClick={() => { setDiscountPct(discountPct === val ? "" : val); setVisibleCount(24); }}
              className={`flex h-8 items-center gap-1 rounded-full border px-2.5 text-[11px] font-semibold transition-all duration-200 ${
                discountPct === val
                  ? "border-success/40 bg-success/20 text-success shadow-lg shadow-success/10"
                  : "banner-glass-chip text-text-faint hover:border-border-light hover:text-text"
              }`}
            >
              <Tag className={`h-2.5 w-2.5 ${discountPct === val ? "" : "text-accent/70"}`} />
              {val}%+
            </button>
          ))}

          {/* Clear filters */}
          {activeFilterCount > 0 && (
            <button
              type="button"
              onClick={resetFilters}
              className="flex h-8 items-center gap-1.5 rounded-full border border-danger/30 bg-danger/10 px-3.5 text-[11px] font-semibold text-danger hover:bg-danger/20 transition-all duration-200"
            >
              <X className="h-2.5 w-2.5" />
              Clear filters
            </button>
          )}
        </motion.div>

        {/* Hidden file input for visual search (triggered from header camera button) */}
        <input
          ref={visualSearchInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleImageFile(file);
            e.target.value = "";
          }}
        />

        {/* Result count */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs text-text-faint">
            {loading ? tr("searchingNow") : (
              <>
                <span className="text-text font-semibold">{totalCount.toLocaleString()}</span>
                {" "}{tr("results")}
                {search && (
                  <span> {tr("resultsFor")} &ldquo;<strong className="text-primary">{search}</strong>&rdquo;</span>
                )}
              </>
            )}
          </p>
          {activeFilterCount > 0 && (
            <span className="text-[10px] text-text-faint">{activeFilterCount} {activeFilterCount === 1 ? tr("filterApplied") : tr("filtersApplied")}</span>
          )}
        </div>

        {/* Product Results */}
        <div className="theme-card rounded-[1.75rem] p-4 sm:p-6">
          {/* Active filter chips */}
          {activeFilterCount > 0 && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
              className="flex flex-wrap gap-1.5 mb-4"
            >
              {search && <FilterChip label={`"${search}"`} onRemove={() => setSearch("")} color="indigo" />}
              {category !== "all" && <FilterChip label={tr(CATEGORIES.find((c) => c.value === category)?.labelKey ?? "allProducts")} onRemove={() => setCategory("all")} color="indigo" />}
              {newArrivals && <FilterChip label={tr("newArrivals")} onRemove={() => setNewArrivals(false)} color="sky" icon={<Sparkles className="w-2.5 h-2.5" />} />}
              {deals && !discountPct && <FilterChip label={tr("deals")} onRemove={() => setDeals(false)} color="green" icon={<Percent className="w-2.5 h-2.5" />} />}
              {discountPct && <FilterChip label={`${discountPct}%+ Off`} onRemove={() => setDiscountPct("")} color="green" icon={<Percent className="w-2.5 h-2.5" />} />}
              {selectedSuppliers.map((s) => (
                <FilterChip key={s} label={s} onRemove={() => {
                  setSelectedSuppliers((prev) => prev.filter((x) => x !== s));
                  if (selectedSuppliers.length === 1 && supplier === s) setSupplier("");
                }} color="purple" icon={<Store className="w-2.5 h-2.5" />} />
              ))}
              {!selectedSuppliers.length && supplier && <FilterChip label={supplier} onRemove={() => setSupplier("")} color="purple" icon={<Store className="w-2.5 h-2.5" />} />}
              {minPrice && <FilterChip label={`${tr("fromPrice")} ${formatCurrent(Number(minPrice))}`} onRemove={() => setMinPrice("")} />}
              {maxPrice && <FilterChip label={`${tr("upToPrice")} ${formatCurrent(Number(maxPrice))}`} onRemove={() => setMaxPrice("")} />}
              {minRating && <FilterChip label={`${minRating}+ ${tr("rating")}`} onRemove={() => setMinRating("")} color="amber" />}
              {brand && <FilterChip label={brand} onRemove={() => setBrand("")} />}
              {color && <FilterChip label={color} onRemove={() => setColor("")} />}
              {selectedTag && <FilterChip label={`#${selectedTag}`} onRemove={() => setSelectedTag("")} color="purple" />}
            </motion.div>
          )}

          <SupplierResultsSection
            showSupplierSection={showSupplierSection}
            loadingSupplierResults={loadingSupplierResults}
            supplierResultTotal={supplierResultTotal}
            supplierResults={deferredSupplierResults}
            onOpenSupplier={handleOpenSupplier}
          />

          <ProductResultsGrid
            loading={loading}
            products={products}
            translatedProductNames={translatedProductNames}
            hasMore={hasMore}
            onLoadMore={handleLoadMore}
            resetFilters={resetFilters}
            tr={tr}
          />
        </div>
      </div>



      <AnimatePresence>
        {showBackToTop && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            className="fixed bottom-6 right-6 p-3 bg-primary hover:bg-primary-dark text-on-brand rounded-full shadow-lg shadow-primary/30 transition-colors z-40"
          >
            <ArrowUp className="w-5 h-5" />
          </motion.button>
        )}
      </AnimatePresence>
    </main>
  );
}

const SupplierResultsSection = memo(function SupplierResultsSection({
  showSupplierSection,
  loadingSupplierResults,
  supplierResultTotal,
  supplierResults,
  onOpenSupplier,
}: {
  showSupplierSection: boolean;
  loadingSupplierResults: boolean;
  supplierResultTotal: number;
  supplierResults: SupplierPublicSummary[];
  onOpenSupplier: (supplier: SupplierPublicSummary) => void;
}) {
  if (!showSupplierSection) {
    return null;
  }

  return (
    <section className="mb-6 rounded-[1.75rem] border border-border bg-surface/95 p-4 shadow-sm shadow-black/5">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-text-faint">Supplier storefronts</p>
          <h2 className="mt-1 text-lg font-semibold text-text">
            {loadingSupplierResults
              ? "Searching supplier pages..."
              : supplierResultTotal > 0
              ? `${supplierResultTotal.toLocaleString()} supplier storefront${supplierResultTotal === 1 ? "" : "s"} matched`
              : "No supplier storefronts matched this supplier filter yet"}
          </h2>
        </div>
        {supplierResultTotal > 0 && (
          <span className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[11px] font-semibold text-primary">
            <Store className="h-3 w-3" />
            Supplier pages
          </span>
        )}
      </div>

      {loadingSupplierResults ? (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="h-44 animate-pulse rounded-[1.4rem] border border-border bg-surface-2/70" />
          ))}
        </div>
      ) : supplierResults.length > 0 ? (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {supplierResults.map((supplierResult) => (
            <SupplierStoreCard
              key={supplierResult.id}
              supplier={supplierResult}
              onOpen={() => onOpenSupplier(supplierResult)}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-border bg-surface-2/40 px-4 py-5 text-sm text-text-muted">
          Supplier pages are now part of search on this screen. Try a supplier name or pick a supplier filter to open the storefront directly.
        </div>
      )}
    </section>
  );
});

const ProductResultsGrid = memo(function ProductResultsGrid({
  loading,
  products,
  translatedProductNames,
  hasMore,
  onLoadMore,
  resetFilters,
  tr,
}: {
  loading: boolean;
  products: Product[];
  translatedProductNames: string[];
  hasMore: boolean;
  onLoadMore: () => void;
  resetFilters: () => void;
  tr: (key: TranslationKey) => string;
}) {
  const initialLoading = loading && products.length === 0;
  const loadingMore = loading && products.length > 0;
  const loadMoreSentinelRef = useRef<HTMLDivElement | null>(null);
  const lastAutoLoadCountRef = useRef<number>(-1);

  useEffect(() => {
    if (!hasMore || loadingMore) {
      return;
    }

    if (typeof IntersectionObserver === "undefined") {
      return;
    }

    const node = loadMoreSentinelRef.current;
    if (!node) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const first = entries[0];
        if (!first?.isIntersecting) {
          return;
        }
        if (lastAutoLoadCountRef.current === products.length) {
          return;
        }
        lastAutoLoadCountRef.current = products.length;
        onLoadMore();
      },
      {
        root: null,
        rootMargin: "320px 0px",
        threshold: 0.01,
      }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [hasMore, loadingMore, onLoadMore, products.length]);

  if (initialLoading) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
        {Array.from({ length: 12 }).map((_, index) => <ProductCardSkeleton key={index} />)}
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center py-20 text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-2/60">
          <Search className="h-7 w-7 text-text-faint" />
        </div>
        <h3 className="mb-2 text-lg font-bold text-text">{tr("noProductsFound")}</h3>
        <p className="mb-5 max-w-sm text-sm text-text-muted">{tr("tryAdjustingFilters")}</p>
        <button onClick={resetFilters} className="rounded-xl theme-btn-primary px-5 py-2.5 text-sm font-semibold">
          {tr("clearAllFilters")}
        </button>
      </motion.div>
    );
  }

  return (
    <>
      <motion.div className="grid grid-cols-2 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
        {products.map((product, index) => (
          <div
            key={product.id}
            className="animate-fadeInUp"
            style={{ animationDelay: `${Math.min(index * 0.014, 0.14)}s`, animationFillMode: "backwards" }}
          >
            <ProductCard product={product} translatedName={translatedProductNames[index]} />
          </div>
        ))}
      </motion.div>
      {hasMore && (
        <div className="mt-10 flex justify-center">
          <div
            ref={loadMoreSentinelRef}
            aria-hidden="true"
            className="h-1 w-full"
          />
          <div className="rounded-2xl border border-border px-6 py-2.5 text-sm font-semibold text-text-muted">
            <span className="inline-flex items-center gap-2">
              {loadingMore ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {loadingMore ? "Loading more..." : "Scroll down to load more"}
            </span>
          </div>
        </div>
      )}
    </>
  );
});

function FilterChip({
  label, onRemove, color = "slate", icon,
}: {
  label: string;
  onRemove: () => void;
  color?: "slate" | "indigo" | "rose" | "amber" | "green" | "sky" | "purple";
  icon?: React.ReactNode;
}) {
  const colors: Record<string, string> = {
    slate:  "bg-surface-2 text-text-muted border-border",
    indigo: "bg-primary/15 text-primary border-primary/30",
    rose:   "bg-danger/15 text-danger border-danger/30",
    amber:  "bg-warning/15 text-warning border-warning/30",
    green:  "bg-success/15 text-success border-success/30",
    sky:    "bg-info/15 text-info border-info/30",
    purple: "bg-primary/15 text-primary border-primary/30",
  };
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={`inline-flex items-center gap-1 text-[11px] font-medium px-2.5 py-1 rounded-full border ${colors[color]}`}
    >
      {icon}{label}
      <button onClick={onRemove} className="ml-0.5 hover:opacity-70 transition-opacity">
        <X className="w-2.5 h-2.5" />
      </button>
    </motion.span>
  );
}

function SupplierStoreCard({
  supplier,
  onOpen,
}: {
  supplier: SupplierPublicSummary;
  onOpen: () => void;
}) {
  const displayName = supplier.business_name?.trim() || supplier.username;
  const initials = displayName
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  const location = [supplier.city, supplier.country].filter(Boolean).join(", ");
  const badgeInfo = getPartnerBadgeStyle(supplier.badge_level);
  const reviewCount = Number(supplier.total_reviews ?? 0);
  const trustScore = Number(supplier.credibility_score ?? 0);
  const avgRating = Number(supplier.avg_rating ?? 0);
  const hasBadge = supplier.badge_level && supplier.badge_level !== "none";
  const isVerified = supplier.is_verified || supplier.verification_status === "approved";

  return (
    <motion.button
      type="button"
      onClick={onOpen}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -3, scale: 1.005 }}
      className="group flex h-full flex-col overflow-hidden rounded-[1.4rem] border border-border bg-background text-left shadow-sm transition-all hover:border-primary/30 hover:shadow-xl hover:shadow-primary/8"
    >
      {/* Colored cover strip (tinted by badge tier) */}
      <div className={`relative h-16 w-full shrink-0 overflow-hidden ${hasBadge ? badgeInfo.toneClass : "bg-surface-2"}`}>
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: "radial-gradient(circle, currentColor 1px, transparent 1px)",
          backgroundSize: "18px 18px",
        }} />
        <div className={`absolute right-3 top-2.5 flex items-center gap-1.5 rounded-full border border-current/25 bg-background/75 px-2.5 py-1 text-[10px] font-bold backdrop-blur-sm ${badgeInfo.toneClass}`}>
          <span className="text-base leading-none">{badgeInfo.emoji}</span>
          <span className="uppercase tracking-wide">{badgeInfo.shortLabel ?? badgeInfo.label}</span>
        </div>
      </div>

      {/* Avatar + verified badge */}
      <div className="-mt-7 flex items-end gap-3 px-4">
        {supplier.logo_url ? (
          <div className="relative h-14 w-14 shrink-0 overflow-hidden rounded-2xl border-2 border-background bg-surface-2 shadow-lg">
            <Image
              src={resolveImage(supplier.logo_url)}
              alt={displayName}
              fill
              sizes="56px"
              className="object-cover"
            />
          </div>
        ) : (
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border-2 border-background bg-primary/15 text-sm font-bold text-primary shadow-lg">
            {initials}
          </div>
        )}
        <div className="mb-1 min-w-0 flex-1">            {isVerified && (
            <span className="inline-flex items-center gap-1 rounded-full bg-success/15 px-2 py-0.5 text-[10px] font-semibold text-success">
              <CheckCircle className="h-3 w-3" />
              Verified
            </span>
          )}
        </div>
      </div>

      {/* Name / username / location */}
      <div className="mt-2 px-4">
        <h3 className="truncate text-sm font-bold text-text">{displayName}</h3>
        <p className="mt-0.5 truncate text-[11px] text-text-faint">
          @{supplier.username}
          {location ? <span className="opacity-60"> · {location}</span> : null}
        </p>
        {supplier.bio && (
          <p className="mt-1.5 line-clamp-2 text-xs leading-5 text-text-muted">{supplier.bio}</p>
        )}
      </div>

      {/* Stats grid */}
      <div className="mx-4 mt-3 grid grid-cols-3 gap-1.5 text-xs">
        <div className="flex flex-col items-center rounded-xl bg-surface-2/60 py-2">
          <span className="text-[10px] font-medium text-text-faint">Products</span>
          <span className="mt-0.5 font-bold text-text">{supplier.product_count.toLocaleString()}</span>
        </div>
        <div className="flex flex-col items-center rounded-xl bg-surface-2/60 py-2">
          <span className="text-[10px] font-medium text-text-faint">Rating</span>
          <span className="mt-0.5 inline-flex items-center gap-0.5 font-bold text-text">
            <Star className="h-3 w-3 fill-warning text-warning" />
            {reviewCount > 0 ? avgRating.toFixed(1) : "New"}
          </span>
        </div>
        <div className="flex flex-col items-center rounded-xl bg-surface-2/60 py-2">
          <span className="text-[10px] font-medium text-text-faint">Sales</span>
          <span className="mt-0.5 font-bold text-text">{Number(supplier.total_sales ?? 0).toLocaleString()}</span>
        </div>
      </div>

      {/* CTA button */}
      <span className="mx-4 mb-4 mt-3 inline-flex items-center justify-center gap-2 rounded-xl bg-primary/10 py-2 text-xs font-semibold text-primary transition-all group-hover:bg-primary group-hover:text-white">
        <Store className="h-3.5 w-3.5" />
        View Store
      </span>
    </motion.button>
  );
}