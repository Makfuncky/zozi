"use client";

import { create } from "zustand";
import { Product } from "./types";
import { apiFetch, getAccessToken } from "./api";

export interface CartItem extends Product {
  quantity: number;
  line_id: string;
  cart_item_id?: number;
  selected_size?: string;
  selected_color?: string;
}

export interface CartVariantOptions {
  selectedSize?: string;
  selectedColor?: string;
  quantity?: number;
}

interface CartState {
  items: CartItem[];
  addItem: (product: Product, options?: CartVariantOptions) => void;
  removeItem: (lineId: string) => void;
  updateQuantity: (lineId: string, quantity: number) => void;
  clearCart: () => void;
  getTotal: () => number;
  getItemCount: () => number;
  initialize: () => void;
  /** Call after login: push local cart to server, then load the merged result. */
  syncOnLogin: () => Promise<void>;
  /** Call after a transient auth blip: stop server mirroring but keep local cart. */
  detachFromServer: () => void;
  /** Call after an explicit logout: wipe the local guest cart from this device. */
  clearLocalCart: () => void;
}

const STORAGE_KEY = "cart-storage";

function normalizeVariant(value?: string): string {
  return (value || "").trim();
}

function buildLineId(productId: number | string, selectedSize?: string, selectedColor?: string): string {
  return `${productId}::${normalizeVariant(selectedSize)}::${normalizeVariant(selectedColor)}`;
}

function resolveProductId(value: unknown, fallback: string): number | string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return fallback;
}

function hasSession(): boolean {
  return typeof window !== "undefined" && localStorage.getItem("zozi_has_session") === "1";
}

function persist(items: CartItem[]) {
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }
}

function hydrate(): CartItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed)
      ? parsed.map((item, index) => {
          const selectedSize = normalizeVariant(item.selected_size);
          const selectedColor = normalizeVariant(item.selected_color);
          const productId = resolveProductId(item.id ?? item.product_id, `legacy-${index}`);

          return {
            ...item,
            id: productId,
            line_id: item.line_id || buildLineId(productId, selectedSize, selectedColor),
            selected_size: selectedSize,
            selected_color: selectedColor,
          };
        })
      : [];
  } catch {
    return [];
  }
}

/** True when the user is logged in and we should mirror mutations to the server. */
function isAuthenticated(): boolean {
  return typeof window !== "undefined" && hasSession() && Boolean(getAccessToken());
}

/** Convert a server cart row (has product snapshot fields) into a CartItem. */
function serverRowToItem(row: any): CartItem {
  const selectedSize = normalizeVariant(row.selected_size);
  const selectedColor = normalizeVariant(row.selected_color);
  const productId = resolveProductId(row.product_id ?? row.id, `server-${row.cart_item_id ?? "unknown"}`);

  return {
    ...row,
    id: productId,
    name: row.product_name ?? "",
    price: row.product_price ?? 0,
    image_url: row.product_image ?? null,
    description: "",
    category: row.product_category ?? row.category ?? "",
    stock: row.product_stock ?? row.stock ?? 0,
    is_active: true,
    quantity: row.quantity,
    cart_item_id: row.cart_item_id,
    line_id: buildLineId(productId, selectedSize, selectedColor),
    selected_size: selectedSize,
    selected_color: selectedColor,
  } as CartItem;
}

