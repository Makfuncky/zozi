import { create } from "zustand";

interface EffectStore {
  effect: string;
  setEffect: (effect: string) => void;
}

export const useEffectStore = create<EffectStore>((set) => ({
  effect: "none",
  setEffect: (effect) => set({ effect }),
}));
