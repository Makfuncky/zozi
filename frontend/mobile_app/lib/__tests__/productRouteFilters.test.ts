import { resolveProductRouteFilters } from "@/lib/productRouteFilters";

describe("resolveProductRouteFilters", () => {
  it("maps route params into initial product-screen filters", () => {
    expect(resolveProductRouteFilters({
      category: "electronics",
      trending: "1",
      newArrivals: "true",
      supplier: "Acme",
      brand: "Nova",
      color: "Black",
      discountPct: "25",
      search: "buds",
    })).toEqual({
      category: "electronics",
      search: "buds",
      supplier: "Acme",
      brand: "Nova",
      color: "Black",
      trendingOnly: true,
      newArrivals: true,
      discountPct: "25",
    });
  });

  it("falls back to safe defaults when route params are absent", () => {
    expect(resolveProductRouteFilters({})).toEqual({
      category: "all",
      search: "",
      supplier: "",
      brand: "",
      color: "",
      trendingOnly: false,
      newArrivals: false,
      discountPct: "",
    });
  });
});