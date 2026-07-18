import { hasCreateAiSource, hasEditAiSource, isVideoAsset } from "@/lib/supplierProductAi";

describe("supplierProductAi helpers", () => {
  it("treats the create screen main image as a valid AI source", () => {
    const mainImage = { uri: "file:///product.jpg", name: "product.jpg", mimeType: "image/jpeg" } as any;

    expect(hasCreateAiSource("", "", mainImage)).toBe(true);
  });

  it("treats the edit screen current image url as a valid AI source", () => {
    expect(hasEditAiSource("", "", null, "/uploads/product.jpg", [])).toBe(true);
  });

  it("treats the edit screen existing gallery images as a valid AI source", () => {
    expect(hasEditAiSource("", "", null, "", ["/uploads/gallery-1.jpg"])).toBe(true);
  });

  it("filters video assets out of persisted gallery image reuse", () => {
    expect(isVideoAsset("/uploads/demo.mp4")).toBe(true);
    expect(isVideoAsset("/uploads/demo.jpg")).toBe(false);
  });
});