import { create } from "zustand";
import { Product } from "@shared/types";
import { apiFetch } from "@/lib/api";

export interface CartItem {
  id?: number;
  product_id: number;
  product_name: string;
  image_url: string;
  price: number;
  quantity: number;
  selected_size?: string;
  selected_color?: string;
  available_stock?: number;
  is_available?: boolean;
  availability_reason?: string | null;
}

interface CartState {
  items: CartItem[];
  isLoading: boolean;
  total: number;
  itemCount: number;
  fetchCart: () => Promise<void>;
  addItem: (product: Product, qty?: number, size?: string, color?: string) => Promise<void>;
  removeItem: (cartItemId: number, fallbackProductId?: number) => Promise<void>;
  updateQty: (cartItemId: number, qty: number, fallbackProductId?: number) => Promise<void>;
  clearCart: () => void;
}

function computeTotals(items: CartItem[]) {
  const total = items.reduce((s, i) => s + i.price * i.quantity, 0);
  const itemCount = items.reduce((s, i) => s + i.quantity, 0);
  return { total, itemCount };
}

function matchesCartItem(item: CartItem, cartItemId: number, fallbackProductId?: number) {
  if (item.id != null) {
    return item.id === cartItemId;
  }
  return item.product_id === (fallbackProductId ?? cartItemId);
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  isLoading: false,
  total: 0,
  itemCount: 0,

  async fetchCart() {
    set({ isLoading: true });
    try {
      const data = await apiFetch<{ items: any[] }>("/cart");
      const rawItems = data.items ?? [];
      const items: CartItem[] = rawItems.map((item: any) => ({
        id: typeof item.id === "number" ? item.id : undefined,
        product_id: item.product_id,
        product_name: item.product?.name ?? item.product_name ?? "",
        image_url: item.product?.image_url ?? item.image_url ?? "",
        price: item.product?.price ?? item.price ?? 0,
        quantity: item.quantity,
        selected_size: item.selected_size ?? "",
        selected_color: item.selected_color ?? null,
        available_stock: typeof item.available_stock === "number" ? item.available_stock : undefined,
        is_available: typeof item.is_available === "boolean" ? item.is_available : undefined,
        availability_reason: typeof item.availability_reason === "string" ? item.availability_reason : null,
      }));
      set({ items, ...computeTotals(items) });
    } catch {
      // stay with local state
    } finally {
      set({ isLoading: false });
    }
  },

  async addItem(product, qty = 1, size, color) {
    await apiFetch("/cart/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: product.id,
        quantity: qty,
        selected_size: size ?? "",
        selected_color: color ?? null,
      }),
    });
    await get().fetchCart();
  },

  async removeItem(cartItemId, fallbackProductId) {
    await apiFetch(`/cart/items/${cartItemId}`, { method: "DELETE" });
    const items = get().items.filter((item) => !matchesCartItem(item, cartItemId, fallbackProductId));
    set({ items, ...computeTotals(items) });
  },

  async updateQty(cartItemId, qty, fallbackProductId) {
    if (qty <= 0) {
      await get().removeItem(cartItemId, fallbackProductId);
      return;
    }
    await apiFetch(`/cart/items/${cartItemId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quantity: qty }),
    });
    const items = get().items.map((item) =>
      matchesCartItem(item, cartItemId, fallbackProductId) ? { ...item, quantity: qty } : item
    );
    set({ items, ...computeTotals(items) });
  },

  clearCart() {
    apiFetch("/cart", { method: "DELETE" }).catch(() => {});
    set({ items: [], total: 0, itemCount: 0 });
  },
}));
