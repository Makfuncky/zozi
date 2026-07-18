import { buildHomeCategoryHighlights } from "@/lib/homeInsights";

describe("buildHomeCategoryHighlights", () => {
  it("aggregates and sorts marketplace categories for the home dashboard", () => {
    const highlights = buildHomeCategoryHighlights([
      { id: 1, name: "Noise Cancelling Headphones", category: "Electronics" },
      { id: 2, name: "Smart Watch", category: "electronics" },
      { id: 3, name: "Running Shoes", category: "Sports" },
      { id: 4, name: "Leather Tote", category: "Accessories" },
    ] as any);

    expect(highlights[0]).toMatchObject({ slug: "electronics", count: 2, sampleName: "Noise Cancelling Headphones" });
    expect(highlights.map((item) => item.slug)).toEqual(["electronics", "accessories", "sports"]);
  });
});
