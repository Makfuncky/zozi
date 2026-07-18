import {
  inferSuggestedSubCategory,
  mergeVariantOptions,
  normalizeSuggestedColor,
  resolveKnownCategory,
} from "@/lib/supplierProductForm";

describe("supplierProductForm helpers", () => {
  it("normalizes common AI color aliases", () => {
    expect(normalizeSuggestedColor("gray")).toBe("Grey");
    expect(normalizeSuggestedColor("off white")).toBe("Ivory");
  });

  it("resolves known categories with canonical casing", () => {
    expect(resolveKnownCategory("furniture")).toBe("Furniture");
    expect(resolveKnownCategory("unknown value")).toBe("General");
  });

  it("infers storage for cupboard-style furniture text", () => {
    expect(inferSuggestedSubCategory("Furniture", "Brown rectangular wooden cupboard with storage shelves")).toBe("Storage");
  });

  it("merges AI variant options into a clean single string", () => {
    expect(mergeVariantOptions(["S", "M", "M", "L"], "")).toBe("S, M, L");
    expect(mergeVariantOptions(null, "One Size")).toBe("One Size");
  });
});