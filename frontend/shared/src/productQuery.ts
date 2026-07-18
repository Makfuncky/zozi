import { Product } from "./types";

export type ProductSortOption = {
  value: string;
  label: string;
};

export const PRODUCT_CATEGORIES = [
  "all",
  "electronics",
  "fashion",
  "accessories",
  "furniture",
  "beauty",
  "sports",
  "home",
  "books",
  "grocery",
] as const;

export const PRODUCT_SORT_OPTIONS: ProductSortOption[] = [
  { value: "newest", label: "Newest" },
  { value: "rating", label: "Rating" },
  { value: "bestseller", label: "Best Seller" },
  { value: "discount", label: "Biggest Discount" },
];

export function buildProductQueryParams(params: {
  search?: string;
  category?: string;
  sort?: string;
  trending?: boolean;
  newArrivals?: boolean;
  bestSellers?: boolean;
  deals?: boolean;
  discountPct?: string;
  minPrice?: string;
  maxPrice?: string;
  brand?: string;
  brands?: string[];
  color?: string;
  minRating?: string;
  inStock?: boolean;
  tag?: string;
  selectedTag?: string;
  supplier?: string;
  saleId?: string;
  hasVideo?: boolean;
  hasDiscount?: boolean;
  attributes?: Record<string, string[]>;
  limit?: number;
  offset?: number;
}): string {
  const qp = new URLSearchParams();
  if (params.search) qp.set("q", params.search);
  if (params.category && params.category !== "all") qp.set("category", params.category);
  if (params.sort && params.sort !== "default") {
    const sortValue = params.sort.replace(":", "_");
    qp.set("sort", sortValue);
  }
  if (params.trending) qp.set("trending", "1");
  if (params.newArrivals) qp.set("new_arrivals", "1");
  if (params.bestSellers) qp.set("best_sellers", "1");
  if (params.deals) qp.set("deals", "1");
  if (params.discountPct) qp.set("min_discount", params.discountPct);
  if (params.hasDiscount) qp.set("has_discount", "1");
  if (params.minPrice) qp.set("min_price", params.minPrice);
  if (params.maxPrice) qp.set("max_price", params.maxPrice);
  if (params.brand) qp.set("brand", params.brand);
  if (params.brands && params.brands.length) qp.set("brands", params.brands.join(","));
  if (params.color) qp.set("color", params.color);
  if (params.minRating) qp.set("min_rating", params.minRating);
  if (params.inStock) qp.set("in_stock", "true");
  if (params.tag) qp.set("tag", params.tag);
  if (params.supplier) qp.set("supplier", params.supplier);
  if (params.saleId) qp.set("sale_id", params.saleId);
  if (params.hasVideo) qp.set("has_video", "1");
  if (params.attributes && Object.keys(params.attributes).length) {
    qp.set("attributes", JSON.stringify(params.attributes));
  }
  return qp.toString();
}

export function mapSortOptionToFields(sort: string): { sort_by?: string; sort_order?: string } {
  if (!sort || sort === "default") return {};
  if (sort.includes(":")) {
    const [field, order] = sort.split(":");
    return { sort_by: field, sort_order: order };
  }
  switch (sort) {
    case "newest":
      return { sort_by: "created_at", sort_order: "desc" };
    case "rating":
      return { sort_by: "rating", sort_order: "desc" };
    case "bestseller":
      return { sort_by: "sales", sort_order: "desc" };
    case "discount":
      return { sort_by: "discount_pct", sort_order: "desc" };
    default:
      return {};
  }
}

export function normalizeProductItems(items: Product[]): Product[] {
  return items.map((item) => ({ ...item, isNew: item.isNew ?? false, isFeatured: item.isFeatured ?? false }));
}