function extractServerCartItems(payload: unknown): any[] {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (
    payload &&
    typeof payload === "object" &&
    Array.isArray((payload as { items?: unknown[] }).items)
  ) {
    return (payload as { items: any[] }).items;
  }
  return [];
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],

  addItem: (product, options = {}) => {
    set((state) => {
      const selectedSize = normalizeVariant(options.selectedSize);
      const selectedColor = normalizeVariant(options.selectedColor);
      const lineId = buildLineId(product.id, selectedSize, selectedColor);
      const quantityToAdd = Math.max(1, options.quantity ?? 1);
      const existing = state.items.find((i) => i.line_id === lineId);
      let next: CartItem[];
      if (existing) {
        next = state.items.map((i) =>
          i.line_id === lineId ? { ...i, quantity: i.quantity + quantityToAdd } : i
        );
      } else {
        next = [
          ...state.items,
          {
            ...product,
            quantity: quantityToAdd,
            line_id: lineId,
            selected_size: selectedSize,
            selected_color: selectedColor,
          },
        ];
      }
      persist(next);

      // Mirror to server (fire-and-forget; optimistic UI already done above)
      if (isAuthenticated()) {
        const newQty = existing ? existing.quantity + quantityToAdd : quantityToAdd;
        apiFetch(`/cart/items/${product.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            product_id: product.id,
            quantity: newQty,
            selected_size: selectedSize,
            selected_color: selectedColor,
          }),
        }).catch(() => {/* swallow — local state is source of truth when offline */});
      }

      return { items: next };
    });
  },

  removeItem: (lineId) => {
    set((state) => {
      const target = state.items.find((i) => i.line_id === lineId);
      const next = state.items.filter((i) => i.line_id !== lineId);
      persist(next);

      if (isAuthenticated() && target) {
        const params = new URLSearchParams({
          selected_size: normalizeVariant(target.selected_size),
          selected_color: normalizeVariant(target.selected_color),
        });
        apiFetch(`/cart/items/${target.id}?${params.toString()}`, { method: "DELETE" }).catch(() => {});
      }

      return { items: next };
    });
  },

  updateQuantity: (lineId, quantity) => {
    set((state) => {
      const target = state.items.find((i) => i.line_id === lineId);
      if (!target) return { items: state.items };
      if (quantity <= 0) {
        const next = state.items.filter((i) => i.line_id !== lineId);
        persist(next);

        if (isAuthenticated()) {
          const params = new URLSearchParams({
            selected_size: normalizeVariant(target.selected_size),
            selected_color: normalizeVariant(target.selected_color),
          });
          apiFetch(`/cart/items/${target.id}?${params.toString()}`, { method: "DELETE" }).catch(() => {});
        }

        return { items: next };
      }
      const next = state.items.map((i) =>
        i.line_id === lineId ? { ...i, quantity } : i
      );
      persist(next);

      if (isAuthenticated()) {
        apiFetch(`/cart/items/${target.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            product_id: target.id,
            quantity,
            selected_size: normalizeVariant(target.selected_size),
            selected_color: normalizeVariant(target.selected_color),
          }),
        }).catch(() => {});
      }

      return { items: next };
    });
  },

  clearCart: () => {
    persist([]);

    if (isAuthenticated()) {
      apiFetch("/cart", { method: "DELETE" }).catch(() => {});
    }

    set({ items: [] });
  },

  getTotal: () =>
    get().items.reduce((sum, i) => sum + Number(i.price ?? 0) * i.quantity, 0),

  getItemCount: () =>
    get().items.reduce((sum, i) => sum + i.quantity, 0),

  initialize: () => {
    set({ items: hydrate() });
  },

  syncOnLogin: async () => {
    const local = get().items;

    try {
      if (local.length === 0) {
        const res = await apiFetch("/cart");
        if (res.ok) {
          const serverItems = extractServerCartItems(await res.json());
          const merged = serverItems.map(serverRowToItem);
          persist(merged);
          set({ items: merged });
        }
        return;
      }

      const res = await apiFetch("/cart/sync", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: local.map((i) => ({
            product_id: i.id,
            quantity: i.quantity,
            selected_size: normalizeVariant(i.selected_size),
            selected_color: normalizeVariant(i.selected_color),
          })),
        }),
      });

      if (res.ok) {
        const serverItems = extractServerCartItems(await res.json());
        const merged = serverItems.map(serverRowToItem);
        persist(merged);
        set({ items: merged });
      }
    } catch {
      // Network error — keep local cart unchanged
    }
  },

  detachFromServer: () => {
    // Keep the local cart — it remains a valid guest cart. Server mirroring is
    // already gated by isAuthenticated(), so once we are detached (logout or a
    // transient auth blip) mutations simply stop syncing to the server. Wiping
    // the local cart here would discard a customer's items on an aborted silent
    // refresh or a spurious 401, which is never what we want.
    set({ items: get().items });
  },

  clearLocalCart: () => {
    // Explicit logout: discard the local cart so the previous user's items do
    // not leak into a subsequent guest or different-user session on this device.
    // We do NOT call the server here — logout already tears down the session.
    if (typeof window !== "undefined") {
      localStorage.removeItem(STORAGE_KEY);
    }
    set({ items: [] });
  },
}));
