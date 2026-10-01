"use client";

import { useState, useEffect, useCallback } from "react";

// ─── Types ────────────────────────────────────────────────────────────────

export type PanelState = "expanded" | "collapsed";

export interface PanelLayoutState {
  /** Map of panel keys to their collapsed/expanded state */
  panels: Record<string, PanelState>;
  /** Active density mode for this page */
  density?: "compact" | "normal" | "expanded";
  /** Whether the grid is in compact mode */
  compactGrid?: boolean;
}

// ─── Storage key utilities ────────────────────────────────────────────────

function storageKey(pageId: string): string {
  return `panel-layout-${pageId}`;
}

function loadState(pageId: string): PanelLayoutState {
  if (typeof window === "undefined") return { panels: {} };
  try {
    const raw = localStorage.getItem(storageKey(pageId));
    if (raw) return JSON.parse(raw) as PanelLayoutState;
  } catch {}
  return { panels: {} };
}

function saveState(pageId: string, state: PanelLayoutState) {
  try {
    localStorage.setItem(storageKey(pageId), JSON.stringify(state));
  } catch {}
}

// ─── Hook ─────────────────────────────────────────────────────────────────

export function usePanelLayout(pageId: string, defaultDensity?: "compact" | "normal" | "expanded") {
  const [layout, setLayout] = useState<PanelLayoutState>(() => loadState(pageId));

  // Sync to localStorage on change
  useEffect(() => {
    saveState(pageId, layout);
  }, [pageId, layout]);

  // Toggle a single panel's collapsed state
  const togglePanel = useCallback((key: string) => {
    setLayout((prev) => ({
      ...prev,
      panels: {
        ...prev.panels,
        [key]: prev.panels[key] === "collapsed" ? "expanded" : "collapsed",
      },
    }));
  }, []);

  // Set a specific panel state
  const setPanelState = useCallback((key: string, state: PanelState) => {
    setLayout((prev) => ({
      ...prev,
      panels: {
        ...prev.panels,
        [key]: state,
      },
    }));
  }, []);

  // Expand all panels
  const expandAll = useCallback(() => {
    setLayout((prev) => {
      const allExpanded: Record<string, PanelState> = {};
      Object.keys(prev.panels).forEach((k) => { allExpanded[k] = "expanded"; });
      return { ...prev, panels: allExpanded };
    });
  }, []);

  // Collapse all panels
  const collapseAll = useCallback(() => {
    setLayout((prev) => {
      const allCollapsed: Record<string, PanelState> = {};
      Object.keys(prev.panels).forEach((k) => { allCollapsed[k] = "collapsed"; });
      return { ...prev, panels: allCollapsed };
    });
  }, []);

  // Check if a specific panel is expanded
  const isExpanded = useCallback((key: string): boolean => {
    return layout.panels[key] !== "collapsed";
  }, [layout.panels]);

  // Set density mode
  const setDensity = useCallback((d: "compact" | "normal" | "expanded") => {
    setLayout((prev) => ({ ...prev, density: d }));
  }, []);

  // Set compact grid
  const setCompactGrid = useCallback((v: boolean) => {
    setLayout((prev) => ({ ...prev, compactGrid: v }));
  }, []);

  // Reset layout for this page
  const resetLayout = useCallback(() => {
    const fresh = { panels: {}, density: defaultDensity };
    setLayout(fresh);
    saveState(pageId, fresh);
  }, [pageId, defaultDensity]);

  return {
    panels: layout.panels,
    density: layout.density ?? defaultDensity,
    compactGrid: layout.compactGrid ?? false,
    togglePanel,
    setPanelState,
    expandAll,
    collapseAll,
    isExpanded,
    setDensity,
    setCompactGrid,
    resetLayout,
  };
}
