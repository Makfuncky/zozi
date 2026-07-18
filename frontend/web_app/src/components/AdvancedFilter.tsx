"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ChevronDown, RotateCcw, Star, X, Zap } from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useRouter, useSearchParams } from "next/navigation";

export type AdvancedFilters = {
  minPrice: string;
  maxPrice: string;
  brands: string[];
  minRating: string;
  attributes: Record<string, string[]>;
  hasVideo: boolean;
  hasDiscount: boolean;
  inStock: boolean;
  newArrivals: boolean;
  bestSellers: boolean;
  trending: boolean;
};

const INITIAL_FILTERS: AdvancedFilters = {
  minPrice: "",
  maxPrice: "",
  brands: [],
  minRating: "",
  attributes: {},
  hasVideo: false,
  hasDiscount: false,
  inStock: false,
  newArrivals: false,
  bestSellers: false,
  trending: false,
};

export default function AdvancedFilter() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [filters, setFilters] = useState<AdvancedFilters>(INITIAL_FILTERS);
  const [meta, setMeta] = useState<{
    price_range?: { min: number; max: number; avg: number };
    brands?: Array<{ brand: string; count: number }>;
    ratings?: Array<{ min_rating: number; label: string; count: number }>;
    attributes?: Array<{
      id: number;
      name: string;
      type: string;
      display_order: number;
      options: Array<{ value: string; display: string; count: number }>;
    }>;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const categoryId = useMemo(() => {
    const cat = searchParams?.get("category");
    return cat && cat !== "all" ? cat : undefined;
  }, [searchParams]);

  const searchQuery = useMemo(() => searchParams?.get("search") || undefined, [searchParams]);

  const toQueryString = useCallback(
    (next: AdvancedFilters) => {
      const p = new URLSearchParams(searchParams?.toString() || "");
      if (next.minPrice) p.set("minPrice", next.minPrice);
      else p.delete("minPrice");
      if (next.maxPrice) p.set("maxPrice", next.maxPrice);
      else p.delete("maxPrice");
      if (next.minRating) p.set("minRating", next.minRating);
      else p.delete("minRating");
      if (next.brands.length) p.set("brand", next.brands.join(","));
      else p.delete("brand");
      if (next.hasVideo) p.set("hasVideo", "1");
      else p.delete("hasVideo");
      if (next.hasDiscount) p.set("hasDiscount", "1");
      else p.delete("hasDiscount");
      if (next.inStock) p.set("inStock", "true");
      else p.delete("inStock");
      if (next.newArrivals) p.set("newArrivals", "1");
      else p.delete("newArrivals");
      if (next.bestSellers) p.set("bestSellers", "1");
      else p.delete("bestSellers");
      if (next.trending) p.set("trending", "1");
      else p.delete("trending");
      if (Object.keys(next.attributes).length) {
        p.set("attributes", JSON.stringify(next.attributes));
      } else {
        p.delete("attributes");
      }
      const qs = p.toString();
      return qs ? `?${qs}` : "";
    },
    [searchParams],
  );

  const apply = useCallback(
    (next: AdvancedFilters) => {
      setFilters(next);
      const qs = toQueryString(next);
      router.push(`/products${qs}`);
    },
    [router, toQueryString],
  );

  const loadMeta = useCallback(async () => {
    setLoading(true);
    try {
      const p = new URLSearchParams();
      if (categoryId) p.set("category_id", categoryId);
      if (searchQuery) p.set("q", searchQuery);
      const res = await apiFetch(`/search/filters?${p.toString()}`);
      if (!res.ok) throw new Error("Failed to load filters");
      const data = await parseJsonResponse(res) as { filters: typeof meta };
      setMeta(data.filters || null);
    } catch {
      setMeta(null);
    } finally {
      setLoading(false);
    }
  }, [categoryId, searchQuery]);

  useEffect(() => {
    loadMeta();
  }, [loadMeta]);

  useEffect(() => {
    const q = searchParams || new URLSearchParams();
    const next: AdvancedFilters = {
      minPrice: q.get("minPrice") || "",
      maxPrice: q.get("maxPrice") || "",
      brands: q.get("brand") ? q.get("brand")!.split(",") : [],
      minRating: q.get("minRating") || "",
      attributes: q.get("attributes") ? JSON.parse(q.get("attributes")!) : {},
      hasVideo: q.get("hasVideo") === "1",
      hasDiscount: q.get("hasDiscount") === "1",
      inStock: q.get("inStock") === "true",
      newArrivals: q.get("newArrivals") === "1",
      bestSellers: q.get("bestSellers") === "1",
      trending: q.get("trending") === "1",
    };
    setFilters(next);
  }, [searchParams]);

  const reset = useCallback(() => {
    apply(INITIAL_FILTERS);
  }, [apply]);

  const toggleBrand = useCallback(
    (brand: string) => {
      const next = {
        ...filters,
        brands: filters.brands.includes(brand) ? filters.brands.filter((b) => b !== brand) : [...filters.brands, brand],
      };
      apply(next);
    },
    [apply, filters],
  );

  const toggleAttribute = useCallback(
    (attrKey: string, value: string) => {
      const current = filters.attributes[attrKey] || [];
      const nextValues = current.includes(value) ? current.filter((v) => v !== value) : [...current, value];
      apply({ ...filters, attributes: { ...filters.attributes, [attrKey]: nextValues } });
    },
    [apply, filters],
  );

  const activeCount = useMemo(() => {
    let count = 0;
    if (filters.minPrice || filters.maxPrice) count += 1;
    if (filters.brands.length) count += 1;
    if (filters.minRating) count += 1;
    if (Object.values(filters.attributes).some((arr) => arr.length)) count += 1;
    if (filters.hasVideo) count += 1;
    if (filters.hasDiscount) count += 1;
    if (filters.inStock) count += 1;
    if (filters.newArrivals) count += 1;
    if (filters.bestSellers) count += 1;
    if (filters.trending) count += 1;
    return count;
  }, [filters]);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface-1 px-3 py-2 text-xs font-semibold text-text transition-colors hover:bg-surface-2"
      >
        <Zap className="h-3.5 w-3.5" />
        Advanced filters
        {activeCount > 0 && (
          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[9px] font-bold text-on-brand">
            {activeCount > 9 ? "9+" : activeCount}
          </span>
        )}
        <motion.span animate={{ rotate: open ? 180 : 0 }} className="text-text-faint">
          <ChevronDown className="h-3.5 w-3.5" />
        </motion.span>
      </button>

      {open && (
        <motion.div
          initial={{ opacity: 0, y: 8, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 8, scale: 0.98 }}
          className="glass-dropdown absolute top-full z-[999] mt-2 w-[340px] rounded-2xl p-4"
        >
          <div className="mb-3 flex items-center justify-between">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">
              Filters
              {activeCount > 0 && (
                <span className="ml-2 rounded-full bg-primary/15 px-1.5 py-0.5 text-[10px] font-bold text-primary">
                  {activeCount} active
                </span>
              )}
            </p>
            <div className="flex items-center gap-1">
              {activeCount > 0 && (
                <button
                  type="button"
                  onClick={reset}
                  className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-medium text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
                >
                  <RotateCcw className="h-3 w-3" />
                  Reset
                </button>
              )}
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="rounded-lg p-1 text-text-faint transition-colors hover:bg-surface-2 hover:text-text"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {loading ? (
            <div className="space-y-3">
              <div className="h-4 w-24 animate-pulse rounded bg-surface-2" />
              <div className="h-4 w-full animate-pulse rounded bg-surface-2" />
              <div className="h-4 w-full animate-pulse rounded bg-surface-2" />
            </div>
          ) : (
            <div className="space-y-5">
              <PriceRange
                priceRange={meta?.price_range}
                value={{ min: filters.minPrice, max: filters.maxPrice }}
                onChange={(next) => apply({ ...filters, ...next })}
              />
              <BrandFilter
                brands={meta?.brands}
                selected={filters.brands}
                onToggle={toggleBrand}
              />
              <RatingFilter
                ratings={meta?.ratings}
                selected={filters.minRating}
                onSelect={(minRating) => apply({ ...filters, minRating })}
              />
              <BooleanFilterField
                label="Has video"
                checked={filters.hasVideo}
                onChange={(hasVideo) => apply({ ...filters, hasVideo })}
              />
              <BooleanFilterField
                label="On discount"
                checked={filters.hasDiscount}
                onChange={(hasDiscount) => apply({ ...filters, hasDiscount })}
              />
              <BooleanFilterField
                label="In stock"
                checked={filters.inStock}
                onChange={(inStock) => apply({ ...filters, inStock })}
              />
              <BooleanFilterField
                label="New arrivals"
                checked={filters.newArrivals}
                onChange={(newArrivals) => apply({ ...filters, newArrivals })}
              />
              <BooleanFilterField
                label="Best sellers"
                checked={filters.bestSellers}
                onChange={(bestSellers) => apply({ ...filters, bestSellers })}
              />
              {meta?.attributes?.map((attr) => (
                <AttributeFilter
                  key={attr.id}
                  attr={attr}
                  selected={filters.attributes[attr.name] || []}
                  onToggle={(value) => toggleAttribute(attr.name, value)}
                />
              ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}

interface PriceRangeProps {
  priceRange?: { min: number; max: number; avg: number };
  value: { min: string; max: string };
  onChange: (next: { minPrice: string; maxPrice: string }) => void;
}

function PriceRange({ priceRange, value, onChange }: PriceRangeProps) {
  const min = priceRange?.min ?? 0;
  const max = priceRange?.max ?? 10000;
  const step = Math.max(1, Math.round((max - min) / 100));

  const numMin = Number(value.min) || min;
  const numMax = value.max ? Number(value.max) : max;

  // Clamp the two handles so the lower handle never crosses the upper one.
  const handleMin = (raw: number) => {
    const next = Math.min(raw, numMax - step);
    onChange({ minPrice: String(next), maxPrice: value.max });
  };
  const handleMax = (raw: number) => {
    const next = Math.max(raw, numMin + step);
    onChange({ minPrice: value.min, maxPrice: String(next) });
  };

  const pctMin = ((numMin - min) / (max - min)) * 100;
  const pctMax = ((numMax - min) / (max - min)) * 100;

  return (
    <div className="space-y-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Price</p>

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
          value={numMin}
          aria-label="Minimum price"
          onChange={(e) => handleMin(Number(e.target.value))}
        />
        <input
          type="range"
          className="theme-range"
          min={min}
          max={max}
          step={step}
          value={numMax}
          aria-label="Maximum price"
          onChange={(e) => handleMax(Number(e.target.value))}
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="number"
          value={value.min}
          onChange={(e) => onChange({ minPrice: e.target.value, maxPrice: value.max })}
          className="w-full rounded-xl border border-border bg-surface-1 px-2 py-1.5 text-xs text-text"
          placeholder={`${min}`}
          min={min}
          max={max}
        />
        <span className="text-[11px] text-text-faint">to</span>
        <input
          type="number"
          value={value.max}
          onChange={(e) => onChange({ minPrice: value.min, maxPrice: e.target.value })}
          className="w-full rounded-xl border border-border bg-surface-1 px-2 py-1.5 text-xs text-text"
          placeholder={`${max}`}
          min={min}
          max={max}
        />
      </div>
    </div>
  );
}

interface BrandFilterProps {
  brands?: Array<{ brand: string; count: number }>;
  selected: string[];
  onToggle: (brand: string) => void;
}

function BrandFilter({ brands, selected, onToggle }: BrandFilterProps) {
  if (!brands || brands.length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Brands</p>
      <div className="max-h-40 space-y-1 overflow-y-auto">
        {brands.slice(0, 20).map((item) => {
          const active = selected.includes(item.brand);
          return (
            <label key={item.brand} className="flex items-center gap-2">
              <input
                type="checkbox"
                className="h-3.5 w-3.5 rounded border-border text-primary"
                checked={active}
                onChange={() => onToggle(item.brand)}
              />
              <span className="flex-1 truncate text-xs text-text">{item.brand}</span>
              <span className="text-[10px] text-text-faint">{item.count}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

interface RatingFilterProps {
  ratings?: Array<{ min_rating: number; label: string; count: number }>;
  selected: string;
  onSelect: (minRating: string) => void;
}

function RatingFilter({ ratings, selected, onSelect }: RatingFilterProps) {
  if (!ratings || ratings.length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Rating</p>
      <div className="space-y-1">
        {ratings.map((item) => (
          <button
            key={item.min_rating}
            type="button"
            onClick={() => onSelect(selected === String(item.min_rating) ? "" : String(item.min_rating))}
            className={`flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-xs transition-colors ${
              selected === String(item.min_rating) ? "bg-primary/10 text-primary" : "hover:bg-surface-2"
            }`}
          >
            <span className="inline-flex items-center gap-1">
              <Star className="h-3 w-3" />
              {item.label}
            </span>
            <span className="text-[10px] text-text-faint">{item.count}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

interface AttributeFilterProps {
  attr: {
    id: number;
    name: string;
    type: string;
    display_order: number;
    options: Array<{ value: string; display: string; count: number }>;
  };
  selected: string[];
  onToggle: (value: string) => void;
}

function AttributeFilter({ attr, selected, onToggle }: AttributeFilterProps) {
  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">{attr.name}</p>
      <div className="flex flex-wrap gap-1.5">
        {attr.options.map((opt) => {
          const active = selected.includes(opt.value);
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onToggle(opt.value)}
              className={`rounded-lg border px-2 py-1 text-[11px] font-medium transition-colors ${
                active
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border bg-surface-1 text-text-muted hover:border-primary/40"
              }`}
            >
              {opt.display}
              <span className="ml-1 text-[10px] text-text-faint">({opt.count})</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

interface BooleanFilterFieldProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function BooleanFilterField({ label, checked, onChange }: BooleanFilterFieldProps) {
  return (
    <label className="flex items-center justify-between rounded-lg px-2 py-1.5 transition-colors hover:bg-surface-2">
      <span className="text-xs text-text">{label}</span>
      <input
        type="checkbox"
        className="h-3.5 w-3.5 rounded border-border text-primary"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
    </label>
  );
}
