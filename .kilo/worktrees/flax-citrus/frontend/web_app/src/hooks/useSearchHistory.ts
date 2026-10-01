"use client";

import { useState, useCallback, useEffect } from "react";

const STORAGE_KEY = "zozi_search_history";
const MAX_ITEMS = 20;

function loadHistory(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.slice(0, MAX_ITEMS).filter((s): s is string => typeof s === "string") : [];
  } catch {
    return [];
  }
}

function saveHistory(items: string[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX_ITEMS)));
  } catch {
    // localStorage might be full or unavailable — silently ignore
  }
}

export interface SearchHistory {
  /** The list of recent searches, most recent first */
  items: string[];
  /** Add a query to history (dedupes, moves to front) */
  addToHistory: (query: string) => void;
  /** Remove a single query from history */
  removeFromHistory: (query: string) => void;
  /** Clear all search history */
  clearHistory: () => void;
}

export function useSearchHistory(): SearchHistory {
  const [items, setItems] = useState<string[]>(loadHistory);

  // Sync to localStorage whenever items change
  useEffect(() => {
    saveHistory(items);
  }, [items]);

  const addToHistory = useCallback((query: string) => {
    const trimmed = query.trim();
    if (!trimmed) return;
    setItems((prev) => {
      // Remove duplicate if exists, then add to front
      const filtered = prev.filter((s) => s.toLowerCase() !== trimmed.toLowerCase());
      return [trimmed, ...filtered].slice(0, MAX_ITEMS);
    });
  }, []);

  const removeFromHistory = useCallback((query: string) => {
    setItems((prev) => prev.filter((s) => s.toLowerCase() !== query.toLowerCase()));
  }, []);

  const clearHistory = useCallback(() => {
    setItems([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  return { items, addToHistory, removeFromHistory, clearHistory };
}
