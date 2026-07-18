/**
 * productDetailScreen.test.ts
 * Tests the cart and wishlist interactions used by the product detail screen.
 * Renders no JSX — tests the store actions that the screen triggers.
 */

const mockApiFetch = jest.fn();

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  login: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
  register: jest.fn(),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: { clearAccessToken: jest.fn(), clearRefreshToken: jest.fn() },
}));

import { useCartStore } from "@/lib/cartStore";
import { useWishlistStore } from "@/lib/wishlistStore";

const product = {
  id: 42,
  name: "Test Shoe",
  price: 99,
  image_url: "",
  description: "",
  category: "shoes",
  stock: 5,
  is_active: true,
};

beforeEach(() => {
  useCartStore.setState({ items: [], total: 0, itemCount: 0, isLoading: false });
  useWishlistStore.setState({ items: [], isLoading: false });
  jest.clearAllMocks();
});

describe("Product detail — add to cart flow", () => {
  it("adds product to cart and reflects updated total", async () => {
    mockApiFetch
      .mockResolvedValueOnce({}) // POST /cart
      .mockResolvedValueOnce({
        items: [{ product_id: 42, product_name: "Test Shoe", image_url: "", price: 99, quantity: 1 }],
      }); // GET /cart

    await useCartStore.getState().addItem(product as any);

    expect(useCartStore.getState().items).toHaveLength(1);
    expect(useCartStore.getState().total).toBe(99);
  });
});

describe("Product detail — wishlist toggle flow", () => {
  it("adds product to wishlist", async () => {
    mockApiFetch
      .mockResolvedValueOnce({}) // POST /wishlist/add
      .mockResolvedValueOnce([{ id: 1, product_id: 42, created_at: "", product: { id: 42, name: "Test", price: 50 } }]); // GET /wishlist

    await useWishlistStore.getState().add(42);

    expect(useWishlistStore.getState().has(42)).toBe(true);
  });

  it("removes product from wishlist", async () => {
    useWishlistStore.setState({
      items: [{ id: 1, product_id: 42, created_at: "", product: { id: 42, name: "Test", price: 50 } as any }],
    });
    mockApiFetch.mockResolvedValueOnce({}); // DELETE /wishlist/42

    await useWishlistStore.getState().remove(42);

    expect(useWishlistStore.getState().has(42)).toBe(false);
  });
});
