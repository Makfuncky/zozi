import type { Product } from "@shared/types";

export interface HomeCategoryHighlight {
  slug: string;
  label: string;
  count: number;
  sampleName: string;
  accent: string;
}

const CATEGORY_META: Record<string, { label: string; accent: string }> = {
  electronics: { label: "Electronics", accent: "#2563eb" },
  fashion: { label: "Fashion", accent: "#db2777" },
  accessories: { label: "Accessories", accent: "#7c3aed" },
  furniture: { label: "Furniture", accent: "#b45309" },
  beauty: { label: "Beauty", accent: "#ec4899" },
  sports: { label: "Sports", accent: "#16a34a" },
  home: { label: "Home & Living", accent: "#0891b2" },
  books: { label: "Books", accent: "#4f46e5" },
  grocery: { label: "Grocery", accent: "#65a30d" },
  baby: { label: "Baby & Kids", accent: "#f97316" },
  automotive: { label: "Automotive", accent: "#6b7280" },
  crafts: { label: "Crafts", accent: "#9333ea" },
  other: { label: "Marketplace Picks", accent: "#0f766e" },
};

function toSlug(rawValue?: string | null): string {
  const normalized = String(rawValue || "")
    .trim()
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");

  if (!normalized) return "other";
  if (normalized.includes("elect")) return "electronics";
  if (normalized.includes("fashion") || normalized.includes("cloth") || normalized.includes("apparel")) return "fashion";
  if (normalized.includes("accessor") || normalized.includes("watch") || normalized.includes("jewel")) return "accessories";
  if (normalized.includes("furnitur")) return "furniture";
  if (normalized.includes("beaut") || normalized.includes("cosmetic")) return "beauty";
  if (normalized.includes("sport")) return "sports";
  if (normalized.includes("home") || normalized.includes("living") || normalized.includes("kitchen")) return "home";
  if (normalized.includes("book")) return "books";
  if (normalized.includes("grocery") || normalized.includes("food")) return "grocery";
  if (normalized.includes("baby") || normalized.includes("kids")) return "baby";
  if (normalized.includes("auto")) return "automotive";
  if (normalized.includes("craft")) return "crafts";
  return normalized in CATEGORY_META ? normalized : "other";
}

export function buildHomeCategoryHighlights(products: Product[], limit = 4): HomeCategoryHighlight[] {
  const buckets = new Map<string, { count: number; sampleName: string }>();

  products.forEach((product) => {
    const slug = toSlug(product.category);
    const current = buckets.get(slug);
    if (current) {
      current.count += 1;
      return;
    }

    buckets.set(slug, {
      count: 1,
      sampleName: product.name,
    });
  });

  return Array.from(buckets.entries())
    .map(([slug, value]) => ({
      slug,
      label: CATEGORY_META[slug]?.label || CATEGORY_META.other.label,
      accent: CATEGORY_META[slug]?.accent || CATEGORY_META.other.accent,
      count: value.count,
      sampleName: value.sampleName,
    }))
    .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label))
    .slice(0, limit);
}
