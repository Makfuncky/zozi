export interface ProductRouteFilters {
  category: string;
  search: string;
  supplier: string;
  brand: string;
  color: string;
  trendingOnly: boolean;
  newArrivals: boolean;
  discountPct: string;
}

function firstValue(value?: string | string[]): string {
  if (Array.isArray(value)) return String(value[0] || "");
  return String(value || "");
}

function toBooleanFlag(value?: string | string[]): boolean {
  const normalized = firstValue(value).trim().toLowerCase();
  return normalized === "1" || normalized === "true" || normalized === "yes";
}

export function resolveProductRouteFilters(
  params: Record<string, string | string[] | undefined>,
): ProductRouteFilters {
  const category = firstValue(params.category).trim().toLowerCase() || "all";

  return {
    category,
    search: firstValue(params.search).trim(),
    supplier: firstValue(params.supplier).trim(),
    brand: firstValue(params.brand).trim(),
    color: firstValue(params.color).trim(),
    trendingOnly: toBooleanFlag(params.trending),
    newArrivals: toBooleanFlag(params.newArrivals),
    discountPct: firstValue(params.discountPct).trim(),
  };
}
