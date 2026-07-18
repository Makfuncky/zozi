import { create } from "zustand";

/**
 * Mobile effect store — mirrors web's effectStore.
 * The active banner sets this; MobileBackgroundEffect reads and renders it.
 */
interface EffectStore {
  effect: string;
  setEffect: (effect: string) => void;
}

export const useEffectStore = create<EffectStore>((set) => ({
  effect: "",
  setEffect: (effect) => set({ effect }),
}));
