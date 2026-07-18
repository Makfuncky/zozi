import { mapProductToCardModel } from "./ProductCard";
import { getProductBadges, getProductDiscountPercent } from "../productHelpers";

test("mapProductToCardModel maps product fields correctly", () => {
  const product = {
    id: 100,
    name: "Test Product",
    price: 49.99,
    compare_price: 99.99,
    image_url: "https://placehold.co/300x300",
    stock: 5,
    category: "fashion",
    supplier: "Test Supplier",
    rating: 4.8,
    sales_count: 200,
    tags: "new, hot, trend",
    ai_description: "Best product ever",
  };

  const model = mapProductToCardModel(
    product as any,
    (price) => `$${price.toFixed(2)}`,
    (p) => p.supplier || "ZOZI CURATED"
  );

  expect(model.id).toBe(100);
  expect(model.name).toBe("Test Product");
  expect(model.formattedPrice).toBe("$49.99");
  expect(model.formattedComparePrice).toBe("$99.99");
  expect(model.discountPercent).toBeGreaterThan(0);
  expect(model.inStock).toBe(true);
  expect(model.tags).toEqual(["new", "hot", "trend"]);
});

test("getProductDiscountPercent handles string numeric API payloads", () => {
  const product = {
    price: "80.00",
    compare_price: "100.00",
    offer_discount_pct: null,
  };

  expect(getProductDiscountPercent(product as any)).toBe(20);
});

test("getProductBadges renders promotion offers as red badges", () => {
  const product = {
    id: 1,
    name: "Bundle Deal",
    description: "Buy one get one free",
    price: "80.00",
    compare_price: "100.00",
    image_url: "https://placehold.co/300x300",
    stock: 3,
    category: "fashion",
    offer_type: "promotion",
    offer_discount_pct: 20,
  };

  const [badge] = getProductBadges(product as any);
  expect(badge.label).toContain("DEAL");
  expect(badge.cls).toContain("bg-danger");
});
