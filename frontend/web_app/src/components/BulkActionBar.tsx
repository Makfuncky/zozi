"use client";

import React from "react";
import { X } from "lucide-react";

export interface BulkAction {
  label: string;
  onClick: () => void;
  loading?: boolean;
  variant?: "primary" | "danger" | "warning" | "success";
  disabled?: boolean;
}

interface Props {
  selectedCount: number;
  onClearSelection: () => void;
  actions: BulkAction[];
  children?: React.ReactNode;
}

const VARIANT_CLASSES: Record<NonNullable<BulkAction["variant"]>, string> = {
  primary: "theme-btn-primary",
  danger: "bg-danger text-white hover:bg-danger/80",
  warning: "bg-warning text-black hover:bg-warning/80",
  success: "bg-success text-white hover:bg-success/80",
};

export default function BulkActionBar({ selectedCount, onClearSelection, actions, children }: Props) {
  if (selectedCount === 0) return null;

  return (
    <div
      data-testid="bulk-action-bar"
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 rounded-2xl border border-border bg-surface-1 px-4 py-3 shadow-2xl"
    >
      <span className="text-sm font-semibold text-text whitespace-nowrap">
        {selectedCount} selected
      </span>
      <div className="w-px h-5 bg-border" />
      {children && (
        <>
          {children}
          <div className="w-px h-5 bg-border" />
        </>
      )}
      <div className="flex items-center gap-2 flex-wrap">
        {actions.map((action) => (
          <button
            key={action.label}
            onClick={action.onClick}
            disabled={action.disabled || action.loading}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors disabled:opacity-50 ${
              VARIANT_CLASSES[action.variant ?? "primary"]
            }`}
          >
            {action.loading ? "Working…" : action.label}
          </button>
        ))}
      </div>
      <div className="w-px h-5 bg-border" />
      <button
        onClick={onClearSelection}
        aria-label="Clear selection"
        className="p-1 rounded-lg text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}


