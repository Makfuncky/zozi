/**
 * Tests for web_app/src/lib/wishlistStore.ts
 */

jest.mock("@/lib/api", () => ({
  apiFetch: jest.fn().mockResolvedValue({ ok: true, json: async () => [] }),
  getAccessToken: jest.fn().mockReturnValue(null),
}));

// Suppress localStorage in jsdom
beforeAll(() => {
  Object.defineProperty(window, "localStorage", {
    value: {
      getItem: jest.fn(() => null),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    },
    writable: true,
  });
});

import { useWishlistStore } from "@/lib/wishlistStore";

beforeEach(() => {
  useWishlistStore.setState({ ids: [], synced: false });
  jest.clearAllMocks();
});

describe("wishlistStore — add", () => {
  it("adds an id to the store", () => {
    useWishlistStore.getState().add(42);
    expect(useWishlistStore.getState().ids).toContain(42);
  });

  it("does not duplicate ids", () => {
    useWishlistStore.getState().add(42);
    useWishlistStore.getState().add(42);
    expect(useWishlistStore.getState().ids.filter((i) => i === 42)).toHaveLength(1);
  });
});

describe("wishlistStore — remove", () => {
  it("removes an id", () => {
    useWishlistStore.getState().add(10);
    useWishlistStore.getState().remove(10);
    expect(useWishlistStore.getState().ids).not.toContain(10);
  });

  it("is a no-op for unknown ids", () => {
    useWishlistStore.getState().add(10);
    useWishlistStore.getState().remove(99);
    expect(useWishlistStore.getState().ids).toHaveLength(1);
  });
});

describe("wishlistStore — isInWishlist", () => {
  it("returns true when id is present", () => {
    useWishlistStore.getState().add(7);
    expect(useWishlistStore.getState().isInWishlist(7)).toBe(true);
  });

  it("returns false when id is absent", () => {
    expect(useWishlistStore.getState().isInWishlist(99)).toBe(false);
  });
});
