/**
 * Tests for mobile_app/lib/cartStore.ts
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

import { useCartStore } from "@/lib/cartStore";

function makeProduct(id = 1, price = 10) {
  return { id, name: `Product ${id}`, price, image_url: "", description: "", category: "test", stock: 10, is_active: true };
}

beforeEach(() => {
  useCartStore.setState({ items: [], total: 0, itemCount: 0, isLoading: false });
  jest.clearAllMocks();
});

describe("mobile cartStore — fetchCart", () => {
  it("populates items from API response (flat format)", async () => {
    const items = [{ id: 11, product_id: 1, product_name: "Widget", image_url: "/img.jpg", price: 10, quantity: 2, selected_size: "M", selected_color: "Red", available_stock: 5, is_available: true, availability_reason: null }];
    mockApiFetch.mockResolvedValueOnce({ items });

    await useCartStore.getState().fetchCart();

    expect(useCartStore.getState().items).toHaveLength(1);
    expect(useCartStore.getState().items[0].id).toBe(11);
    expect(useCartStore.getState().items[0].product_name).toBe("Widget");
    expect(useCartStore.getState().items[0].available_stock).toBe(5);
    expect(useCartStore.getState().items[0].is_available).toBe(true);
    expect(useCartStore.getState().total).toBe(20);
  });

  it("populates items from API response (nested product format)", async () => {
    const items = [{
      product_id: 2,
      quantity: 3,
      selected_size: "L",
      selected_color: "Blue",
      product: { name: "Gadget", image_url: "/g.jpg", price: 15 },
    }];
    mockApiFetch.mockResolvedValueOnce({ items });

    await useCartStore.getState().fetchCart();

    expect(useCartStore.getState().items).toHaveLength(1);
    expect(useCartStore.getState().items[0].product_name).toBe("Gadget");
    expect(useCartStore.getState().items[0].image_url).toBe("/g.jpg");
    expect(useCartStore.getState().items[0].price).toBe(15);
    expect(useCartStore.getState().total).toBe(45);
  });

  it("leaves state unchanged on API error", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("network failure"));

    await useCartStore.getState().fetchCart();
    expect(useCartStore.getState().items).toHaveLength(0);
  });
});

describe("mobile cartStore — addItem", () => {
  it("calls POST /cart/items and then fetchCart", async () => {
    mockApiFetch
      .mockResolvedValueOnce({}) // addItem POST
      .mockResolvedValueOnce({ items: [{ product_id: 1, product_name: "Widget", image_url: "", price: 10, quantity: 1 }] }); // fetchCart

    await useCartStore.getState().addItem(makeProduct() as any);

    expect(mockApiFetch).toHaveBeenCalledTimes(2);
    expect(mockApiFetch.mock.calls[0][0]).toBe("/cart/items");
    expect(mockApiFetch.mock.calls[0][1].method).toBe("POST");
    expect(useCartStore.getState().items).toHaveLength(1);
  });

  it("sends selected_size and selected_color", async () => {
    mockApiFetch
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ items: [] });

    await useCartStore.getState().addItem(makeProduct() as any, 2, "L", "Blue");

    const body = JSON.parse(mockApiFetch.mock.calls[0][1].body);
    expect(body.selected_size).toBe("L");
    expect(body.selected_color).toBe("Blue");
    expect(body.quantity).toBe(2);
  });
});

describe("mobile cartStore — removeItem", () => {
  it("calls DELETE /cart/items/:id and removes from local state", async () => {
    useCartStore.setState({
      items: [{ id: 101, product_id: 1, product_name: "A", image_url: "", price: 10, quantity: 1 }],
      total: 10,
      itemCount: 1,
    });
    mockApiFetch.mockResolvedValueOnce({});

    await useCartStore.getState().removeItem(101, 1);

    expect(mockApiFetch).toHaveBeenCalledWith("/cart/items/101", { method: "DELETE" });
    expect(useCartStore.getState().items).toHaveLength(0);
    expect(useCartStore.getState().total).toBe(0);
  });

  it("removes only the matching variant row when the same product is in the cart twice", async () => {
    useCartStore.setState({
      items: [
        { id: 201, product_id: 9, product_name: "Variant A", image_url: "", price: 10, quantity: 1, selected_size: "M", selected_color: "Red" },
        { id: 202, product_id: 9, product_name: "Variant B", image_url: "", price: 10, quantity: 2, selected_size: "L", selected_color: "Blue" },
      ],
      total: 30,
      itemCount: 3,
    });
    mockApiFetch.mockResolvedValueOnce({});

    await useCartStore.getState().removeItem(201, 9);

    expect(useCartStore.getState().items).toEqual([
      expect.objectContaining({ id: 202, product_id: 9, selected_size: "L", selected_color: "Blue", quantity: 2 }),
    ]);
    expect(useCartStore.getState().total).toBe(20);
    expect(useCartStore.getState().itemCount).toBe(2);
  });
});

describe("mobile cartStore — clearCart", () => {
  it("empties all items and calls DELETE /cart", () => {
    useCartStore.setState({
      items: [{ product_id: 1, product_name: "A", image_url: "", price: 10, quantity: 2 }],
      total: 20, itemCount: 2,
    });
    mockApiFetch.mockResolvedValueOnce({});

    useCartStore.getState().clearCart();

    expect(useCartStore.getState().items).toHaveLength(0);
    expect(useCartStore.getState().total).toBe(0);
    expect(mockApiFetch).toHaveBeenCalledWith("/cart", { method: "DELETE" });
  });
});

describe("mobile cartStore — updateQty", () => {
  it("calls PUT /cart/items/:id with quantity", async () => {
    useCartStore.setState({
      items: [{ id: 305, product_id: 5, product_name: "B", image_url: "", price: 20, quantity: 1 }],
      total: 20, itemCount: 1,
    });
    mockApiFetch.mockResolvedValueOnce({});

    await useCartStore.getState().updateQty(305, 3, 5);

    expect(mockApiFetch).toHaveBeenCalledWith("/cart/items/305", expect.objectContaining({
      method: "PUT",
    }));
    expect(useCartStore.getState().items[0].quantity).toBe(3);
    expect(useCartStore.getState().total).toBe(60);
  });

  it("updates only the matching cart row when the same product has multiple variants", async () => {
    useCartStore.setState({
      items: [
        { id: 401, product_id: 12, product_name: "Sneaker", image_url: "", price: 20, quantity: 1, selected_size: "42", selected_color: "Black" },
        { id: 402, product_id: 12, product_name: "Sneaker", image_url: "", price: 25, quantity: 2, selected_size: "43", selected_color: "White" },
      ],
      total: 70,
      itemCount: 3,
    });
    mockApiFetch.mockResolvedValueOnce({});

    await useCartStore.getState().updateQty(402, 5, 12);

    expect(useCartStore.getState().items).toEqual([
      expect.objectContaining({ id: 401, quantity: 1, selected_size: "42" }),
      expect.objectContaining({ id: 402, quantity: 5, selected_size: "43" }),
    ]);
    expect(useCartStore.getState().total).toBe(145);
    expect(useCartStore.getState().itemCount).toBe(6);
  });

  it("keeps quantities unchanged when the quantity update request fails", async () => {
    useCartStore.setState({
      items: [{ id: 601, product_id: 20, product_name: "Jacket", image_url: "", price: 40, quantity: 2 }],
      total: 80,
      itemCount: 2,
    });
    mockApiFetch.mockRejectedValueOnce(new Error("stock changed"));

    await expect(useCartStore.getState().updateQty(601, 3, 20)).rejects.toThrow("stock changed");

    expect(useCartStore.getState().items[0].quantity).toBe(2);
    expect(useCartStore.getState().total).toBe(80);
    expect(useCartStore.getState().itemCount).toBe(2);
  });

  it("keeps the cart row when removeItem fails", async () => {
    useCartStore.setState({
      items: [{ id: 701, product_id: 21, product_name: "Headphones", image_url: "", price: 55, quantity: 1 }],
      total: 55,
      itemCount: 1,
    });
    mockApiFetch.mockRejectedValueOnce(new Error("remove failed"));

    await expect(useCartStore.getState().removeItem(701, 21)).rejects.toThrow("remove failed");

    expect(useCartStore.getState().items).toEqual([
      expect.objectContaining({ id: 701, product_id: 21, quantity: 1 }),
    ]);
    expect(useCartStore.getState().total).toBe(55);
    expect(useCartStore.getState().itemCount).toBe(1);
  });

  it("removes item when qty is 0", async () => {
    useCartStore.setState({
      items: [{ id: 505, product_id: 5, product_name: "B", image_url: "", price: 20, quantity: 2 }],
      total: 40, itemCount: 2,
    });
    mockApiFetch.mockResolvedValueOnce({});

    await useCartStore.getState().updateQty(505, 0, 5);

    expect(useCartStore.getState().items).toHaveLength(0);
  });
});

