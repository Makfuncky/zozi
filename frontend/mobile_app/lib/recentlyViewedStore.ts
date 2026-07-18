import { create } from "zustand";

export interface ViewedProduct {
  id: number;
  name: string;
  price: number;
  image_url?: string;
  category?: string;
  rating?: number;
  viewedAt: number;
}

interface RecentlyViewedState {
  products: ViewedProduct[];
  track: (product: Omit<ViewedProduct, "viewedAt" | "price"> & { price: number | string }) => void;
  clear: () => void;
}

const MAX_ITEMS = 16;

export const useRecentlyViewedStore = create<RecentlyViewedState>((set, get) => ({
  products: [],

  track(product) {
    const entry: ViewedProduct = {
      ...product,
      price: Number(product.price ?? 0),
      viewedAt: Date.now(),
    };
    const updated = [entry, ...get().products.filter((item) => item.id !== product.id)].slice(0, MAX_ITEMS);
    set({ products: updated });
  },

  clear() {
    set({ products: [] });
  },
}));