/**
 * Tests for web_app/src/lib/utils.ts
 * Covers: cn, resolveImage, fmtSold, slugify
 */

// Mock API_URL used inside utils.ts
jest.mock("@/lib/api", () => ({
  API_URL: "http://localhost:8000",
}));

import { cn, resolveImage, fmtSold, slugify, supplierStorefrontPath } from "@/lib/utils";

// ── cn ────────────────────────────────────────────────────────────────────────

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("handles conditional classes", () => {
    const skip = false;
    expect(cn("base", skip && "skip", "visible")).toBe("base visible");
  });

  it("deduplicates Tailwind conflicts (twMerge)", () => {
    // p-2 should win over p-1 when both supplied
    expect(cn("p-1", "p-2")).toBe("p-2");
  });
});

// ── resolveImage ──────────────────────────────────────────────────────────────

describe("resolveImage", () => {
  it("returns placeholder for undefined", () => {
    expect(resolveImage(undefined)).toBe("/placeholder.svg");
  });

  it("returns placeholder for empty string", () => {
    expect(resolveImage("")).toBe("/placeholder.svg");
  });

  it("maps the legacy placeholder path to the current asset", () => {
    expect(resolveImage("/placeholder.jpg")).toBe("/placeholder.svg");
  });

  it("returns absolute https URL as-is", () => {
    expect(resolveImage("https://cdn.example.com/img.jpg")).toBe("https://cdn.example.com/img.jpg");
  });

  it("prefixes /uploads/ paths with API_URL", () => {
    expect(resolveImage("/uploads/photo.jpg")).toBe("http://localhost:8000/uploads/photo.jpg");
  });

  it("prefixes relative uploads/ path", () => {
    expect(resolveImage("uploads/photo.jpg")).toBe("http://localhost:8000/uploads/photo.jpg");
  });

  it("treats bare filename as legacy upload", () => {
    expect(resolveImage("photo.jpg")).toBe("http://localhost:8000/uploads/photo.jpg");
  });

  it("normalises Windows backslashes", () => {
    expect(resolveImage("/uploads\\photo.jpg")).toBe("http://localhost:8000/uploads/photo.jpg");
  });
});

// ── fmtSold ───────────────────────────────────────────────────────────────────

describe("fmtSold", () => {
  it("formats numbers below 1000 with + suffix", () => {
    expect(fmtSold(42)).toBe("42+");
  });

  it("formats numbers >= 1000 as k+ notation", () => {
    expect(fmtSold(1500)).toBe("1.5k+");
  });

  it("rounds to 1 decimal", () => {
    expect(fmtSold(10000)).toBe("10.0k+");
  });
});

// ── slugify ───────────────────────────────────────────────────────────────────

describe("slugify", () => {
  it("lowercases and replaces spaces with dashes", () => {
    expect(slugify("Blue Headphones")).toBe("blue-headphones");
  });

  it("strips special characters", () => {
    expect(slugify("Best Product! (2024)")).toMatch(/^best-product.*2024$/);
  });
});

describe("supplierStorefrontPath", () => {
  it("builds the canonical storefront route from a supplier slug", () => {
    expect(supplierStorefrontPath({ slug: "dream-mart" })).toBe("/supplier=dream-mart");
  });

  it("falls back to business name when slug is absent", () => {
    expect(supplierStorefrontPath({ business_name: "Dream Mart" })).toBe("/supplier=dream-mart");
  });
});
