import { create } from "zustand";

const MAX_HISTORY = 15;

interface SearchHistoryState {
  history: string[];
  add: (term: string) => void;
  remove: (term: string) => void;
  clear: () => void;
}

export const useSearchHistoryStore = create<SearchHistoryState>((set) => ({
  history: [],

  add: (term) =>
    set((state) => {
      const trimmed = term.trim();
      if (!trimmed) return state;
      const deduped = state.history.filter((h) => h.toLowerCase() !== trimmed.toLowerCase());
      return { history: [trimmed, ...deduped].slice(0, MAX_HISTORY) };
    }),

  remove: (term) =>
    set((state) => ({
      history: state.history.filter((h) => h !== term),
    })),

  clear: () => set({ history: [] }),
}));
