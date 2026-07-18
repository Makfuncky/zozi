/**
 * Tests for mobile_app/lib/wishlistStore.ts
 */

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

const mockApiFetch = jest.fn();
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

import { useWishlistStore } from "@/lib/wishlistStore";

function makeEntry(productId: number) {
  return { id: productId, product_id: productId, created_at: "", product: { id: productId, name: "Product", price: 10 } as any };
}

beforeEach(() => {
  useWishlistStore.setState({ items: [], isLoading: false });
  jest.clearAllMocks();
});

describe("mobile wishlistStore — fetch", () => {
  it("populates items on success", async () => {
    mockApiFetch.mockResolvedValueOnce([makeEntry(1), makeEntry(2)]);

    await useWishlistStore.getState().fetch();

    expect(useWishlistStore.getState().items).toHaveLength(2);
    expect(useWishlistStore.getState().isLoading).toBe(false);
  });

  it("treats non-array response as empty", async () => {
    mockApiFetch.mockResolvedValueOnce(null);

    await useWishlistStore.getState().fetch();

    expect(useWishlistStore.getState().items).toHaveLength(0);
  });

  it("keeps existing items on API error", async () => {
    useWishlistStore.setState({ items: [makeEntry(5)] });
    mockApiFetch.mockRejectedValueOnce(new Error("network"));

    await useWishlistStore.getState().fetch();

    expect(useWishlistStore.getState().items).toHaveLength(1);
  });
});

describe("mobile wishlistStore — add", () => {
  it("calls POST /wishlist/:id then refetches", async () => {
    mockApiFetch
      .mockResolvedValueOnce({}) // POST
      .mockResolvedValueOnce([makeEntry(7)]); // fetch

    await useWishlistStore.getState().add(7);

    expect(mockApiFetch).toHaveBeenCalledTimes(2);
    expect(mockApiFetch.mock.calls[0][0]).toBe("/wishlist/7");
    expect(mockApiFetch.mock.calls[0][1].method).toBe("POST");
    expect(useWishlistStore.getState().items[0].product_id).toBe(7);
  });
});

describe("mobile wishlistStore — remove", () => {
  it("calls DELETE and removes item from local state", async () => {
    useWishlistStore.setState({ items: [makeEntry(3), makeEntry(4)] });
    mockApiFetch.mockResolvedValueOnce({});

    await useWishlistStore.getState().remove(3);

    expect(mockApiFetch).toHaveBeenCalledWith("/wishlist/3", { method: "DELETE" });
    expect(useWishlistStore.getState().items).toHaveLength(1);
    expect(useWishlistStore.getState().items[0].product_id).toBe(4);
  });
});

describe("mobile wishlistStore — has", () => {
  it("returns true when product is in wishlist", () => {
    useWishlistStore.setState({ items: [makeEntry(10)] });
    expect(useWishlistStore.getState().has(10)).toBe(true);
  });

  it("returns false when product is not in wishlist", () => {
    useWishlistStore.setState({ items: [makeEntry(10)] });
    expect(useWishlistStore.getState().has(99)).toBe(false);
  });
});
