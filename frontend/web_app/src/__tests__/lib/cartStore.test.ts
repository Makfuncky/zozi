/**
 * Tests for web_app/src/lib/cartStore.ts
 * Uses the Zustand store directly (not via React hooks).
 */

// Mock apiFetch and getAccessToken so store server mutations are no-ops
jest.mock("@/lib/api", () => ({
  apiFetch: jest.fn().mockResolvedValue(new Response("{}", { status: 200 })),
  getAccessToken: jest.fn().mockReturnValue(null),
}));

import { useCartStore } from "@/lib/cartStore";
import { Product } from "@/lib/types";

const { apiFetch: mockApiFetch } = jest.requireMock("@/lib/api");

// Suppress localStorage errors in jsdom
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

function makeProduct(id = 1, price = 10): Product {
  return {
    id,
    name: `Product ${id}`,
    price,
    image_url: null,
    description: "desc",
    category: "test",
    stock: 50,
    is_active: true,
  } as unknown as Product;
}

beforeEach(() => {
  // Reset store state between tests
  useCartStore.setState({ items: [] });
});

describe("cartStore — addItem", () => {
  it("adds a new item to the cart", () => {
    const { addItem } = useCartStore.getState();
    addItem(makeProduct(1));
    expect(useCartStore.getState().items).toHaveLength(1);
    expect(useCartStore.getState().items[0].id).toBe(1);
  });

  it("increments quantity when same variant added again", () => {
    useCartStore.getState().addItem(makeProduct(1));
    useCartStore.getState().addItem(makeProduct(1));
    const state = useCartStore.getState();
    expect(state.items).toHaveLength(1);
    expect(state.items[0].quantity).toBe(2);
  });

  it("treats different size variants as separate line items", () => {
    useCartStore.getState().addItem(makeProduct(1), { selectedSize: "S" });
    useCartStore.getState().addItem(makeProduct(1), { selectedSize: "L" });
    expect(useCartStore.getState().items).toHaveLength(2);
  });
});

describe("cartStore — removeItem", () => {
  it("removes the correct item by line_id", () => {
    useCartStore.getState().addItem(makeProduct(1));
    const lineId = useCartStore.getState().items[0].line_id;
    useCartStore.getState().removeItem(lineId);
    expect(useCartStore.getState().items).toHaveLength(0);
  });

  it("does nothing when line_id not found", () => {
    useCartStore.getState().addItem(makeProduct(1));
    useCartStore.getState().removeItem("nonexistent");
    expect(useCartStore.getState().items).toHaveLength(1);
  });
});

describe("cartStore — updateQuantity", () => {
  it("updates the quantity of an item", () => {
    useCartStore.getState().addItem(makeProduct(1));
    const lineId = useCartStore.getState().items[0].line_id;
    useCartStore.getState().updateQuantity(lineId, 5);
    expect(useCartStore.getState().items[0].quantity).toBe(5);
  });

  it("removes item when quantity set to 0", () => {
    useCartStore.getState().addItem(makeProduct(1));
    const lineId = useCartStore.getState().items[0].line_id;
    useCartStore.getState().updateQuantity(lineId, 0);
    expect(useCartStore.getState().items).toHaveLength(0);
  });
});

describe("cartStore — getTotal", () => {
  it("returns 0 for empty cart", () => {
    expect(useCartStore.getState().getTotal()).toBe(0);
  });

  it("sums price × quantity for all items", () => {
    useCartStore.getState().addItem(makeProduct(1, 10), { quantity: 2 });
    useCartStore.getState().addItem(makeProduct(2, 5), { quantity: 3 });
    expect(useCartStore.getState().getTotal()).toBe(35);
  });
});

describe("cartStore — clearCart", () => {
  it("empties all items", () => {
    useCartStore.getState().addItem(makeProduct(1));
    useCartStore.getState().addItem(makeProduct(2));
    useCartStore.getState().clearCart();
    expect(useCartStore.getState().items).toHaveLength(0);
  });
});

describe("cartStore — syncOnLogin", () => {
  it("hydrates from wrapped /cart response payloads", async () => {
    mockApiFetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          items: [
            {
              product_id: 11,
              product_name: "Server Product",
              product_price: 49,
              product_image: null,
              product_category: "bags",
              product_stock: 5,
              quantity: 2,
              cart_item_id: 33,
              selected_size: "L",
              selected_color: "Gold",
            },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    await useCartStore.getState().syncOnLogin();

    expect(useCartStore.getState().items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 11,
          quantity: 2,
          cart_item_id: 33,
          selected_size: "L",
          selected_color: "Gold",
        }),
      ])
    );
  });

  it("rebuilds a stable line_id when server rows carry an empty legacy line_id", async () => {
    mockApiFetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          items: [
            {
              product_id: 11,
              product_name: "Server Product",
              product_price: 49,
              product_image: null,
              product_category: "bags",
              product_stock: 5,
              quantity: 2,
              cart_item_id: 33,
              line_id: null,
              selected_size: " L ",
              selected_color: " Gold ",
            },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    await useCartStore.getState().syncOnLogin();

    expect(useCartStore.getState().items[0]).toEqual(
      expect.objectContaining({
        id: 11,
        line_id: "11::L::Gold",
        selected_size: "L",
        selected_color: "Gold",
      })
    );
  });

  it("merges wrapped /cart/sync response payloads for local carts", async () => {
    useCartStore.getState().addItem(makeProduct(7, 15), { quantity: 3, selectedSize: "M" });
    mockApiFetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          items: [
            {
              product_id: 7,
              product_name: "Merged Product",
              product_price: 15,
              product_image: null,
              product_category: "test",
              product_stock: 50,
              quantity: 3,
              cart_item_id: 44,
              selected_size: "M",
              selected_color: "",
            },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    await useCartStore.getState().syncOnLogin();

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/cart/sync",
      expect.objectContaining({ method: "PUT" })
    );
    expect(useCartStore.getState().items[0]).toEqual(
      expect.objectContaining({
        id: 7,
        quantity: 3,
        cart_item_id: 44,
        selected_size: "M",
      })
    );
  });
});

describe("cartStore — initialize", () => {
  it("repairs legacy local cart rows that only store product_id", () => {
    (window.localStorage.getItem as jest.Mock).mockImplementation((key: string) => {
      if (key === "zozi_has_session") return "1";
      if (key === "cart-storage") {
        return JSON.stringify([
          {
            product_id: 21,
            name: "Legacy Product",
            quantity: 1,
            selected_size: "M",
            selected_color: "Blue",
          },
        ]);
      }
      return null;
    });

    useCartStore.getState().initialize();

    expect(useCartStore.getState().items[0]).toEqual(
      expect.objectContaining({
        id: 21,
        line_id: "21::M::Blue",
        selected_size: "M",
        selected_color: "Blue",
      })
    );
  });
});
